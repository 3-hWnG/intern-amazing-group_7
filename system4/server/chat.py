"""Một lượt trò chuyện Friendly (NV2).

Một chế độ trả lời (D9, 18/10: bỏ hẳn chế độ suy nghĩ ~30 giây và nút ngắt của nó):
  - fast: ép đầu ra JSON {plan, answer, ask_back, choices} -> model không suy nghĩ, ~1-3 giây.
          Chữ trong "answer" được tách dần và hiện ngay khi model đang viết.
Thứ tự trong một lượt:
  1. guardrail "block"  -> trả lời cố định, không gọi AI
  2. ngôn ngữ (code)    -> không phải tiếng Việt: hiện câu xin lỗi trước, AI trả lời tiếng Việt
  3. lời dặn hệ thống   -> vai trò + bộ nhớ + tóm tắt + guardrail "instruct" + cảm xúc + giới hạn hỏi lại
  4. AI sinh chữ        -> lọc chữ ngoài Latin/emoji; guardrail "replace"; lọt nhiều chữ lạ -> viết lại 1 lần
     Chỉ lần viết đầu hiện dần. Bước kiểm cần viết lại (chi tiết bịa, thiếu [n], chữ lạ, câu chào bị từ chối): bản đã hiện được lưu
     thành một phiên bản và GIỮ trên màn hình; bản viết lại không hiện dần, lưu thành phiên bản mới (cùng tin người dùng) và thành
     nhánh đang xem khi xong — người dùng mở lại bản đầu bằng ‹ ›. Dừng / lỗi lúc viết lại: giữ bản đầu.
  5. lưu câu trả lời    -> nút lựa chọn khi AI hỏi lại
  6. việc nền           -> bộ nhớ (chỉ khi tin nhắn đáng nhớ), tóm tắt hội thoại dài
NV5 (mỗi bước bật/tắt trong ⚙, mặc định tắt = như trước): câu chào khi bật dữ liệu (GREETING_MODE), công cụ bảng (TABLE_TOOL),
hỏi lại khi trùng tên (AMBIGUITY_CHECK, trả lời bằng code), kiểm chi tiết bịa rồi viết lại (GROUNDING_CHECK), thứ tự lời dặn
để Ollama dùng lại phần đã đọc (PROMPT_CACHE_ORDER), chế độ Nhanh dạng chữ (FAST_FORMAT=text).
Sự kiện SSE: meta, queue, start, delta, checking (đang kiểm + viết lại, bản đầu giữ nguyên), replace, done | error, memory.
"""
from __future__ import annotations
import asyncio
import json
import re
import time
import uuid

from core import gpu, websearch as core_web
from . import ambig, answer_cache, context, db, fastpath, greet, profile, ground, guard, lang, llm, memory, persona, search, settings, tabletool, websearch
from ..abi import turn as abi_turn

RULES_ONLY_MESSAGE = ("Bạn đang ở chế độ **chỉ trả lời bằng luật** nên lĩnh vực này (cần AI viết câu trả lời) tạm không trả lời. "
                      "Lĩnh vực Thủ tục vẫn trả lời bằng dữ liệu. Tắt chế độ này trong ô Tài khoản nếu muốn dùng AI (máy không có card đồ hoạ "
                      "thì AI trả lời chậm, khoảng 7–40 giây).")
NO_DATA_MESSAGE = ("Lĩnh vực «{name}» chưa có bộ dữ liệu nào đang bật nên chưa trả lời được (lĩnh vực này chỉ trả lời từ dữ liệu). "
                   "Dev / cán bộ cần tải lên hoặc đồng bộ dữ liệu ở Quản lý lĩnh vực.")
_background: set = set()   # giữ tham chiếu tới việc nền để không bị dọn mất giữa chừng
_turns: dict[str, dict] = {}   # lượt đang chạy: turn_id -> {"user": id}


def sse(obj: dict) -> str:
    return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"


