"""Một lượt trò chuyện Friendly (NV2).

Hai chế độ trả lời:
  - fast  (mặc định): ép đầu ra JSON {plan, answer, ask_back, choices} -> model không suy nghĩ, ~1-3 giây.
                       Chữ trong "answer" được tách dần và hiện ngay khi model đang viết.
  - think (Suy nghĩ kỹ): model suy nghĩ (ẩn) rồi trả lời, ~30 giây. Người dùng bấm "Trả lời nhanh" -> dừng suy nghĩ,
                       trả lời ngay bằng chế độ fast trong cùng lượt.
Thứ tự trong một lượt:
  1. guardrail "block"  -> trả lời cố định, không gọi AI
  2. ngôn ngữ (code)    -> không phải tiếng Việt: hiện câu xin lỗi trước, AI trả lời tiếng Việt
  3. lời dặn hệ thống   -> vai trò + bộ nhớ + tóm tắt + guardrail "instruct" + cảm xúc + giới hạn hỏi lại
  4. AI sinh chữ        -> lọc chữ ngoài Latin/emoji; guardrail "replace"; lọt nhiều chữ lạ -> viết lại 1 lần
  5. lưu câu trả lời    -> nút lựa chọn khi AI hỏi lại
  6. việc nền           -> bộ nhớ (chỉ khi tin nhắn đáng nhớ), tóm tắt hội thoại dài
Sự kiện SSE: meta, queue, start, thinking, switch, delta, restart, replace, done | error, memory.
"""
from __future__ import annotations
import asyncio
import json
import re
import time
import uuid

from . import context, db, guard, lang, llm, memory, persona, search, settings

_background: set = set()   # giữ tham chiếu tới việc nền để không bị dọn mất giữa chừng
_turns: dict[str, dict] = {}   # lượt đang chạy: turn_id -> {"user": id, "fast": cờ "Trả lời nhanh"}


def sse(obj: dict) -> str:
    return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"


def interrupt(turn_id: str, user_id: int) -> bool:
    """Nút "Trả lời nhanh": bật cờ cho lượt đang suy nghĩ. Trả False nếu lượt không tồn tại / không phải của người này."""
    t = _turns.get(turn_id)
    if not t or t["user"] != user_id:
        return False
    t["fast"] = True
    return True


class AnswerStream:
    """Tách dần giá trị chuỗi "answer" trong JSON đang được sinh ({"plan": "...", "answer": "...", ...}),
    giải mã các ký tự thoát (\\n, \\", \\uXXXX) để hiện chữ ngay mà không chờ JSON xong."""

    _KEY = re.compile(r'"answer"\s*:\s*"')
    _ESC = {"n": "\n", "t": "\t", "r": "", "b": "", "f": "", '"': '"', "\\": "\\", "/": "/"}

    def __init__(self):
        self.raw, self.pos, self.done = "", None, False

    def feed(self, chunk: str) -> str:
        self.raw += chunk
        if self.done:
            return ""
        if self.pos is None:
            m = self._KEY.search(self.raw)
            if not m:
                return ""
            self.pos = m.end()
        raw, i, out = self.raw, self.pos, []
        while i < len(raw):
            ch = raw[i]
            if ch == "\\":
                if i + 1 >= len(raw):
                    break   # chờ mẩu sau
                nx = raw[i + 1]
                if nx != "u":
                    out.append(self._ESC.get(nx, nx)); i += 2
                    continue
                if i + 6 > len(raw):
                    break
                try:
                    code = int(raw[i + 2:i + 6], 16)
                except ValueError:
                    code = 0xFFFD
                if 0xD800 <= code <= 0xDBFF:   # cặp surrogate (emoji…): cần đủ 12 ký tự
                    if i + 12 > len(raw):
                        break
                    try:
                        lo = int(raw[i + 8:i + 12], 16)
                        out.append(chr(0x10000 + ((code - 0xD800) << 10) + (lo - 0xDC00))); i += 12
                        continue
                    except ValueError:
                        code = 0xFFFD
                out.append(chr(code)); i += 6
                continue
            if ch == '"':
                self.done = True; i += 1
                break
            out.append(ch); i += 1
        self.pos = i
        return "".join(out)

    def final(self) -> dict:
        try:
            v = json.loads(self.raw)
            return v if isinstance(v, dict) else {}
        except ValueError:
            return {}


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


def search_query(text: str, history_path: list[dict]) -> str:
    """Câu để tìm dữ liệu: câu ngắn kiểu "còn phí thì sao?" ghép thêm câu hỏi trước của người dùng để đủ ngữ cảnh."""
    if len(text.split()) >= 6:
        return text
    prev = next((m["content"] for m in reversed(history_path) if m["role"] == "user"), "")
    return f"{prev} {text}".strip()


