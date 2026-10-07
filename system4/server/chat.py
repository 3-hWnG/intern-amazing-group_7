"""Một lượt trò chuyện Friendly (NV2).

Thứ tự trong một lượt:
  1. guardrail "block"  -> trả lời cố định, không gọi AI
  2. ngôn ngữ (code)    -> không phải tiếng Việt: hiện câu xin lỗi trước, AI trả lời tiếng Việt
  3. lời dặn hệ thống   -> vai trò + bộ nhớ + tóm tắt + guardrail "instruct" + cảm xúc + giới hạn hỏi lại
  4. AI sinh chữ        -> lọc chữ ngoài Latin/emoji; guardrail "replace"; lọt nhiều chữ lạ -> viết lại 1 lần
  5. lưu câu trả lời    -> tách [[CHOICES]] thành nút lựa chọn
  6. việc nền           -> cập nhật bộ nhớ, tóm tắt hội thoại dài (giữ chỗ trên GPU như một lượt)
Sự kiện SSE: meta, queue, start, thinking, delta, restart, replace, done | error, memory.
"""
from __future__ import annotations
import asyncio
import json

from . import context, db, guard, lang, llm, memory, persona, settings

_background: set = set()   # giữ tham chiếu tới việc nền để không bị dọn mất giữa chừng


def sse(obj: dict) -> str:
    return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"


def clarify_streak(path: list[dict]) -> int:
    """Số lần trợ lý hỏi lại liên tiếp ngay trước tin mới (đếm ngược trên nhánh, bỏ qua tin người dùng)."""
    n = 0
    for m in reversed(path):
        if m["role"] != "assistant":
            continue
        if m["meta"].get("choices"):
            n += 1
        else:
            break
    return n


def build_messages(user_id: int, cid: str, history_path: list[dict], text: str, *, leak_retry: bool = False) -> tuple[list[dict], dict]:
    """Lời dặn hệ thống + lịch sử + tin mới. Trả (messages, thông tin để lưu vào meta)."""
    block, instructions = guard.check_input(text)
    foreign = not lang.is_vietnamese(text)
    streak = clarify_streak(history_path)
    limit = settings.get("CLARIFY_MAX")
    exhausted = streak if streak >= limit and limit > 0 else (max(streak, 1) if limit == 0 else 0)
    if leak_retry:
        instructions = instructions + ["Lần trước bạn đã dùng chữ không phải tiếng Việt. Lần này CHỈ viết tiếng Việt bằng chữ cái Latin."]
    mems = [m["text"] for m in db.list_memories(user_id)]
    draft = persona.build(mems, "", instructions, clarify_exhausted=exhausted, upset=persona.negative(text), foreign=foreign)
    summary, hist = context.history(cid, history_path, len(draft))
    system = persona.build(mems, summary, instructions, clarify_exhausted=exhausted,
                           upset=persona.negative(text), foreign=foreign) if summary else draft
    msgs = [{"role": "system", "content": system}] + hist + [{"role": "user", "content": text}]
    return msgs, {"block": block, "foreign": foreign, "exhausted": bool(exhausted)}


async def _generate(msgs: list[dict], prefix: str, state: dict):
    """Sinh một câu trả lời đã lọc; yield sự kiện SSE. Kết quả để trong state (parts, filter, replaced);
    parts được ghi dần nên bấm Dừng giữa chừng vẫn giữ được phần đã sinh."""
    filt = lang.LatinFilter()
    body: list[str] = []
    state.update(parts=body, filter=filt, replaced=None)
    if prefix:
        yield sse({"type": "delta", "text": prefix + "\n\n"})
    async for t in llm.stream_chat(msgs):
        if t is llm.THINKING:
            yield sse({"type": "thinking"})
            continue
        clean = filt.feed(t)
        if not clean:
            continue
        body.append(clean)
        hit = guard.check_output("".join(body))
        if hit:
            state["replaced"] = hit
            yield sse({"type": "replace", "text": hit["message"]})
            return   # thoát vòng lặp -> stream_chat dừng gọi model
        yield sse({"type": "delta", "text": clean})


async def _after_turn(user_id: int, cid: str, text: str) -> dict:
    """Việc nền sau câu trả lời: bộ nhớ + tóm tắt. Chờ GPU như mọi lượt khác."""
    try:
        async with llm.Turn():
            mem = await asyncio.to_thread(memory.update, user_id, text)
            await asyncio.to_thread(context.maybe_summarize, cid)
        return mem
    except Exception:   # việc phụ: lỗi thì bỏ qua, không ảnh hưởng câu trả lời
        return {"added": [], "removed": []}


async def run(user: dict, cid: str, user_mid: int, text: str, history_path: list[dict]):
    """Async generator SSE cho một lượt. user_mid = tin người dùng mà câu trả lời nối vào."""
    msgs, info = build_messages(user["id"], cid, history_path, text)
    yield sse({"type": "meta", "conversation_id": cid, "user_message_id": user_mid})
    if info["block"]:   # guardrail chặn: không gọi AI, không ghi nhớ
        b = info["block"]
        db.add_message(cid, "assistant", b["message"], "done", user_mid, {"guard": b["name"]})
        yield sse({"type": "delta", "text": b["message"]})
        yield sse({"type": "done"})
        return
    pos = llm.queue_position()
    if pos:
        yield sse({"type": "queue", "position": pos})
    prefix = settings.get("LANG_FALLBACK_APOLOGY") if info["foreign"] else ""
    state, meta, status, err = {}, {}, "done", None
    try:
        async with llm.Turn():
            yield sse({"type": "start"})
            async for ev in _generate(msgs, prefix, state):
                yield ev
            if not state.get("replaced") and state["filter"].heavy_leak():   # lọt nhiều chữ lạ: viết lại một lần
                meta["leak_retry"] = True
                yield sse({"type": "restart"})
                msgs, _ = build_messages(user["id"], cid, history_path, text, leak_retry=True)
                async for ev in _generate(msgs, prefix, state):
                    yield ev
    except (llm.QueueFull, llm.LLMError) as e:
        status, err = "error", str(e)
    except (asyncio.CancelledError, GeneratorExit):
        status = "stopped"   # người dùng bấm Dừng / rời trang: giữ phần đã sinh
        raise
    finally:
        f = state.get("filter")
        if f and (f.removed_letters or f.removed_other):
            meta["filtered"] = {"letters": f.removed_letters, "other": f.removed_other}
        if state.get("replaced"):
            meta["guard"] = state["replaced"]["name"]
            content, choices = state["replaced"]["message"], []
        else:
            content, choices = persona.split_choices("".join(state.get("parts") or []))
            if prefix and (content or status != "error"):
                content = f"{prefix}\n\n{content}".strip()
        if choices and not info["exhausted"]:
            meta["choices"] = choices
        elif choices:   # đã hết lượt hỏi lại mà AI vẫn đưa lựa chọn: hiện như văn bản
            content += "\n\n" + "\n".join(f"- {c}" for c in choices)
        if err:
            db.add_message(cid, "assistant", err, "error", user_mid, meta)
        elif content:
            db.add_message(cid, "assistant", content, status, user_mid, meta)
    if err:
        yield sse({"type": "error", "message": err})
        return
    yield sse({"type": "done"})
    task = asyncio.create_task(_after_turn(user["id"], cid, text))
    _background.add(task)
    task.add_done_callback(_background.discard)
    try:
        mem = await asyncio.wait_for(asyncio.shield(task), timeout=90)
        if mem["added"] or mem["removed"]:
            yield sse({"type": "memory", **mem})
    except asyncio.TimeoutError:
        pass