class AnswerStream:
    """Tách dần giá trị chuỗi "answer" trong JSON đang được sinh ({"plan": "...", "answer": "...", ...}),
    giải mã các ký tự thoát (\\n, \\", \\uXXXX) để hiện chữ ngay mà không chờ JSON xong."""

    _KEY = re.compile(r'"(?:c_)?answer"\s*:\s*"')
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
            return persona.plain_keys(v) if isinstance(v, dict) else {}
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
                   small_talk: bool = False, web: bool = False) -> tuple[list[dict], dict]:
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
              cache_order=cache, text_format=fast and settings.get("FAST_FORMAT") == "text", small_talk=small_talk, web=web)
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
    Lựa chọn hỏi lại theo mẫu [[CHOICES]] (tách khi lưu)."""
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
    """Việc nền sau câu trả lời: bộ nhớ (chỉ khi đáng) + tóm tắt. Chờ GPU ở mức ưu tiên thấp (P2): câu hỏi mới đi trước."""
    try:
        async with llm.Turn(gpu.P2):
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


def _cited(state: dict) -> bool:
    """Câu trả lời từ dữ liệu có ghi số đoạn [n] (trong chữ hoặc mục "sources" của JSON) không; câu "không có trong dữ liệu" coi như đạt."""
    txt = _answer_text(state)
    return bool(re.search(r"\[\d{1,2}\]", txt) or state.get("sources")) or _refusal(txt)


def _answer_text(state: dict) -> str:
    raw = "".join(state.get("parts") or [])
    return raw if state.get("mode") == "fast" and state.get("fmt") == "json" else persona.split_choices(raw)[0]


def _shown(state: dict) -> tuple[str, list[str]]:
    """Câu trả lời AI vừa viết, dạng lưu: (nội dung, lựa chọn hỏi lại)."""
    if state.get("mode") == "fast" and state.get("fmt") == "json":
        return "".join(state.get("parts") or []).strip(), state.get("choices") or []
    return persona.split_choices("".join(state.get("parts") or []))


def _sources_meta(content: str, state: dict, evidence: list[dict] | None, small: bool) -> dict:
    """Chuyên gia: nguồn = các đoạn AI ghi [n] (hoặc liệt kê trong "sources"); không ghi số nào thì 3 đoạn đã tra."""
    if evidence is None or small:
        return {}
    cited = sorted({int(n) for n in re.findall(r"\[(\d{1,2})\]", content)} | set(state.get("sources") or []))
    out = {"sources": [{"n": n, "record_id": evidence[n - 1]["id"], "url": evidence[n - 1].get("url"), "title": evidence[n - 1]["title"],
                        "dataset": evidence[n - 1]["dataset"], "score": evidence[n - 1].get("score")}
                       for n in cited if 1 <= n <= len(evidence)]}
    if not out["sources"]:
        out["consulted"] = [{"record_id": e["id"], "url": e.get("url"), "title": e["title"], "dataset": e["dataset"], "score": e.get("score")}
                            for e in evidence[:3]]
    return out


async def _answerable(choices: list[str], dataset_ids: list[int]) -> list[str]:
    """Giữ lựa chọn mà bộ dữ liệu đang bật có đoạn khớp. AI tự nghĩ ra lựa chọn nên có thể gợi ý điều dữ liệu không có;
    chọn vào đó chỉ nhận "không có trong dữ liệu"."""
    try:
        ok = await asyncio.to_thread(search.supported, choices, dataset_ids)
    except Exception:   # tìm lỗi: giữ nút, không đoán
        return choices
    return [c for c, good in zip(choices, ok) if good]


async def run(user: dict, cid: str, user_mid: int, text: str, history_path: list[dict], web: bool = False, allow_cache: bool = True):
    """Async generator SSE cho một lượt. user_mid = tin người dùng mà câu trả lời nối vào.
    allow_cache=False (bấm ↻ tạo lại): không dùng lại câu đã 👍, AI viết mới."""
    mode = "fast"
    turn_id = uuid.uuid4().hex
    _turns[turn_id] = {"user": user["id"]}
    try:
        evidence, sinfo, t0 = None, None, time.perf_counter()
        dom = db.get_domain((db.get_conversation(cid) or {}).get("domain_id")) or db.get_domain(2)
        prof = profile.get(dom)   # G4.3: hồ sơ lĩnh vực (cách trả lời, trích dẫn, hỏi lại, tìm kiếm, công cụ, vai trò, tìm web)
        web_blocked = web and not prof["web_allowed"]
        web = web and not web_blocked
        abi_mode = dom["engine"] == "abi"   # lĩnh vực ABI: dữ liệu abi.com.vn (system4/abi), luôn ở chế độ Chuyên gia
        active = db.active_datasets(user["id"], dom["id"], user["role"])
        # câu chào: xét khi có dữ liệu, ở ABI, và ở lĩnh vực "chỉ trả lời từ dữ liệu" kể cả khi CHƯA có dữ liệu (19/10: lĩnh vực FLM chưa
        # đồng bộ trả lời "Chào…" xong bị thay bằng "không có trong dữ liệu")
        gm = settings.get("GREETING_MODE") if active or abi_mode or prof["answer_mode"] != "free" else "off"
        gate = gm in ("code_first", "ai_first") and greet.is_greeting(text, history_path)   # quy tắc code: ngắn + có từ chào
        small_by_code = gm == "code_first" and gate        # code nhận trước: không tra dữ liệu
        ask_small = gm != "off" and not small_by_code       # AI được đánh dấu câu xã giao
        amb, table, abi_res, fp = None, None, None, None
        squery = search_query(text, history_path)
        if web:   # nút "Tìm web": chỉ DuckDuckGo, bỏ qua bộ dữ liệu và câu xã giao
            gm, gate, small_by_code, ask_small = "off", False, False, False
            evidence, sinfo = await asyncio.to_thread(websearch.search, squery)
            sinfo["search_ms"] = int((time.perf_counter() - t0) * 1000)
        elif abi_mode and not small_by_code:   # ABI: code nhận ý định + tính (đếm, sự kiện theo ngày…) trước, rồi mới tìm
            abi_res = await asyncio.to_thread(abi_turn.prepare, user["id"], text, squery, [d["id"] for d in active], history_path,
                                              prof.get("code_answer"))
            evidence, sinfo = abi_res["evidence"], abi_res["info"]
            sinfo["search_ms"] = int((time.perf_counter() - t0) * 1000)
        elif active and not small_by_code:   # có bộ dữ liệu đang bật -> Chuyên gia: tìm trước khi hỏi AI
            if settings.get("FASTPATH_ENABLED") and prof.get("fast_path", True):   # đường nhanh: code trả lời câu tra cứu rõ ràng, không tìm, không AI
                limit = settings.get("CLARIFY_MAX")
                can_ask = bool(prof["clarify"]) and limit > 0 and clarify_streak(history_path) < limit
                fp = await asyncio.to_thread(fastpath.answer, [d["id"] for d in active], text, history_path, prof["answer_mode"] != "free", can_ask)
        if fp and fp["use"]:
            evidence, sinfo = [], {"datasets": len(active), "fast_path": fp["trace"], "search_ms": int((time.perf_counter() - t0) * 1000)}
        elif active and not small_by_code and not web and not abi_mode:
            evidence, sinfo = await asyncio.to_thread(search.search, user["id"], squery, [d["id"] for d in active], profile.search_overrides(prof))
            if fp:
                sinfo["fast_path"] = fp["trace"]   # đường nhanh đã nhường: lý do hiện trong 🔍
            ids = [d["id"] for d in active]
            if search.is_overview(text):   # "tóm tắt file": các đoạn đầu của tệp văn bản trước, rồi tới đoạn tìm được (bỏ trùng)
                ov = await asyncio.to_thread(search.overview, ids)   # (19/10: chia theo mục thì một đoạn ngắn như tên tài liệu
                seen = {e["id"] for e in ov}                         #  vẫn có thể khớp chữ "nội dung" -> trước đây chặn mất đường này)
                if ov:
                    evidence = (ov + [e for e in evidence if e["id"] not in seen])[:max(len(ov), settings.get("RETRIEVAL_TOP_K"))]
                    sinfo["overview"] = len(ov)
            sinfo["search_ms"] = int((time.perf_counter() - t0) * 1000)
            if settings.get("TABLE_TOOL") and "table" in prof["tools"] and tabletool.triggered(text):
                t1 = time.perf_counter()
                async with llm.Turn(gpu.P1):
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
        if evidence is None and prof["answer_mode"] != "free" and not small_by_code:   # grounded / verbatim: không có dữ liệu thì không dùng kiến thức chung
            evidence, sinfo = [], {"datasets": len(active), "no_data": True, "search_ms": 0}
        if prof["persona"]:
            extra0.append(f"Vai trò riêng trong lĩnh vực «{dom['name']}»: {prof['persona']}")
        if not prof["clarify"]:
            extra0.append(profile.NO_CLARIFY)
        if prof["require_citation"] and evidence:
            extra0.append(profile.CITE)
        if dom["guardrail"]:   # guardrail của domain: lời dặn gửi thẳng cho AI ngay trước khi soạn câu trả lời
            extra0.append(f"Quy tắc riêng của lĩnh vực «{dom['name']}»: {dom['guardrail']}")
        if abi_res:
            extra0 += abi_res["extra"]   # ngày hôm nay + giờ đồng bộ: AI so "sắp tới / đã qua" đúng
        bm = lambda **k: build_messages(user["id"], cid, history_path, text, **{"evidence": evidence, "extra": extra0,
                                                                                "small_talk": ask_small and evidence is not None, "web": web, **k})
        msgs, info = bm(fast=True)
        if not prof["clarify"]:
            info["exhausted"] = True   # lĩnh vực không hỏi lại: lựa chọn (nếu AI vẫn đưa) thành văn bản, bỏ thẻ hỏi lại trùng tên
        prompts = [{"why": "lần gửi đầu", "messages": msgs}]
        yield sse({"type": "meta", "conversation_id": cid, "user_message_id": user_mid, "turn_id": turn_id, "mode": mode,
                   "specialist": evidence is not None})
        checks = {"foreign": info["foreign"], "upset": info["upset"], "streak": info["streak"], "greeting_gate": gate,
                  "greeting_mode": gm}
        if info["block"]:   # guardrail chặn: không gọi AI, không ghi nhớ
            b = info["block"]
            bmid = db.add_message(cid, "assistant", b["message"], "done", user_mid, {"guard": b["name"]}, pii_from=text)
            db.save_trace(bmid, cid, user["id"], {"mode": mode, "query": text, "blocked_by": b["name"], "checks": checks},
                          settings.get("TRACE_KEEP"))
            yield sse({"type": "delta", "text": b["message"]})
            yield sse({"type": "done"})
            return
        if fp and fp["use"]:   # đường nhanh: code trả lời (nguyên văn ô dữ liệu + nguồn) / hỏi lại bằng nút, không gọi AI
            r = fp["result"]
            ans = (settings.get("LANG_FALLBACK_APOLOGY") + "\n\n" if info["foreign"] else "") + r["content"]
            meta = {"specialist": True, "mode": mode,
                    "fast_path": {"kind": r["kind"], "route": r.get("route"), "ms": r["ms"], "state": fp["trace"]["state_out"]},
                    "sources": [{"n": i, "record_id": x["record_id"], "url": None, "title": x["title"], "dataset": x["dataset"], "score": None}
                                for i, x in enumerate(r.get("sources") or [], 1)],
                    "timing": {"llm_ms": 0, "total_ms": int((time.perf_counter() - t0) * 1000),
                               "fast_path_ms": fp["trace"]["total_ms"], "build_ms": fp["trace"]["build_ms"]}}
            if r["kind"] == "ask":
                meta["choices"] = r["choices"]
            fmid = db.add_message(cid, "assistant", ans, "done", user_mid, meta, pii_from=text)
            db.save_trace(fmid, cid, user["id"], {"mode": mode, "specialist": True, "query": text, "retrieval": sinfo, "checks": checks,
                                                  "prompts": [], "output": {"final_text": ans}, "timing": meta["timing"]}, settings.get("TRACE_KEEP"))
            yield sse({"type": "delta", "text": ans})
            yield sse({"type": "done"})
            return
        if amb and not info["exhausted"]:   # trùng tên: hỏi lại bằng code, không gọi AI
            q = ambig.question(amb)
            meta = {"specialist": True, "choices": amb["options"], "ambiguity": amb["phrase"], "mode": mode,
                    "retrieval": {k: sinfo.get(k) for k in ("datasets", "reranked", "candidates_n", "keyword", "vector", "search_ms")},
                    "timing": {"llm_ms": 0, "total_ms": int((time.perf_counter() - t0) * 1000)}}
            amid = db.add_message(cid, "assistant", q, "done", user_mid, meta, pii_from=text)
            db.save_trace(amid, cid, user["id"], {"mode": mode, "specialist": True, "query": squery, "retrieval": sinfo,
                                                  "checks": {**checks, "ambiguity": amb}, "prompts": [],
                                                  "output": {"final_text": q}, "timing": meta["timing"]}, settings.get("TRACE_KEEP"))
            yield sse({"type": "delta", "text": q})
            yield sse({"type": "done"})
            return
        if abi_res and abi_res["answer"]:   # ABI: code hiểu trọn câu hỏi -> câu trả lời bằng code, không gọi AI
            ans = abi_res["answer"]
            meta = {"specialist": True, "mode": mode, "abi": sinfo.get("abi"),
                    "sources": [{"n": i, "record_id": None, "url": s["url"], "title": s["title"], "dataset": "abi.com.vn", "score": None}
                                for i, s in enumerate(abi_res["sources"], 1)],
                    "timing": {"llm_ms": 0, "total_ms": int((time.perf_counter() - t0) * 1000)}}
            amid = db.add_message(cid, "assistant", ans, "done", user_mid, meta, pii_from=text)
            db.save_trace(amid, cid, user["id"], {"mode": mode, "specialist": True, "query": squery, "retrieval": sinfo, "checks": checks,
                                                  "prompts": [], "output": {"final_text": ans}, "timing": meta["timing"]}, settings.get("TRACE_KEEP"))
            yield sse({"type": "delta", "text": ans})
            yield sse({"type": "done"})
            return
        if prof["answer_mode"] == "verbatim" and evidence is not None and not small_by_code:   # trích nguyên văn bằng code, không gọi AI
            ans = profile.verbatim(evidence, settings.evidence_chars())
            meta = {"specialist": True, "mode": mode, "verbatim": True,
                    "sources": [{"n": i, "record_id": e.get("id"), "url": e.get("url"), "title": e["title"], "dataset": e["dataset"],
                                 "score": e.get("score")} for i, e in enumerate(evidence, 1)],
                    "timing": {"llm_ms": 0, "total_ms": int((time.perf_counter() - t0) * 1000)}}
            vmid = db.add_message(cid, "assistant", ans, "done", user_mid, meta, pii_from=text)
            db.save_trace(vmid, cid, user["id"], {"mode": mode, "specialist": True, "query": squery, "retrieval": sinfo, "checks": checks,
                                                  "prompts": [], "output": {"final_text": ans}, "timing": meta["timing"]}, settings.get("TRACE_KEEP"))
            yield sse({"type": "delta", "text": ans})
            yield sse({"type": "done"})
            return
        cacheable = answer_cache.eligible(text, history_path, evidence, web, abi_mode, info)
        hit = answer_cache.lookup(text, dom) if cacheable and allow_cache else None
        if hit:   # câu y chang đã được 👍: trả ngay, không xếp hàng GPU, không gọi model
            meta = {"mode": mode, "model": settings.get("FRIENDLY_MODEL"), "cached": {"from": hit["from"]}, "cacheable": True,
                    "cache_fp": answer_cache.fingerprint(dom), "timing": {"llm_ms": 0, "total_ms": int((time.perf_counter() - t0) * 1000)}}
            if hit["choices"]:
                meta["choices"] = hit["choices"]
            hmid = db.add_message(cid, "assistant", hit["answer"], "done", user_mid, meta, pii_from=text)
            db.save_trace(hmid, cid, user["id"], {"mode": mode, "query": text, "cached_from": hit["from"], "checks": checks, "prompts": [],
                                                  "output": {"final_text": hit["answer"]}, "timing": meta["timing"]}, settings.get("TRACE_KEEP"))
            yield sse({"type": "cached", "from": hit["from"]})
            yield sse({"type": "delta", "text": hit["answer"]})
            yield sse({"type": "done"})
            return
        if db.get_rules_only(user["id"]):   # G3.3: tài khoản bật "Chỉ trả lời bằng luật": lĩnh vực cần AI thì báo, không gọi AI
            msg = RULES_ONLY_MESSAGE
            rmid = db.add_message(cid, "assistant", msg, "done", user_mid, {"rules_only": True})
            db.save_trace(rmid, cid, user["id"], {"mode": mode, "query": text, "rules_only": True, "checks": checks}, settings.get("TRACE_KEEP"))
            yield sse({"type": "delta", "text": msg})
            yield sse({"type": "done"})
            return
        pos = llm.queue_position()
        if pos:
            yield sse({"type": "queue", "position": pos})
        prefix = settings.get("LANG_FALLBACK_APOLOGY") if info["foreign"] else ""
        state = {"kb": evidence is not None, "ask_small": ask_small and evidence is not None}
        meta, status, err, small = {}, "done", None, small_by_code
        draft = {}   # bản đầu đã hiện, khi một bước kiểm cần viết lại: {"mid", "why"}

        def revise(why: str):
            """Bước kiểm cần viết lại. Lần đầu: lưu câu trả lời đang hiện thành một phiên bản (người dùng mở lại được bằng ‹ ›)
            và báo giao diện giữ nguyên nó trong lúc kiểm. Trả sự kiện SSE, hoặc None nếu đã báo rồi."""
            if draft:
                return None
            content = _shown(state)[0]
            if prefix and content:
                content = f"{prefix}\n\n{content}"
            dmid = None
            if content:   # chữ lạ bị lọc hết: chưa hiện gì, không có bản đầu để giữ
                dmeta = {"mode": state.get("mode", mode), "model": settings.get("FRIENDLY_MODEL"), "draft": {"why": why},
                         **_sources_meta(content, state, evidence, small)}
                if evidence is not None:
                    dmeta["specialist"] = True
                dmid = db.add_message(cid, "assistant", content, "done", user_mid, dmeta, pii_from=text)
                db.save_trace(dmid, cid, user["id"], {"mode": mode, "specialist": evidence is not None, "status": "draft", "draft_why": why,
                                                      "query": squery if evidence is not None else text, "retrieval": sinfo, "checks": checks,
                                                      "prompts": prompts[:1], "output": {"final_text": content}}, settings.get("TRACE_KEEP"))
            draft.update(mid=dmid, why=why)
            return sse({"type": "checking", "draft_id": dmid, "why": why})

        async def quiet(m):   # viết lại sau khi kiểm: không hiện dần (bản đầu vẫn trên màn hình), chỉ cập nhật state
            async for _ in _fast(m, prefix, state):
                pass
        try:
            t_wait = time.perf_counter()
            async with llm.Turn():
                t_llm = time.perf_counter()
                meta["queue_ms"] = int((t_llm - t_wait) * 1000)   # G3.4: chờ tới lượt dùng GPU
                yield sse({"type": "start"})
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
                    if ev := revise("trả lời câu chào bằng “không có trong dữ liệu”"):
                        yield ev
                    msgs, _ = bm(fast=state["mode"] == "fast", evidence=None, small_talk=False, extra=[greet.SMALL_TALK_INSTRUCTION])
                    prompts.append({"why": "câu chào bị trả lời 'không có trong dữ liệu': viết lại kiểu xã giao", "messages": msgs})
                    state["kb"], state["ask_small"] = False, False
                    await quiet(msgs)
                if small:
                    meta["small_talk"] = "code" if small_by_code else meta.get("small_talk_override") or "ai"
                if evidence == [] and not web and not small and not state.get("replaced") and kb_violation("".join(state.get("parts") or [])):
                    # yêu cầu .docx: không dùng kiến thức chung. Tìm không thấy mà AI vẫn tự trả lời -> thay bằng câu cố định
                    msg = settings.get("KB_NOT_FOUND_MESSAGE") if active or abi_mode else NO_DATA_MESSAGE.format(name=dom["name"])
                    state["replaced"] = {"name": "Chỉ trả lời từ dữ liệu", "message": msg}
                    if not draft:   # đã có bản đầu trên màn hình: câu cố định thành phiên bản mới, không ghi đè bản đầu
                        yield sse({"type": "replace", "text": state["replaced"]["message"]})
                # ---- kiểm chi tiết bịa (NV5, 2A): viết lại một lần
                if settings.get("GROUNDING_CHECK") == "rewrite" and not small and not state.get("replaced"):
                    kb = evidence is not None
                    allowed = _allowed_text(text, history_path, evidence)
                    items = ground.ungrounded(_answer_text(state), allowed, kb, settings.get("BUSINESS_NAME"))
                    if items:
                        meta["grounding"] = {"items": items}
                        if ev := revise("có chi tiết không tìm thấy trong nguồn"):
                            yield ev
                        msgs, _ = bm(fast=state["mode"] == "fast", extra=extra0 + [ground.rewrite_instruction(items, kb)])
                        prompts.append({"why": "chi tiết không có nguồn: viết lại", "messages": msgs})
                        await quiet(msgs)
                        if not state.get("replaced"):
                            meta["grounding"]["after"] = ground.ungrounded(_answer_text(state), allowed, kb, settings.get("BUSINESS_NAME"))
                if prof["require_citation"] and evidence and not small and not state.get("replaced") and not _cited(state):
                    meta["cite_retry"] = True   # G4.3: lĩnh vực bắt buộc trích dẫn mà AI không ghi [n]: viết lại một lần
                    if ev := revise("thiếu số đoạn nguồn [n]"):
                        yield ev
                    msgs, _ = bm(fast=True, extra=extra0 + [profile.CITE_RETRY])
                    prompts.append({"why": "thiếu số đoạn nguồn: viết lại", "messages": msgs})
                    await quiet(msgs)
                    if not state.get("replaced") and not _cited(state):
                        meta["uncited"] = True
                if not state.get("replaced") and state["filter"].heavy_leak():   # lọt nhiều chữ lạ: viết lại một lần
                    meta["leak_retry"] = True
                    if ev := revise("lọt nhiều chữ không phải tiếng Việt"):
                        yield ev
                    msgs, _ = bm(fast=state["mode"] == "fast", leak_retry=True)
                    prompts.append({"why": "lọt nhiều chữ lạ: viết lại", "messages": msgs})
                    await quiet(msgs)
            if web_blocked:
                meta["web_blocked"] = True
                note = "\n\n_Lĩnh vực này không dùng Tìm web: câu trả lời trên không lấy từ web._"
                state.setdefault("parts", []).append(note)
                if not draft:   # có bản đầu: ghi chú nằm trong phiên bản mới, không nối vào bản đầu trên màn hình
                    yield sse({"type": "delta", "text": note})
            if web and (sinfo or {}).get("pii_masked") and not state.get("replaced"):   # G1.3 (D10): báo đã che số trước khi tìm web
                note = "\n\n_" + core_web.PII_NOTE + "_"
                state.setdefault("parts", []).append(note)
                if not draft:
                    yield sse({"type": "delta", "text": note})
            if settings.get("CHOICE_CHECK") and evidence is not None and not web and not small and state.get("choices") and not state.get("replaced"):
                kept = await _answerable(state["choices"], [d["id"] for d in active])   # nút gợi ý phải trả lời được từ dữ liệu
                meta["choices_filter"] = {"before": len(state["choices"]), "kept": len(kept)}
                state["choices"] = kept
        except (llm.QueueFull, llm.LLMError) as e:
            status, err = "error", str(e)
        except (asyncio.CancelledError, GeneratorExit):
            status = "stopped"   # người dùng bấm Dừng / rời trang: giữ phần đã sinh
            raise
        finally:
            meta["mode"] = state.get("mode", mode)
            meta["model"] = settings.get("FRIENDLY_MODEL")   # model lúc trả lời, cho feedback_log
            if "t_llm" in locals():
                meta["timing"] = {"llm_ms": int((time.perf_counter() - t_llm) * 1000), "total_ms": int((time.perf_counter() - t0) * 1000),
                                  "before_llm_ms": int((t_wait - t0) * 1000)}   # 20/10: tách thời gian trước AI (đường nhanh, tìm, dựng lời dặn)
                if fp:
                    meta["timing"].update(fast_path_ms=fp["trace"].get("total_ms"), build_ms=fp["trace"].get("build_ms"))
            f = state.get("filter")
            if f and (f.removed_letters or f.removed_other):
                meta["filtered"] = {"letters": f.removed_letters, "other": f.removed_other}
            if state.get("replaced"):
                meta["guard"] = state["replaced"]["name"]
                content, choices = state["replaced"]["message"], []
            else:
                content, choices = _shown(state)
            if prefix and not state.get("replaced") and (content or status != "error"):
                content = f"{prefix}\n\n{content}".strip()
            if evidence is not None:
                meta["specialist"] = True
                meta["retrieval"] = {k: sinfo.get(k) for k in ("datasets", "reranked", "candidates_n", "keyword", "vector", "search_ms", "web", "error",
                                                                 "timing", "requery")}
            if web:
                meta["web"] = True
            if abi_res:
                meta["abi"] = sinfo.get("abi")
            meta.update(_sources_meta(content, state, evidence, small))
            if draft.get("mid"):
                meta["revised_from"] = {"id": draft["mid"], "why": draft["why"]}   # giao diện: "bản đầu ở phiên bản trước"
            if cacheable and status == "done" and not err and not state.get("replaced") and not meta.get("leak_retry"):
                meta["cacheable"], meta["cache_fp"] = True, answer_cache.fingerprint(dom)   # 👍 thì người khác hỏi y chang được trả ngay
            if choices and not info["exhausted"]:
                meta["choices"] = choices
            elif choices:   # đã hết lượt hỏi lại mà AI vẫn đưa lựa chọn: hiện như văn bản
                content += "\n\n" + "\n".join(f"- {c}" for c in choices)
            mid, kept = None, bool(draft.get("mid")) and status != "done"
            if kept:   # dừng / lỗi lúc viết lại: giữ bản đầu làm câu trả lời, không lưu bản viết dở (người dùng chưa thấy nó)
                db.set_leaf(cid, draft["mid"])
                db.patch_trace(draft["mid"], "rewrite", {"status": status, "error": err, "why": draft["why"], "prompts": prompts[1:]})
                mid, err = draft["mid"], None
            elif err:
                mid = db.add_message(cid, "assistant", err, "error", user_mid, meta, pii_from=text)
            elif content:
                mid = db.add_message(cid, "assistant", content, status, user_mid, meta, pii_from=text)
            if mid and not kept:
                a = state.get("ans")
                db.save_trace(mid, cid, user["id"], {
                    "mode": mode, "final_mode": meta["mode"], "specialist": evidence is not None, "status": status, "error": err,
                    "query": squery if evidence is not None else text,
                    "retrieval": sinfo,
                    "checks": {**checks, "clarify_streak": info["streak"],
                               "clarify_exhausted": info["exhausted"], "instructions": info["instructions"],
                               "guard_replaced": meta.get("guard"), "kb_guard": meta.get("guard") == "Chỉ trả lời từ dữ liệu",
                               "filtered": meta.get("filtered"), "leak_retry": meta.get("leak_retry", False),
                               "memories_in_prompt": info["memories"],
                               "summary_in_prompt": info["summary"], "history_messages": info["history"],
                               "small_talk": meta.get("small_talk"), "small_talk_override": meta.get("small_talk_override"),
                               "grounding": meta.get("grounding")},
                    "prompts": prompts,
                    "output": {"raw_json": a.raw if a else None,
                               "raw_text": "".join(state.get("raw_text") or []) or None,
                               "plan": (a.final().get("plan") if a else state.get("plan")),
                               "final_text": content},
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