def build_messages(user_id: int, cid: str, history_path: list[dict], text: str, *, fast: bool,
                   leak_retry: bool = False, evidence: list[dict] | None = None) -> tuple[list[dict], dict]:
    """Lời dặn hệ thống + lịch sử + tin mới. Trả (messages, thông tin để quyết định / lưu meta)."""
    block, instructions = guard.check_input(text)
    foreign = not lang.is_vietnamese(text)
    streak = clarify_streak(history_path)
    limit = settings.get("CLARIFY_MAX")
    exhausted = streak if streak >= limit and limit > 0 else (max(streak, 1) if limit == 0 else 0)
    if leak_retry:
        instructions = instructions + ["Lần trước bạn đã dùng chữ không phải tiếng Việt. Lần này CHỈ viết tiếng Việt bằng chữ cái Latin."]
    mems = [m["text"] for m in db.list_memories(user_id)]
    kw = dict(clarify_exhausted=exhausted, upset=persona.negative(text), foreign=foreign, fast=fast, evidence=evidence)
    draft = persona.build(mems, "", instructions, **kw)
    summary, hist = context.history(cid, history_path, len(draft))
    system = persona.build(mems, summary, instructions, **kw) if summary else draft
    msgs = [{"role": "system", "content": system}] + hist + [{"role": "user", "content": text}]
    return msgs, {"block": block, "foreign": foreign, "exhausted": bool(exhausted)}


_REFUSAL = ("khong co thong tin", "khong tim thay", "khong co trong du lieu", "chua co thong tin", "khong de cap", "khong chua",
            "khong co du lieu", "khong thay thong tin", "khong the tra loi")


def kb_violation(content: str) -> bool:
    """Chuyên gia, tìm không thấy gì: AI vẫn viết một câu trả lời có nội dung mà không nói "không có trong dữ liệu"."""
    n = lang.normalize(content)
    return len(n) > 60 and not any(p in n for p in _REFUSAL)   # câu xã giao ngắn ("dạ, không có gì ạ") không tính


def _check(body: list[str], clean: str, state: dict):
    """Thêm chữ đã lọc; trả sự kiện replace nếu guardrail "replace" khớp."""
    body.append(clean)
    hit = guard.check_output("".join(body))
    if hit:
        state["replaced"] = hit
        return sse({"type": "replace", "text": hit["message"]})
    return None


async def _think(msgs: list[dict], prefix: str, state: dict, flag: dict):
    """Chế độ Suy nghĩ kỹ. Cờ "Trả lời nhanh" bật -> dừng ngay (state["interrupted"])."""
    filt, body = lang.LatinFilter(), []
    state.update(parts=body, filter=filt, replaced=None, mode="think", choices=None)
    if prefix:
        yield sse({"type": "delta", "text": prefix + "\n\n"})
    told = False
    async for t in llm.stream_chat(msgs):
        if flag["fast"] and not body:   # chỉ ngắt khi chưa có chữ trả lời (đang suy nghĩ)
            state["interrupted"] = True
            return   # thoát -> stream dừng gọi model
        if t is llm.THINKING:
            if not told:
                told = True
                yield sse({"type": "thinking"})
            continue
        clean = filt.feed(t)
        if not clean:
            continue
        rep = _check(body, clean, state)
        if rep:
            yield rep
            return
        yield sse({"type": "delta", "text": clean})


async def _fast(msgs: list[dict], prefix: str, state: dict):
    """Chế độ Nhanh: JSON có cấu trúc, hiện dần phần "answer"."""
    filt, body, ans = lang.LatinFilter(), [], AnswerStream()
    state.update(parts=body, filter=filt, replaced=None, mode="fast", choices=None, sources=[])
    if prefix:
        yield sse({"type": "delta", "text": prefix + "\n\n"})
    async for t in llm.stream_json(msgs, persona.FAST_SCHEMA_KB if state.get("kb") else persona.FAST_SCHEMA):
        if t is llm.THINKING:
            continue
        clean = filt.feed(ans.feed(t))
        if not clean:
            continue
        rep = _check(body, clean, state)
        if rep:
            yield rep
            return
        yield sse({"type": "delta", "text": clean})
    d = ans.final()
    if not body and isinstance(d.get("answer"), str):   # phòng khi tách dần trượt: lấy từ JSON hoàn chỉnh
        body.append(filt.feed(d["answer"]))
    state["sources"] = [x for x in d.get("sources") or [] if isinstance(x, int)]
    if d.get("ask_back"):
        cf = lang.LatinFilter()
        state["choices"] = [x for x in (cf.feed(str(c)).strip() for c in d.get("choices") or []) if x][:4]


async def _after_turn(user_id: int, cid: str, text: str) -> dict:
    """Việc nền sau câu trả lời: bộ nhớ (chỉ khi đáng) + tóm tắt. Chờ GPU như mọi lượt khác."""
    try:
        async with llm.Turn():
            mem = await asyncio.to_thread(memory.update, user_id, text)
            await asyncio.to_thread(context.maybe_summarize, cid)
        return mem
    except Exception:   # việc phụ: lỗi thì bỏ qua, không ảnh hưởng câu trả lời
        return {"added": [], "removed": []}


