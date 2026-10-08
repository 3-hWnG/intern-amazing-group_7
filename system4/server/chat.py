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
NV5 (mỗi bước bật/tắt trong ⚙, mặc định tắt = như trước): câu chào khi bật dữ liệu (GREETING_MODE), công cụ bảng (TABLE_TOOL),
hỏi lại khi trùng tên (AMBIGUITY_CHECK, trả lời bằng code), kiểm chi tiết bịa rồi viết lại (GROUNDING_CHECK), thứ tự lời dặn
để Ollama dùng lại phần đã đọc (PROMPT_CACHE_ORDER), chế độ Nhanh dạng chữ (FAST_FORMAT=text).
Sự kiện SSE: meta, queue, start, thinking, switch, delta, restart, replace, done | error, memory.
"""
from __future__ import annotations
import asyncio
import json
import re
import time
import uuid

from . import ambig, context, db, greet, ground, guard, lang, llm, memory, persona, search, settings, tabletool

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


_FOLLOW = re.compile(r"^(còn|vậy|thế|rồi|thế còn|vậy còn|ok,? còn)\b|\b(đó|ấy|kia|thì sao|nữa|như trên|vừa rồi)\b", re.I)


def _followup(text: str) -> bool:
    """SEARCH_FOLLOWUP: câu hỏi tiếp kiểu "Còn số điện thoại thì sao?", "Bạn ấy sinh ngày nào?" (<= 10 chữ) cũng ghép câu trước."""
    return len(text.split()) <= 10 and bool(_FOLLOW.search(text.lower()))


def search_query(text: str, history_path: list[dict]) -> str:
    """Câu để tìm dữ liệu: câu ngắn kiểu "còn phí thì sao?" ghép thêm câu hỏi trước của người dùng để đủ ngữ cảnh."""
    if len(text.split()) >= 6 and not (settings.get("SEARCH_FOLLOWUP") and _followup(text)):
        return text
    prev = next((m["content"] for m in reversed(history_path) if m["role"] == "user"), "")
    return f"{prev} {text}".strip()


def build_messages(user_id: int, cid: str, history_path: list[dict], text: str, *, fast: bool,
                   leak_retry: bool = False, evidence: list[dict] | None = None, extra: list[str] | None = None,
                   small_talk: bool = False) -> tuple[list[dict], dict]:
    """Lời dặn hệ thống + lịch sử + tin mới. Trả (messages, thông tin để quyết định / lưu meta).
    extra: lời dặn thêm cho riêng lần gửi này (câu xã giao, viết lại vì chi tiết bịa). small_talk: AI được đánh dấu câu xã giao."""
    block, instructions = guard.check_input(text)
    foreign = not lang.is_vietnamese(text)
    streak = clarify_streak(history_path)
    limit = settings.get("CLARIFY_MAX")
    exhausted = streak if streak >= limit and limit > 0 else (max(streak, 1) if limit == 0 else 0)
    if leak_retry:
        instructions = instructions + ["Lần trước bạn đã dùng chữ không phải tiếng Việt. Lần này CHỈ viết tiếng Việt bằng chữ cái Latin."]
    instructions = instructions + list(extra or [])
    mems = [m["text"] for m in db.list_memories(user_id)]
    cache = settings.get("PROMPT_CACHE_ORDER")
    kw = dict(clarify_exhausted=exhausted, upset=persona.negative(text), foreign=foreign, fast=fast, evidence=evidence,
              cache_order=cache, text_format=fast and settings.get("FAST_FORMAT") == "text", small_talk=small_talk)
    draft = persona.build(mems, "", instructions, **kw)
    size = len(draft) if isinstance(draft, str) else len(draft[0]) + len(draft[1])
    summary, hist = context.history(cid, history_path, size)
    system = persona.build(mems, summary, instructions, **kw) if summary else draft
    if cache:   # phần không đổi trong lời dặn hệ thống; dữ liệu + lời dặn riêng đi cùng tin nhắn mới (Ollama dùng lại phần đã đọc)
        system, tail = system
        last = text + (f"\n\n---\n(Thông tin cho trợ lý, người dùng không thấy)\n{tail}" if tail else "")
    else:
        last = text
    msgs = [{"role": "system", "content": system}] + hist + [{"role": "user", "content": last}]
    return msgs, {"block": block, "foreign": foreign, "exhausted": bool(exhausted), "streak": streak, "instructions": instructions,
                  "upset": kw["upset"], "memories": len(mems), "summary": bool(summary), "history": len(hist)}


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


def _stat(t, state: dict) -> bool:
    """Mẩu số đo Ollama (cuối luồng): lưu cho 🔍 / bộ đo."""
    if isinstance(t, llm.Stats):
        state.setdefault("llm_stats", []).append(dict(t))
        return True
    return False


async def _think(msgs: list[dict], prefix: str, state: dict, flag: dict):
    """Chế độ Suy nghĩ kỹ. Cờ "Trả lời nhanh" bật -> dừng ngay (state["interrupted"]).
    state["ask_small"]: AI có thể mở đầu bằng [XÃ GIAO] -> code bỏ dấu này đi trước khi hiện chữ."""
    filt, body = lang.LatinFilter(), []
    state.update(parts=body, filter=filt, replaced=None, mode="think", choices=None, small_talk=False)
    if prefix:
        yield sse({"type": "delta", "text": prefix + "\n\n"})
    told, head = False, "" if state.get("ask_small") else None
    mark = persona.SMALL_TALK_MARK
    async for t in llm.stream_chat(msgs):
        if _stat(t, state):
            continue
        if flag["fast"] and not body:   # chỉ ngắt khi chưa có chữ trả lời (đang suy nghĩ)
            state["interrupted"] = True
            return   # thoát -> stream dừng gọi model
        if isinstance(t, llm.Thought):
            state.setdefault("thinking", []).append(str(t))
            if not told:
                told = True
                yield sse({"type": "thinking"})
            continue
        if head is not None:   # giữ lại vài chữ đầu để xem có dấu [XÃ GIAO] không
            head += t
            if len(head.lstrip()) < len(mark) and mark.startswith(head.lstrip()):
                continue
            if head.lstrip().startswith(mark):
                state["small_talk"] = True
                t = head.lstrip()[len(mark):].lstrip()
            else:
                t = head
            head = None
            if not t:
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
    """Chế độ Nhanh. FAST_FORMAT=json: JSON có cấu trúc, hiện dần phần "answer". text: dòng kế hoạch ẩn rồi chữ tự do."""
    if settings.get("FAST_FORMAT") == "text":
        async for ev in _fast_text(msgs, prefix, state):
            yield ev
        return
    filt, body, ans = lang.LatinFilter(), [], AnswerStream()
    state.update(parts=body, filter=filt, replaced=None, mode="fast", fmt="json", choices=None, sources=[], ans=ans, small_talk=False)
    if prefix:
        yield sse({"type": "delta", "text": prefix + "\n\n"})
    async for t in llm.stream_json(msgs, persona.fast_schema(bool(state.get("kb")), bool(state.get("ask_small")))):
        if _stat(t, state) or isinstance(t, llm.Thought):
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
    state["small_talk"] = bool(d.get("small_talk"))
    if d.get("ask_back"):
        cf = lang.LatinFilter()
        state["choices"] = [x for x in (cf.feed(str(c)).strip() for c in d.get("choices") or []) if x][:4]


_SEP = re.compile(r"^[ \t]*" + re.escape(persona.TEXT_SEP) + r"[ \t]*\r?\n", re.M)


async def _fast_text(msgs: list[dict], prefix: str, state: dict):
    """FAST_FORMAT=text: model viết "KẾ HOẠCH: …" / "===" / câu trả lời. Phần trước "===" giữ lại (ẩn), phần sau hiện dần.
    Lựa chọn hỏi lại theo mẫu [[CHOICES]] như Suy nghĩ kỹ (tách khi lưu)."""
    filt, body, raw = lang.LatinFilter(), [], []
    state.update(parts=body, filter=filt, replaced=None, mode="fast", fmt="text", choices=None, sources=[], ans=None,
                 raw_text=raw, small_talk=False)
    if prefix:
        yield sse({"type": "delta", "text": prefix + "\n\n"})
    buf, started, limit = "", False, settings.get("PLAN_MAX_CHARS") + 200
    async for t in llm.stream_text(msgs):
        if _stat(t, state) or isinstance(t, llm.Thought):
            continue
        raw.append(t)
        if not started:
            buf += t
            m = _SEP.search(buf)
            lead = buf.lstrip()
            if m:
                started, t = True, buf[m.end():]
            elif len(lead) >= len(persona.PLAN_PREFIX) and not lead.startswith(persona.PLAN_PREFIX):
                started, t = True, buf   # model bỏ qua dòng kế hoạch: hiện luôn
            elif len(buf) > limit and "\n" in lead:
                started, t = True, lead.partition("\n")[2]   # có kế hoạch nhưng thiếu "===": bỏ dòng đầu
            else:
                continue
        if not t:
            continue
        clean = filt.feed(t)
        if not clean:
            continue
        rep = _check(body, clean, state)
        if rep:
            yield rep
            return
        yield sse({"type": "delta", "text": clean})
    plan, answer, small = persona.parse_text("".join(raw))
    state["plan"], state["small_talk"] = plan, small
    if not body and answer:   # kết thúc khi chưa qua "===" (câu trả lời ngắn)
        body.append(filt.feed(answer))
        yield sse({"type": "delta", "text": body[-1]})


async def _after_turn(user_id: int, cid: str, text: str, mid: int | None = None) -> dict:
    """Việc nền sau câu trả lời: bộ nhớ (chỉ khi đáng) + tóm tắt. Chờ GPU như mọi lượt khác."""
    try:
        async with llm.Turn():
            mem = await asyncio.to_thread(memory.update, user_id, text)
            summarized = await asyncio.to_thread(context.maybe_summarize, cid)
        if mid:
            db.patch_trace(mid, "after", {"memory": mem, "summarized": summarized})
        return mem
    except Exception:   # việc phụ: lỗi thì bỏ qua, không ảnh hưởng câu trả lời
        return {"added": [], "removed": []}


def _refusal(content: str) -> bool:
    n = lang.normalize(content)
    return any(p in n for p in _REFUSAL)


def _allowed_text(text: str, history_path: list[dict], evidence: list[dict] | None) -> str:
    """Chữ được phép dùng làm nguồn cho chi tiết trong câu trả lời (kiểm chi tiết bịa)."""
    parts = [text, settings.get("BUSINESS_NAME"), settings.get("BUSINESS_DESCRIPTION") or ""]
    parts += [m["content"] for m in history_path if m["role"] == "user"]
    for e in evidence or []:
        parts += [e["title"], e.get("dataset", ""), e["text"]]
    return "\n".join(parts)


def _answer_text(state: dict) -> str:
    raw = "".join(state.get("parts") or [])
    return raw if state.get("mode") == "fast" and state.get("fmt") == "json" else persona.split_choices(raw)[0]


async def run(user: dict, cid: str, user_mid: int, text: str, history_path: list[dict], mode: str = "fast"):
    """Async generator SSE cho một lượt. user_mid = tin người dùng mà câu trả lời nối vào."""
    mode = "think" if mode == "think" else "fast"
    turn_id = uuid.uuid4().hex
    flag = _turns[turn_id] = {"user": user["id"], "fast": False}
    try:
        evidence, sinfo, t0 = None, None, time.perf_counter()
        active = db.active_datasets(user["id"])
        gm = settings.get("GREETING_MODE") if active else "off"
        gate = gm in ("code_first", "ai_first") and greet.is_greeting(text, history_path)   # quy tắc code: ngắn + có từ chào
        small_by_code = gm == "code_first" and gate        # code nhận trước: không tra dữ liệu
        ask_small = gm != "off" and not small_by_code       # AI được đánh dấu câu xã giao
        amb, table = None, None
        squery = search_query(text, history_path)
        if active and not small_by_code:   # có bộ dữ liệu đang bật -> Chuyên gia: tìm trước khi hỏi AI
            evidence, sinfo = await asyncio.to_thread(search.search, user["id"], squery)
            sinfo["search_ms"] = int((time.perf_counter() - t0) * 1000)
            ids = [d["id"] for d in active]
            if settings.get("TABLE_TOOL") and tabletool.triggered(text):
                t1 = time.perf_counter()
                async with llm.Turn():
                    table = await asyncio.to_thread(tabletool.run, squery, ids)
                if table:
                    table["info"]["ms"] = int((time.perf_counter() - t1) * 1000)
                    sinfo["table_tool"] = table["info"]
                    if table["evidence"]:
                        evidence = [table["evidence"]] + evidence
            if settings.get("AMBIGUITY_CHECK") and not (table and table["evidence"]):
                amb = await asyncio.to_thread(ambig.check, squery, ids, {c["id"] for c in sinfo.get("candidates", [])})
                sinfo["ambiguity"] = amb
        extra0 = [greet.SMALL_TALK_INSTRUCTION] if small_by_code else []
        bm = lambda **k: build_messages(user["id"], cid, history_path, text, **{"evidence": evidence, "extra": extra0,
                                                                                "small_talk": ask_small and evidence is not None, **k})
        msgs, info = bm(fast=mode == "fast")
        prompts = [{"why": "lần gửi đầu", "messages": msgs}]
        yield sse({"type": "meta", "conversation_id": cid, "user_message_id": user_mid, "turn_id": turn_id, "mode": mode,
                   "specialist": evidence is not None})
        checks = {"foreign": info["foreign"], "upset": info["upset"], "streak": info["streak"], "greeting_gate": gate,
                  "greeting_mode": gm}
        if info["block"]:   # guardrail chặn: không gọi AI, không ghi nhớ
            b = info["block"]
            bmid = db.add_message(cid, "assistant", b["message"], "done", user_mid, {"guard": b["name"]})
            db.save_trace(bmid, cid, user["id"], {"mode": mode, "query": text, "blocked_by": b["name"], "checks": checks},
                          settings.get("TRACE_KEEP"))
            yield sse({"type": "delta", "text": b["message"]})
            yield sse({"type": "done"})
            return
        if amb and not info["exhausted"]:   # trùng tên: hỏi lại bằng code, không gọi AI
            q = ambig.question(amb)
            meta = {"specialist": True, "choices": amb["options"], "ambiguity": amb["phrase"], "mode": mode,
                    "retrieval": {k: sinfo.get(k) for k in ("datasets", "reranked", "candidates_n", "keyword", "vector", "search_ms")},
                    "timing": {"llm_ms": 0, "total_ms": int((time.perf_counter() - t0) * 1000)}}
            amid = db.add_message(cid, "assistant", q, "done", user_mid, meta)
            db.save_trace(amid, cid, user["id"], {"mode": mode, "specialist": True, "query": squery, "retrieval": sinfo,
                                                  "checks": {**checks, "ambiguity": amb}, "prompts": [],
                                                  "output": {"final_text": q}, "timing": meta["timing"]}, settings.get("TRACE_KEEP"))
            yield sse({"type": "delta", "text": q})
            yield sse({"type": "done"})
            return
        pos = llm.queue_position()
        if pos:
            yield sse({"type": "queue", "position": pos})
        prefix = settings.get("LANG_FALLBACK_APOLOGY") if info["foreign"] else ""
        state = {"kb": evidence is not None, "ask_small": ask_small and evidence is not None}
        meta, status, err, small = {}, "done", None, small_by_code

        async def gen(m):   # chạy lại đúng chế độ hiện tại (viết lại sau khi kiểm)
            g = _fast(m, prefix, state) if state["mode"] == "fast" else _think(m, prefix, state, flag)
            async for ev in g:
                yield ev
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
                        prompts.append({"why": "bấm Trả lời nhanh: gửi lại ở chế độ Nhanh", "messages": msgs})
                    async for ev in _fast(msgs, prefix, state):
                        yield ev
                # ---- câu xã giao (NV5): AI tự đánh dấu; ai_first: code kiểm lại
                ai_small = bool(state.get("small_talk")) and state["ask_small"]
                if ai_small:
                    small = True
                    if gm == "ai_first" and not gate and greet.looks_like_question(text):
                        small, meta["small_talk_override"] = False, "rejected"   # AI nói xã giao nhưng tin nhắn là câu hỏi
                elif gm == "ai_first" and gate and evidence is not None and not state.get("replaced") and _refusal(_answer_text(state)):
                    meta["small_talk_override"] = "forced"   # câu chào ngắn mà AI trả lời "không có trong dữ liệu": viết lại
                    small = True
                    yield sse({"type": "restart"})
                    msgs, _ = bm(fast=state["mode"] == "fast", evidence=None, small_talk=False, extra=[greet.SMALL_TALK_INSTRUCTION])
                    prompts.append({"why": "câu chào bị trả lời 'không có trong dữ liệu': viết lại kiểu xã giao", "messages": msgs})
                    state["kb"], state["ask_small"] = False, False
                    async for ev in gen(msgs):
                        yield ev
                if small:
                    meta["small_talk"] = "code" if small_by_code else meta.get("small_talk_override") or "ai"
                if evidence == [] and not small and not state.get("replaced") and kb_violation("".join(state.get("parts") or [])):
                    # yêu cầu .docx: không dùng kiến thức chung. Tìm không thấy mà AI vẫn tự trả lời -> thay bằng câu cố định
                    state["replaced"] = {"name": "Chỉ trả lời từ dữ liệu", "message": settings.get("KB_NOT_FOUND_MESSAGE")}
                    yield sse({"type": "replace", "text": state["replaced"]["message"]})
                # ---- kiểm chi tiết bịa (NV5, 2A): viết lại một lần
                if settings.get("GROUNDING_CHECK") == "rewrite" and not small and not state.get("replaced"):
                    kb = evidence is not None
                    allowed = _allowed_text(text, history_path, evidence)
                    items = ground.ungrounded(_answer_text(state), allowed, kb, settings.get("BUSINESS_NAME"))
                    if items:
                        meta["grounding"] = {"items": items}
                        yield sse({"type": "restart"})
                        msgs, _ = bm(fast=state["mode"] == "fast", extra=extra0 + [ground.rewrite_instruction(items, kb)])
                        prompts.append({"why": "chi tiết không có nguồn: viết lại", "messages": msgs})
                        async for ev in gen(msgs):
                            yield ev
                        if not state.get("replaced"):
                            meta["grounding"]["after"] = ground.ungrounded(_answer_text(state), allowed, kb, settings.get("BUSINESS_NAME"))
                if not state.get("replaced") and state["filter"].heavy_leak():   # lọt nhiều chữ lạ: viết lại một lần
                    meta["leak_retry"] = True
                    yield sse({"type": "restart"})
                    msgs, _ = bm(fast=state["mode"] == "fast", leak_retry=True)
                    prompts.append({"why": "lọt nhiều chữ lạ: viết lại", "messages": msgs})
                    async for ev in gen(msgs):
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
            elif state.get("mode") == "fast" and state.get("fmt") == "json":
                content, choices = "".join(state.get("parts") or []).strip(), state.get("choices") or []
            else:
                content, choices = persona.split_choices("".join(state.get("parts") or []))
            if prefix and not state.get("replaced") and (content or status != "error"):
                content = f"{prefix}\n\n{content}".strip()
            if evidence is not None:
                meta["specialist"] = True
                meta["retrieval"] = {k: sinfo.get(k) for k in ("datasets", "reranked", "candidates_n", "keyword", "vector", "search_ms")}
            if evidence is not None and not small:   # Chuyên gia: nguồn = các đoạn AI ghi [n] (hoặc liệt kê trong "sources")
                cited = sorted({int(n) for n in re.findall(r"\[(\d{1,2})\]", content)} | set(state.get("sources") or []))
                meta["sources"] = [{"n": n, "record_id": evidence[n - 1]["id"], "title": evidence[n - 1]["title"],
                                    "dataset": evidence[n - 1]["dataset"], "score": evidence[n - 1].get("score")}
                                   for n in cited if 1 <= n <= len(evidence)]
                if not meta["sources"]:
                    meta["consulted"] = [{"record_id": e["id"], "title": e["title"], "dataset": e["dataset"], "score": e.get("score")}
                                         for e in evidence[:3]]
            if choices and not info["exhausted"]:
                meta["choices"] = choices
            elif choices:   # đã hết lượt hỏi lại mà AI vẫn đưa lựa chọn: hiện như văn bản
                content += "\n\n" + "\n".join(f"- {c}" for c in choices)
            mid = None
            if err:
                mid = db.add_message(cid, "assistant", err, "error", user_mid, meta)
            elif content:
                mid = db.add_message(cid, "assistant", content, status, user_mid, meta)
            if mid:
                a = state.get("ans")
                db.save_trace(mid, cid, user["id"], {
                    "mode": mode, "final_mode": meta["mode"], "specialist": evidence is not None, "status": status, "error": err,
                    "query": squery if evidence is not None else text,
                    "retrieval": sinfo,
                    "checks": {**checks, "clarify_streak": info["streak"],
                               "clarify_exhausted": info["exhausted"], "instructions": info["instructions"],
                               "guard_replaced": meta.get("guard"), "kb_guard": meta.get("guard") == "Chỉ trả lời từ dữ liệu",
                               "filtered": meta.get("filtered"), "leak_retry": meta.get("leak_retry", False),
                               "interrupted": meta.get("interrupted", False), "memories_in_prompt": info["memories"],
                               "summary_in_prompt": info["summary"], "history_messages": info["history"],
                               "small_talk": meta.get("small_talk"), "small_talk_override": meta.get("small_talk_override"),
                               "grounding": meta.get("grounding")},
                    "prompts": prompts,
                    "output": {"raw_json": a.raw if a else None,
                               "raw_text": "".join(state.get("raw_text") or []) or None,
                               "plan": (a.final().get("plan") if a else state.get("plan")),
                               "thinking": "".join(state.get("thinking") or [])[:30000], "final_text": content},
                    "timing": {**meta.get("timing", {}), "search_ms": (sinfo or {}).get("search_ms"),
                               "search_parts": (sinfo or {}).get("timing"), "llm_stats": state.get("llm_stats"),
                               "table_ms": ((table or {}).get("info") or {}).get("ms")},
                }, settings.get("TRACE_KEEP"))
        if err:
            yield sse({"type": "error", "message": err})
            return
        yield sse({"type": "done"})
    finally:
        _turns.pop(turn_id, None)
    task = asyncio.create_task(_after_turn(user["id"], cid, text, locals().get("mid")))
    _background.add(task)
    task.add_done_callback(_background.discard)
    try:
        mem = await asyncio.wait_for(asyncio.shield(task), timeout=90)
        if mem["added"] or mem["removed"]:
            yield sse({"type": "memory", **mem})
    except asyncio.TimeoutError:
        pass