async def run(user: dict, cid: str, user_mid: int, text: str, history_path: list[dict], mode: str = "fast"):
    """Async generator SSE cho một lượt. user_mid = tin người dùng mà câu trả lời nối vào."""
    mode = "think" if mode == "think" else "fast"
    turn_id = uuid.uuid4().hex
    flag = _turns[turn_id] = {"user": user["id"], "fast": False}
    try:
        evidence, sinfo, t0 = None, None, time.perf_counter()
        if db.active_datasets(user["id"]):   # có bộ dữ liệu đang bật -> Chuyên gia: tìm trước khi hỏi AI
            evidence, sinfo = await asyncio.to_thread(search.search, user["id"], search_query(text, history_path))
            sinfo["search_ms"] = int((time.perf_counter() - t0) * 1000)
        bm = lambda **k: build_messages(user["id"], cid, history_path, text, evidence=evidence, **k)
        msgs, info = bm(fast=mode == "fast")
        yield sse({"type": "meta", "conversation_id": cid, "user_message_id": user_mid, "turn_id": turn_id, "mode": mode,
                   "specialist": evidence is not None})
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
        state, meta, status, err = {"kb": evidence is not None}, {}, "done", None
        try:
            async with llm.Turn():
                t_llm = time.perf_counter()
                yield sse({"type": "start"})
                if mode == "think" and not flag["fast"]:
                    async for ev in _think(msgs, prefix, state, flag):
                        yield ev
                interrupted = state.get("interrupted") or (mode == "think" and flag["fast"] and not state.get("parts"))
                if mode == "fast" or interrupted:
                    if mode == "think":
                        meta["interrupted"] = True
                        yield sse({"type": "switch", "mode": "fast"})
                        msgs, _ = bm(fast=True)
                    async for ev in _fast(msgs, prefix, state):
                        yield ev
                if evidence == [] and not state.get("replaced") and kb_violation("".join(state.get("parts") or [])):
                    # yêu cầu .docx: không dùng kiến thức chung. Tìm không thấy mà AI vẫn tự trả lời -> thay bằng câu cố định
                    state["replaced"] = {"name": "Chỉ trả lời từ dữ liệu", "message": settings.get("KB_NOT_FOUND_MESSAGE")}
                    yield sse({"type": "replace", "text": state["replaced"]["message"]})
                if not state.get("replaced") and state["filter"].heavy_leak():   # lọt nhiều chữ lạ: viết lại một lần
                    meta["leak_retry"] = True
                    yield sse({"type": "restart"})
                    fast = state["mode"] == "fast"
                    msgs, _ = bm(fast=fast, leak_retry=True)
                    async for ev in (_fast(msgs, prefix, state) if fast else _think(msgs, prefix, state, flag)):
                        yield ev
        except (llm.QueueFull, llm.LLMError) as e:
            status, err = "error", str(e)
        except (asyncio.CancelledError, GeneratorExit):
            status = "stopped"   # người dùng bấm Dừng / rời trang: giữ phần đã sinh
            raise
        finally:
            meta["mode"] = state.get("mode", mode)
            if "t_llm" in locals():
                meta["timing"] = {"llm_ms": int((time.perf_counter() - t_llm) * 1000), "total_ms": int((time.perf_counter() - t0) * 1000)}
            f = state.get("filter")
            if f and (f.removed_letters or f.removed_other):
                meta["filtered"] = {"letters": f.removed_letters, "other": f.removed_other}
            if state.get("replaced"):
                meta["guard"] = state["replaced"]["name"]
                content, choices = state["replaced"]["message"], []
            elif state.get("mode") == "fast":
                content, choices = "".join(state.get("parts") or []).strip(), state.get("choices") or []
            else:
                content, choices = persona.split_choices("".join(state.get("parts") or []))
            if prefix and not state.get("replaced") and (content or status != "error"):
                content = f"{prefix}\n\n{content}".strip()
            if evidence is not None:   # Chuyên gia: nguồn = các đoạn AI ghi [n] (hoặc liệt kê trong "sources")
                cited = sorted({int(n) for n in re.findall(r"\[(\d{1,2})\]", content)} | set(state.get("sources") or []))
                meta["specialist"] = True
                meta["sources"] = [{"n": n, "record_id": evidence[n - 1]["id"], "title": evidence[n - 1]["title"],
                                    "dataset": evidence[n - 1]["dataset"]} for n in cited if 1 <= n <= len(evidence)]
                if not meta["sources"]:
                    meta["consulted"] = [{"record_id": e["id"], "title": e["title"], "dataset": e["dataset"]} for e in evidence[:3]]
                meta["retrieval"] = sinfo
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
    finally:
        _turns.pop(turn_id, None)
    task = asyncio.create_task(_after_turn(user["id"], cid, text))
    _background.add(task)
    task.add_done_callback(_background.discard)
    try:
        mem = await asyncio.wait_for(asyncio.shield(task), timeout=90)
        if mem["added"] or mem["removed"]:
            yield sse({"type": "memory", **mem})
    except asyncio.TimeoutError:
        pass
