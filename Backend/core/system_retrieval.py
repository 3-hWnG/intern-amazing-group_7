"""HỆ THỐNG 2 — RETRIEVAL (CSDL thủ tục nội bộ). Hệ thống MẶC ĐỊNH.

Chạy song song Hệ thống 1 (`system_websearch.py`): cùng nhận `TurnInput`, cùng
trả `TurnResult`, người dùng chọn bằng nút "Web search". Sơ đồ đầy đủ +
các quyết định thiết kế: Documentation/PHASE2_RETRIEVAL.md.

    [ Người dân hỏi ]  "t người bình định muốn dk kết hôn"
          │
          ▼
    [ Tra TỪ KHOÁ — không LLM ]  retrieval.parse_query(): bỏ lời đệm, bung
          │   viết tắt, tách tên tỉnh -> {"keyword": "nguoi dang ky ket hon",
          │                               "provinces": ["Bình Định"]}
          │   -> FTS5 ba tầng
          │
          ├─ không khớp chắc (mơ hồ, gõ sai "đkj") -> LLM 1 viết lại khoá
          │     (tối đa 3 lượt) -> vẫn không có: xin lỗi, NÊU RÕ khoá + câu gốc
          │
          ├─ MCQ 1 "thủ tục chính"  (Đăng ký khai sinh / Đăng ký lại khai sinh…)
          ├─ MCQ 2 "dạng cụ thể"    (lưu động / có yếu tố nước ngoài / bản tỉnh…)
          ├─ MCQ phụ "trường hợp", "tư cách" (tối đa RETRIEVAL_MAX_MCQ_ROUNDS)
          │     trạng thái nằm ở app.db (`retrieval_pending`), vì một lượt
          │     HTTP không giữ được trạng thái giữa các vòng
          │
          ▼
    [ Dựng bảng bằng CODE ]  procedure_table.build() — zero hallucination
          │
          ▼
    [ LLM 2: chăm sóc khách hàng ]  đọc lịch sử + bảng, chỉ trả lời trong bảng
                                    phát hiện `newProcedure` -> mời sang ô chat mới

BỐN MỐC BÀN GIAO (giữ nguyên tên hàm từ bản khung):
    extract_keys()   LLM 1
    lookup()         CSDL (không LLM)
    build_table()    CODE (không LLM)
    follow_up()      LLM 2

KHÔNG BAO GIỜ trả lời khi không có bản ghi. Không có thì nói không có, rồi mời
người dùng tự bấm Web search — việc chuyển hệ thống luôn là LỰA CHỌN của họ.
"""

from __future__ import annotations

import json
import re
import sqlite3
import time
from typing import Callable

import developer_mode
from config import (PROCEDURES_DB_PATH, RETRIEVAL_ENABLED,
                    RETRIEVAL_FOLLOWUP_ENABLED, RETRIEVAL_MAX_KEY_ATTEMPTS,
                    RETRIEVAL_MAX_MCQ_ROUNDS, SYSTEM_RETRIEVAL)
from core import llm, procedure_table
from core.turn import (MODE_CHAT, MODE_EXACT, MODE_RESUBMIT, MODES, TurnInput,
                       TurnResult)
from db.repositories import MCQMemory, RetrievalPending
from prompts import retrieval_templates as RT

from Database.pipeline import retrieval as R

# Lời nhắn khi Hệ thống 2 bị tắt bằng cờ cấu hình.
UNAVAILABLE_TEXT = (
    "Hệ thống tra cứu từ cơ sở dữ liệu nội bộ (Hệ thống 2) đang tắt.\n\n"
    "Bạn bấm nút **🌐 Web search** ở khung nhập bên dưới để chuyển sang tra cứu "
    "trực tiếp từ các trang .gov.vn — hệ thống sẽ mở một cuộc trò chuyện mới cho bạn."
)

NO_DB_TEXT = (
    "Chưa có cơ sở dữ liệu thủ tục trên máy này.\n\n"
    "Người cài đặt cần chạy một lần:\n"
    "`python -m Database.pipeline.run_pipeline --all`\n\n"
    "Trong lúc chờ, bạn bấm nút **🌐 Web search** để tra trực tiếp từ các trang .gov.vn."
)


# ---------------------------------------------------------------------------
# Kết nối CSDL thủ tục — mỗi luồng một kết nối (sqlite3 không chia sẻ được).
# ---------------------------------------------------------------------------
import threading

_local = threading.local()


def _conn() -> sqlite3.Connection | None:
    """None nếu máy chưa dựng CSDL — tầng trên phải báo thật, không được sập."""
    conn = getattr(_local, "conn", None)
    if conn is not None:
        return conn
    if not PROCEDURES_DB_PATH.exists():
        return None
    try:
        conn = R.connect(PROCEDURES_DB_PATH)
        # Bảng rỗng cũng coi như chưa có CSDL: đỡ trả lời "không tìm thấy" cho mọi câu hỏi.
        if R.count_active(conn) == 0:
            conn.close()
            return None
    except Exception:
        return None
    _local.conn = conn
    return conn


def _domains(conn: sqlite3.Connection, limit: int | None = None) -> list[str]:
    """Danh sách lĩnh vực THẬT để LLM 1 chọn. Lấy từ CSDL, không hardcode.

    Không cắt mặc định: số lĩnh vực đổi theo phạm vi cào (1.407 thủ tục = 103,
    cấp Xã/Phường 1.350 thủ tục = 121). Cắt cứng thì lĩnh vực ít thủ tục nhất
    không bao giờ được chọn.
    """
    cached = getattr(_local, "domains", None)
    if cached is None:
        cached = [r[0] for r in conn.execute(
            "SELECT domain, COUNT(*) n FROM procedures WHERE status='active'"
            " AND TRIM(domain) <> '' GROUP BY domain ORDER BY n DESC")]
        _local.domains = cached
    return cached[:limit]


# ---------------------------------------------------------------------------
# 1. LLM 1 — Router & Extractor
# ---------------------------------------------------------------------------
def extract_keys(question: str, history: list[dict], profile: dict,
                 domains: list[str] | None = None,
                 tried: list[str] | None = None) -> dict:
    """Câu hỏi của người dân -> khoá tra cứu.

    Ra: {"primary_keyword": "đăng ký kết hôn", "domain": "Hộ tịch",
         "entities": ["Bình Định"]}

    `domain` BẮT BUỘC nằm trong `domains` (103 lĩnh vực thật của cổng). Mô hình
    chép sai một ký tự thì coi như rỗng — thà không lọc còn hơn lọc nhầm.
    `tried` khác rỗng = đây là lần SINH LẠI sau khi tra không ra gì.
    """
    domains = domains or []
    user = (RT.retry_user(question, domains, tried) if tried
            else RT.extract_user(question, domains, history))
    raw = llm.chat_json("understand", RT.EXTRACT_SYSTEM, user, RT.EXTRACT_SCHEMA)

    keyword = str(raw.get("primary_keyword") or "").strip()
    domain = str(raw.get("domain") or "").strip()
    entities = [str(e).strip() for e in (raw.get("entities") or []) if str(e).strip()]

    # Mô hình nhỏ hay "sáng tạo" tên lĩnh vực. Chỉ nhận nếu khớp CHÍNH XÁC.
    if domain not in domains:
        domain = ""
    # Không rút được gì -> dùng nguyên câu hỏi, FTS vẫn khớp không dấu được.
    if not keyword:
        keyword = question.strip()

    # Tỉnh trong hồ sơ người dùng là ngữ cảnh phụ, KHÔNG phải bộ lọc: chỉ xếp
    # bản của tỉnh đó lên trước ở MCQ "dạng cụ thể" (retrieval.axis_for_variants).
    if profile.get("province") and profile["province"] not in entities:
        entities.append(profile["province"])

    return {"primary_keyword": keyword, "domain": domain, "entities": entities[:5]}


# ---------------------------------------------------------------------------
# 2. Truy vấn CSDL — KHÔNG qua LLM
# ---------------------------------------------------------------------------
# Số ứng viên lấy về để gom thành "thủ tục chính". Rộng hơn số nút MCQ (6)
# vì nhiều ứng viên rơi chung một nhóm (lưu động, có yếu tố nước ngoài…).
CANDIDATE_POOL = 30


def lookup(keys: dict, conn: sqlite3.Connection | None = None,
           limit: int = CANDIDATE_POOL) -> list[dict]:
    """Khoá -> danh sách ứng viên đã xếp hạng (rỗng nếu không khớp gì).

    Trả về DANH SÁCH chứ không phải một bản ghi: kiến trúc mới cần biết có bao
    nhiêu ứng viên để quyết định hỏi MCQ hay trả bảng thẳng. Đo thật: "đăng ký
    kết hôn" ra 5 thủ tục đều `confident=True` (lưu động, có yếu tố nước ngoài,
    đăng ký lại…) — trả đại một cái là trả sai cho 4/5 người hỏi.
    """
    conn = conn or _conn()
    if conn is None:
        return []
    return R.search_in_domain(conn, keys["primary_keyword"], keys.get("domain", ""), limit)


# ---------------------------------------------------------------------------
# 3. Dựng bảng bằng CODE — zero hallucination
# ---------------------------------------------------------------------------
def build_table(record: dict, *, conn=None, expired=None, picked=None,
                memory_used=None) -> dict:
    """Bản ghi CSDL -> bảng cho giao diện. Không có LLM trong hàm này."""
    return procedure_table.build(record, expired=expired, picked=picked,
                                 memory_used=memory_used)


# ---------------------------------------------------------------------------
# 4. LLM 2 — Chăm sóc khách hàng trên bảng đã trả
# ---------------------------------------------------------------------------
def is_new_procedure(conn, question: str, current_proc_id: str) -> bool:
    """Người dân đã chuyển sang hỏi thủ tục KHÁC chưa? (boundary control)

    KHÔNG dùng LLM — đo thật: Qwen2.5 1.5B trả `true` cho 9/9 câu thử, kể cả
    "lệ phí bao nhiêu tiền?" và "cảm ơn bạn". Dùng nó thì mọi câu hỏi tiếp đều
    bị đá sang ô chat mới và LLM 2 không bao giờ chạy. Chi tiết + số đo:
    Documentation/PHASE2_RETRIEVAL.md §4.6.

    Luật thay thế dựa trên chính CSDL — xem `retrieval.is_other_procedure()`.
    """
    try:
        return R.is_other_procedure(conn, question, current_proc_id)
    except Exception:
        # Hỏng thì KHÔNG chặn người dùng: thà trả lời trong phạm vi bảng còn
        # hơn đuổi họ sang ô chat mới vì một lỗi kỹ thuật.
        return False


def follow_up(question: str, history: list[dict], table: dict) -> str:
    """Hỏi tiếp sau khi đã có bảng: trả lời CHỈ trong phạm vi bảng.

    Bám câu hỏi (đo trên mô hình thật, xem PLAN_SYSTEM2_REBUILD §B3):
      - chỉ đưa các MỤC liên quan tới câu hỏi (`sections_for`), không cả bảng;
      - kèm CÂU HỎI trước đó của người dân (không kèm câu trả lời của trợ lý:
        đưa cả lượt đáp vào thì mô hình 1.5B lẫn vai người hỏi/người đáp);
      - vai `care`: tối đa 320 token thay vì 900.
    """
    previous = next((m.get("content") or "" for m in reversed(history or [])
                     if m.get("role") == "user"), "")
    if procedure_table.is_rewrite(question):
        # "Ngắn hơn nữa", "chi tiết hơn" -> VIẾT LẠI câu trả lời trước, trên đúng
        # các mục của câu hỏi trước. Câu trả lời trước đưa vào như VĂN BẢN cần
        # sửa, không như một lượt chat (đưa như lượt chat thì mô hình lẫn vai).
        last_answer = next((m.get("content") or "" for m in reversed(history or [])
                            if m.get("role") == "assistant"), "")
        secs = procedure_table.sections_for(previous)
        text = procedure_table.to_text(table, only=(secs + ["scope"]) if secs else None)
        return _llm_text(lambda: llm.chat(
            "care", RT.CARE_SYSTEM,
            RT.rewrite_user(question, text, previous[:200], last_answer[:1500]),
            history=None))

    secs = procedure_table.sections_for(question)
    text = procedure_table.to_text(table, only=(secs + ["scope"]) if secs else None)
    return _llm_text(lambda: llm.chat("care", RT.CARE_SYSTEM,
                                      RT.care_user(question, text, previous[:200]),
                                      history=None))


# Mô hình 1.5B đôi khi chen chữ Hán ("缴纳") hoặc chép lại luật trong prompt
# ("Chỉ dùng thông tin có trong bảng.") vào câu trả lời — đo được ở bản thử.
_CJK = re.compile(r"[\u3000-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff00-\uffef]+")
_ECHO = re.compile(r"^\s*(?:Chỉ dùng thông tin có trong bảng\.?|LUẬT BẮT BUỘC:?)\s*",
                   re.IGNORECASE)


def _llm_text(call: Callable[[], str], fallback: str = "") -> str:
    """Gọi LLM, sinh lại MỘT lần nếu có chữ Hán/Nhật; còn thì cắt bỏ phần đó."""
    text = ""
    for _ in range(2):
        text = (call() or "").strip()
        if not _CJK.search(text):
            break
    text = _CJK.sub("", text)
    text = "\n".join(_ECHO.sub("", line) for line in text.splitlines()).strip()
    # Dấu """ bao "văn bản cần viết lại" trong prompt — mô hình hay chép theo.
    text = text.strip('"').strip() if text.startswith('"""') else text
    return text or fallback


# ---------------------------------------------------------------------------
# MCQ — hỏi lại cho đúng, và nhớ hộ người dùng nếu họ muốn
# ---------------------------------------------------------------------------
def _apply_memory(axes: list[dict], memory: dict) -> tuple[list[dict], dict, list]:
    """Bỏ bớt câu hỏi mà trí nhớ người dùng đã trả lời sẵn.

    Đây chính là "hỏi xem người dùng có muốn nhớ lựa chọn để về sau đỡ phải
    chọn hay không" của Proposal — dùng nhiều thì hỏi ít đi.
    """
    remaining, auto, used = [], {}, []
    for ax in axes:
        remembered = memory.get(ax["axis"])
        if remembered and any(o["value"] == remembered for o in ax["options"]):
            auto[ax["axis"]] = remembered
            used.append({"axis": ax["axis"], "value": remembered,
                         "question": ax["question"]})
        else:
            remaining.append(ax)
    return remaining, auto, used


def _match_answer(text: str, options: list[dict]) -> str | None:
    """Câu trả lời của người dùng -> giá trị lựa chọn. None nếu không khớp.

    Nhận cả ba kiểu: bấm nút (gửi đúng nhãn), gõ số thứ tự, gõ một phần nhãn.
    """
    from Database.pipeline.textutil import fold
    raw = (text or "").strip()
    if not raw:
        return None

    # 1. khớp nguyên văn nhãn hoặc giá trị (nút bấm gửi đúng nhãn)
    folded = fold(raw)
    for o in options:
        if folded in (fold(o["label"]), fold(str(o["value"]))):
            return o["value"]

    # 2. số thứ tự: "1", "chọn 2", "số 3"
    digits = "".join(ch for ch in raw if ch.isdigit())
    if digits and len(digits) <= 2 and len(raw) <= 12:
        idx = int(digits) - 1
        if 0 <= idx < len(options):
            return options[idx]["value"]

    # 3. nhãn nằm gọn trong câu trả lời, hoặc ngược lại
    for o in options:
        fl = fold(o["label"])
        if fl and (fl in folded or (len(folded) > 8 and folded in fl)):
            return o["value"]
    return None


def _mcq_result(res: TurnResult, axis: dict, name_hint: str = "") -> None:
    """Gắn một vòng MCQ vào TurnResult để giao diện vẽ."""
    lead = f"Mình tìm thấy **{name_hint}**.\n\n" if name_hint else ""
    res.kind = "clarify"
    res.text = lead + axis["question"]
    res.choices = [o["label"] for o in axis["options"]]
    res.table = {
        "kind": "mcq",
        "axis": axis["axis"],
        "question": axis["question"],
        "options": axis["options"],
        # Trục mô tả NGƯỜI DÙNG mới cho nhớ. Trục mô tả CÂU HỎI thì không —
        # nhớ "lần trước chọn thủ tục X" rồi áp cho câu sau là trả lời sai.
        "memorable": bool(axis.get("memorable")),
        "remember_label": "Nhớ lựa chọn này cho những lần sau",
    }


# ---------------------------------------------------------------------------
# Điều phối một lượt của Hệ thống 2
# ---------------------------------------------------------------------------
def run_turn(inp: TurnInput, status: Callable[[str], None] = lambda _: None) -> TurnResult:
    dev = developer_mode.turn(inp.question, inp.conversation_id)
    res = TurnResult(system=SYSTEM_RETRIEVAL)
    clock = time.time()

    def lap(name: str, since: float) -> int:
        ms = int((time.time() - since) * 1000)
        res.timings[name] = res.timings.get(name, 0) + ms
        return ms

    try:
        if not RETRIEVAL_ENABLED:
            res.kind, res.text = "unavailable", UNAVAILABLE_TEXT
            dev.event("retrieval_disabled", note="RETRIEVAL_ENABLED=false")
            return res

        conn = _conn()
        if conn is None:
            res.kind, res.text = "unavailable", NO_DB_TEXT
            dev.event("no_database", note=str(PROCEDURES_DB_PATH))
            return res

        conv_id = inp.conversation_id
        pending = RetrievalPending.get(conv_id) if conv_id else None
        memory = MCQMemory.all_for(inp.user_id) if inp.user_id else {}

        # Ba trạng thái của một ô chat, đọc từ `retrieval_pending`:
        #   không có dòng           -> CHAT  (chưa tra gì)
        #   có `axis`               -> đang giữa vòng MCQ của 🎯
        #   có `proc_id`, không axis -> CARE  (đã ra bảng = đã dùng 🎯 thành công)
        mode = inp.mode if inp.mode in MODES else MODE_CHAT
        dev.event("mode", mode=mode,
                  state=("mcq" if pending and pending.get("axis") else
                         "care" if pending and pending.get("proc_id") else "chat"))

        # "Tra lại" dưới bảng: người dùng báo mình hiểu sai -> xoá bảng cũ, tra
        # lại từ đầu trong CÙNG ô chat. Không tính là lần 🎯 thứ hai.
        if mode == MODE_RESUBMIT:
            if conv_id:
                RetrievalPending.clear(conv_id)
            pending, mode = None, MODE_EXACT

        # ── A. Đang chờ trả lời MCQ? (bấm nút MCQ = tin nhắn thường) ────
        if pending and pending.get("axis") and mode == MODE_CHAT:
            picked_value = _match_answer(inp.question, pending["options"])
            if picked_value is not None:
                dev.event("mcq_answer", axis=pending["axis"], value=str(picked_value))
                return _resolve(conn, inp, res, dev, lap, pending, picked_value, status)
        if pending and pending.get("axis"):
            # Gõ câu khác, hoặc bấm 🎯 với câu mới -> bỏ vòng MCQ cũ.
            dev.event("mcq_abandoned", question=inp.question[:120])
            RetrievalPending.clear(conv_id)
            pending = None

        # ── B. Đã có bảng rồi ────────────────────────────────────────────
        if pending and pending.get("proc_id"):
            if mode == MODE_EXACT:
                # Proposal: mỗi ô chat chỉ 🎯 thành công MỘT lần.
                return _exact_used(conn, inp, res, dev, pending)
            return _care(conn, inp, res, dev, lap, pending, status)

        # ── C0. Tin nhắn thường, chưa có bảng -> LLM 2 trò chuyện ─────────
        if mode == MODE_CHAT:
            return _chat(conn, inp, res, dev, lap, status)

        # 🎯 với câu chỉ có lời chào/cảm ơn -> KHÔNG đem đi tra. Đo được ở bản
        # chạy thật: "Chào" + 🎯 ra MCQ toàn thủ tục chẳng liên quan.
        if R.is_chitchat(inp.question):
            res.kind = "chitchat"
            res.intent = {"intent": "exact_needs_procedure", "standalone_question": inp.question}
            res.text = RT.EXACT_NEEDS_PROCEDURE
            dev.event("exact_chitchat", question=inp.question[:80])
            return res

        # ── C. 🎯 Tìm chính xác: TỪ KHOÁ trước, LLM 1 chỉ khi từ khoá trượt ──
        # Nhóm chốt (2026-09-24): tra thẳng bằng từ khoá là đường chính. LLM 1
        # chỉ được gọi khi CSDL không khớp chắc — câu hỏi mơ hồ hoặc gõ sai
        # ("đkj"). Sai sót còn lại đã có MCQ "thủ tục chính -> dạng cụ thể" hứng.
        status("Đang tìm thủ tục trong cơ sở dữ liệu…")
        q = R.parse_query(inp.question)
        provinces = list(q["provinces"])
        if inp.profile.get("province") and inp.profile["province"] not in provinces:
            provinces.append(inp.profile["province"])

        t = time.time()
        hits = R.search(conn, q["keyword"], CANDIDATE_POOL) if q["keyword"] else []
        keys = {"primary_keyword": q["keyword"], "domain": "", "entities": provinces,
                "source": "keyword"}
        dev.event("keyword_search", ms=lap("search", t), keyword=q["keyword"],
                  provinces=provinces, n_hits=len(hits), strong=R.is_strong(hits))
        tried = [q["keyword"]] if q["keyword"] else []

        if not R.is_strong(hits):
            # Dừng khi có kết quả CHẮC, không phải khi có kết quả bất kỳ: tầng 3
            # của FTS là OR nên gần như luôn moi ra thứ gì đó. Kết quả yếu vẫn
            # giữ làm phương án cuối, nhưng thử diễn đạt khác trước đã.
            status("Chưa khớp từ khoá — đang nhờ mô hình hiểu lại câu hỏi…")
            domains = _domains(conn)
            for attempt in range(1, RETRIEVAL_MAX_KEY_ATTEMPTS + 1):
                t = time.time()
                k = extract_keys(inp.question, inp.history, inp.profile, domains,
                                 tried if attempt > 1 else None)
                dev.event("extract_keys", ms=lap("understand", t), attempt=attempt, **k)

                t = time.time()
                h = lookup(k, conn)
                strong = R.is_strong(h)
                dev.event("lookup", ms=lap("search", t), attempt=attempt, n_hits=len(h),
                          strong=strong, keyword=k["primary_keyword"])

                k = {**k, "entities": list(dict.fromkeys(k["entities"] + provinces)),
                     "source": "llm1"}
                if h and not hits:             # giữ phương án cuối đầu tiên tìm được
                    hits, keys = h, k
                if strong:
                    hits, keys = h, k
                    break
                tried.append(k["primary_keyword"])
                if attempt < RETRIEVAL_MAX_KEY_ATTEMPTS:
                    status(f"Chưa chắc — đang thử cách diễn đạt khác ({attempt}/{RETRIEVAL_MAX_KEY_ATTEMPTS})…")

        res.intent = {"intent": "retrieval", "standalone_question": inp.question, **keys}

        # Không ra gì cả -> xin lỗi, NÊU RÕ khoá đã tìm + câu hỏi gốc.
        if not hits:
            res.kind = "no_evidence"
            res.text = RT.not_found_text(" / ".join(dict.fromkeys(tried)), inp.question)
            dev.event("not_found", tried=tried)
            if conv_id:
                RetrievalPending.clear(conv_id)
            return res

        low_conf = not R.is_strong(hits)
        if low_conf:
            dev.event("low_confidence", keyword=keys.get("primary_keyword", ""),
                      n_hits=len(hits))
        return _resolve_from_hits(conn, inp, res, dev, lap, keys, hits, memory, status,
                                  low_confidence=low_conf)

    except llm.LLMError as exc:
        res.kind = "error"
        res.text = ("Mình không kết nối được mô hình ngôn ngữ nên chưa hiểu được câu hỏi. "
                    f"Kiểm tra Ollama đang chạy và đã tải mô hình.\n\nChi tiết: {exc}")
        dev.event("llm_error", note=str(exc))
        return res
    except Exception as exc:                      # noqa: BLE001 — một lượt hỏng không được làm sập app
        res.kind = "error"
        res.text = f"Hệ thống 2 gặp lỗi khi tra cứu cơ sở dữ liệu.\n\nChi tiết: {exc}"
        dev.event("error", note=str(exc))
        return res
    finally:
        res.timings["total"] = int((time.time() - clock) * 1000)
        dev.set(kind=res.kind, verdict=res.verdict, intent=res.intent.get("intent", ""),
                standalone=res.intent.get("standalone_question", ""),
                queries=[res.intent.get("primary_keyword", "")],
                sources=[s.get("url") or s.get("title") for s in res.sources],
                timings=res.timings)
        dev.finish()


# ---------------------------------------------------------------------------
# Các nhánh con của một lượt
# ---------------------------------------------------------------------------
def _resolve_from_hits(conn, inp: TurnInput, res: TurnResult, dev, lap,
                       keys: dict, hits: list[dict], memory: dict,
                       status: Callable[[str], None],
                       picked: dict | None = None, rounds: int = 0,
                       low_confidence: bool = False) -> TurnResult:
    """Có ứng viên rồi: hỏi "thủ tục chính" -> "dạng cụ thể", rồi mới dựng bảng.

    Hai MCQ này KHÔNG tính vào `RETRIEVAL_MAX_MCQ_ROUNDS`: chọn đúng thủ tục là
    việc bắt buộc; giới hạn vòng chỉ để khỏi hỏi quá nhiều trục PHỤ (trường
    hợp, tư cách) sau khi đã chốt thủ tục.
    """
    picked = dict(picked or {})
    conv_id = inp.conversation_id
    provinces = keys.get("entities") or []

    def ask(axis: dict) -> TurnResult:
        if conv_id:
            RetrievalPending.save(
                conv_id, question=inp.question, keys=keys,
                candidates=[{"proc_id": h["proc_id"], "name": h["name"],
                             "domain": h.get("domain", "")} for h in hits],
                axis=axis["axis"], options=axis["options"], picked=picked,
                rounds=rounds)
        _mcq_result(res, axis)
        dev.event("mcq_ask", axis=axis["axis"], n_options=len(axis["options"]))
        return res

    if R.AXIS_PROCEDURE not in picked:
        # MCQ 1 — thủ tục chính. Không ứng viên nào chắc -> kèm lối thoát
        # "không có cái nào đúng ý tôi" (kể cả khi chỉ còn một nhóm).
        head = picked.get(R.AXIS_FAMILY)
        if head is None:
            fam = R.axes_for_families(conn, hits, low_confidence, provinces)
            if fam:
                return ask(fam[0])
            head = R.family_of(conn, hits[0]["proc_id"]) if hits else ""

        # MCQ 2 — dạng cụ thể: TOÀN BỘ thành viên của nhóm trong CSDL.
        variants = R.axis_for_variants(conn, head, provinces)
        if variants:
            return ask(variants)
        picked[R.AXIS_PROCEDURE] = R.only_member(conn, head) or (hits[0]["proc_id"] if hits else "")

    proc_id = picked[R.AXIS_PROCEDURE]
    if not proc_id:
        res.kind = "no_evidence"
        res.text = RT.not_found_text(keys.get("primary_keyword", ""), inp.question)
        if conv_id:
            RetrievalPending.clear(conv_id)
        return res
    return _deliver(conn, inp, res, dev, lap, keys, proc_id, picked, memory,
                    status, rounds, hits)


def _deliver(conn, inp: TurnInput, res: TurnResult, dev, lap, keys: dict,
             proc_id: str, picked: dict, memory: dict,
             status: Callable[[str], None], rounds: int,
             hits: list[dict] | None = None) -> TurnResult:
    """Đã chốt được thủ tục: hỏi nốt các trục còn phân nhánh rồi trả bảng."""
    conv_id = inp.conversation_id
    status("Đang tra cứu cơ sở dữ liệu thủ tục…")

    t = time.time()
    case_ordinal = picked.get(R.AXIS_CASE)
    record = R.build_record(conn, proc_id,
                            int(case_ordinal) if case_ordinal is not None else None)
    dev.event("build_record", ms=lap("search", t), proc_id=proc_id, found=bool(record))

    if record is None:
        expired = R.is_expired(conn, proc_id)
        res.kind = "no_evidence"
        res.text = (RT.EXPIRED_WARNING if expired
                    else RT.not_found_text(keys.get("primary_keyword", ""), inp.question))
        if conv_id:
            RetrievalPending.clear(conv_id)
        return res

    # Các trục còn lại: bỏ bớt cái trí nhớ đã trả lời hộ.
    axes = R.axes_for_record(conn, record)
    axes = [a for a in axes if a["axis"] not in picked]
    axes, auto, memory_used = _apply_memory(axes, memory)
    picked.update(auto)
    for m in memory_used:
        if inp.user_id:
            MCQMemory.mark_used(inp.user_id, m["axis"])
    if memory_used:
        dev.event("mcq_memory", used=[m["axis"] for m in memory_used])

    # Trí nhớ vừa chốt thêm trục "trường hợp"? Dựng lại bản ghi cho đúng nhánh.
    if auto.get(R.AXIS_CASE) is not None:
        record = R.build_record(conn, proc_id, int(auto[R.AXIS_CASE]))

    if axes and rounds < RETRIEVAL_MAX_MCQ_ROUNDS:
        axis = axes[0]
        if conv_id:
            RetrievalPending.save(
                conv_id, question=inp.question, keys=keys,
                candidates=[{"proc_id": h["proc_id"], "name": h["name"],
                             "domain": h.get("domain", "")} for h in (hits or [])],
                proc_id=proc_id, axis=axis["axis"], options=axis["options"],
                picked=picked, rounds=rounds + 1)
        _mcq_result(res, axis, name_hint=record["name"])
        dev.event("mcq_ask", axis=axis["axis"], n_options=len(axis["options"]),
                  proc_id=proc_id)
        return res

    # ── Dựng bảng ───────────────────────────────────────────────────────
    status("Đang dựng bảng thông tin…")
    t = time.time()
    expired = R.is_expired(conn, proc_id)
    # Dựng lại danh sách "trí nhớ đã đỡ được câu nào" từ `picked`, KHÔNG dùng
    # `memory_used` của riêng lượt này: một trục có thể đã được trí nhớ chốt từ
    # vòng MCQ trước, lúc đó bảng chưa ra nên chưa khoe được với người dùng.
    shown_memory = [{"axis": ax, "value": val, "question": R.AXIS_QUESTION.get(ax, "")}
                    for ax, val in picked.items()
                    if ax in R.MEMORABLE_AXES and memory.get(ax) == val]
    table = build_table(record, conn=conn, expired=expired, picked=picked,
                        memory_used=shown_memory)
    res.table = table
    res.kind = "answer"
    # Nhãn trên giao diện: "Từ database" — bảng do CODE dựng từ dữ liệu cào
    # thẳng dichvucong.gov.vn, không phải câu trả lời "chưa kiểm chứng".
    res.intent = {**res.intent, "answer_source": "database"}
    res.text = ((RT.EXPIRED_WARNING + "\n\n") if expired else "") + \
        procedure_table.summary_line(table)
    res.sources = [{"id": "S1", "title": f"Cổng Dịch vụ công — {record['name']}",
                    "url": table["meta"]["portal_url"], "trust": "official"}] \
        if table["meta"]["portal_url"] else []
    dev.event("build_table", ms=lap("answer", t), proc_id=proc_id,
              picked=json.dumps(picked, ensure_ascii=False))

    # Ghi lại để lượt sau vào thẳng chế độ chăm sóc khách hàng (LLM 2).
    if conv_id:
        RetrievalPending.save(conv_id, question=inp.question, keys=keys,
                              candidates=[], proc_id=proc_id, axis="",
                              options=[], picked=picked, rounds=rounds)
    return res


def _resolve(conn, inp: TurnInput, res: TurnResult, dev, lap, pending: dict,
             value, status: Callable[[str], None]) -> TurnResult:
    """Người dùng vừa trả lời MCQ -> đi tiếp."""
    keys = pending.get("keys") or {}

    # Người dùng bấm "Không có thủ tục nào đúng ý tôi" -> đi thẳng nhánh xin lỗi.
    if value == R.NONE_OF_THESE:
        question = pending.get("question") or inp.question
        res.kind = "no_evidence"
        res.text = RT.not_found_text(keys.get("primary_keyword", ""), question)
        res.intent = {"intent": "retrieval", "standalone_question": question, **keys}
        dev.event("user_rejected_candidates",
                  keyword=keys.get("primary_keyword", ""))
        RetrievalPending.clear(inp.conversation_id)
        return res

    picked = dict(pending.get("picked") or {})
    picked[pending["axis"]] = value
    memory = MCQMemory.all_for(inp.user_id) if inp.user_id else {}
    rounds = int(pending.get("rounds") or 0)

    # Giữ câu hỏi GỐC: "1" hay "Công dân Việt Nam" không phải câu hỏi tra cứu.
    original = TurnInput(question=pending.get("question") or inp.question,
                         history=inp.history, summary=inp.summary,
                         profile=inp.profile, conversation_id=inp.conversation_id,
                         system=inp.system, user_id=inp.user_id)
    res.intent = {"intent": "retrieval", "standalone_question": original.question, **keys}

    proc_id = picked.get(R.AXIS_PROCEDURE) or pending.get("proc_id") or ""
    if proc_id:
        return _deliver(conn, original, res, dev, lap, keys, proc_id, picked,
                        memory, status, rounds)

    # Vừa chọn "thủ tục chính" -> hỏi tiếp "dạng cụ thể" (hoặc giao luôn nếu
    # nhóm chỉ có một thủ tục). Ứng viên lấy lại từ lượt trước.
    hits = pending.get("candidates") or []
    return _resolve_from_hits(conn, original, res, dev, lap, keys, hits, memory,
                              status, picked, rounds)


def _care(conn, inp: TurnInput, res: TurnResult, dev, lap, pending: dict,
          status: Callable[[str], None]) -> TurnResult:
    """Chế độ chăm sóc khách hàng: đã có bảng, người dân hỏi thêm."""
    proc_id = pending["proc_id"]
    picked = pending.get("picked") or {}
    case_ordinal = picked.get(R.AXIS_CASE)
    record = R.build_record(conn, proc_id,
                            int(case_ordinal) if case_ordinal is not None else None)
    if record is None:
        RetrievalPending.clear(inp.conversation_id)
        res.kind = "no_evidence"
        res.text = RT.not_found_text("", inp.question)
        return res

    table = build_table(record, conn=conn,
                        expired=R.is_expired(conn, proc_id), picked=picked)
    res.intent = {"intent": "retrieval_followup",
                  "standalone_question": inp.question, "proc_id": proc_id}

    # Cảm ơn / chào: trả lời CỐ ĐỊNH. Đưa câu "cảm ơn bạn" cho LLM 2 cùng cả
    # bảng thì mô hình 1.5B lan man kể lại bảng (đo được: 6 giây, sai ngữ cảnh).
    if R.is_chitchat(inp.question):
        res.kind = "chitchat"
        res.text = (f"Không có gì ạ! Bạn cần hỏi thêm gì về **{record['name']}** thì cứ hỏi "
                    "nhé. Muốn tra thủ tục khác, bạn mở cuộc trò chuyện mới.")
        dev.event("care_chitchat")
        return res

    # Boundary control: hỏi sang thủ tục KHÁC? CHỈ CẢNH BÁO, KHÔNG CHẶN.
    # Nhóm chốt (2026-09-24): người dân đã được cảnh báo thì câu trả lời vẫn
    # phải hiện — cảnh báo + nút ô chat mới được GẮN SAU câu trả lời (đúng
    # Proposal: "Warning: chúng tôi không chịu trách nhiệm nếu bạn hỏi thủ tục
    # mới và AI trả lời sai trong ô chat này"). Bộ gác khớp theo chữ không dấu
    # nên có báo nhầm ("ngắn hơn" ~ "ngân … hơn"); chặn hẳn thì báo nhầm là mất
    # câu trả lời, gắn thêm thì chỉ thừa một dòng.
    status("Đang kiểm tra câu hỏi…")
    t = time.time()
    other = (not procedure_table.is_rewrite(inp.question)
             and not procedure_table.refers_to_table(table, inp.question)
             and is_new_procedure(conn, inp.question, proc_id))
    dev.event("new_procedure" if other else "boundary_ok",
              ms=lap("understand", t), proc_id=proc_id)

    if not RETRIEVAL_FOLLOWUP_ENABLED:
        res.kind = "answer"
        res.table = table
        res.text = procedure_table.summary_line(table)
        res.intent["answer_source"] = "database"
        return _warn_other(res, record, inp) if other else res

    # "Chắc không?" -> nói đúng nguồn gốc dữ liệu (CODE), không để LLM 2 đoán.
    # Câu hỏi chỉ về MỘT ô (lệ phí, thời gian, giấy tờ…) -> CODE trích nguyên ô.
    previous = next((m.get("content") or "" for m in reversed(inp.history or [])
                     if m.get("role") == "user"), "")
    quoted = (procedure_table.confirm_answer(table, inp.question)
              or procedure_table.field_answer(table, inp.question, previous))
    if quoted:
        res.kind = "answer"
        res.text = quoted
        res.intent["answer_source"] = "database"
        dev.event("care_quote", sections=procedure_table.sections_for(inp.question))
        return _warn_other(res, record, inp) if other else res

    status("Đang trả lời dựa trên bảng thông tin…")
    t = time.time()
    res.text = follow_up(inp.question, inp.history, table)
    res.kind = "answer"
    res.intent["answer_source"] = "database_llm"
    dev.event("follow_up", ms=lap("answer", t), chars=len(res.text),
              sections=procedure_table.sections_for(inp.question))
    return _warn_other(res, record, inp) if other else res


def _warn_other(res: TurnResult, record: dict, inp: TurnInput) -> TurnResult:
    """Gắn cảnh báo "có vẻ là thủ tục khác" + nút ô chat mới SAU câu trả lời."""
    res.text = f"{res.text}\n\n{RT.new_procedure_note(record['name'])}"
    # `question` đi kèm để nút "ô chat mới" tra luôn câu này bằng 🎯.
    res.table = {"kind": "new_procedure", "current": record["name"],
                 "question": inp.question}
    return res


CHAT_FALLBACK = ("Chào bạn! Mình là trợ lý thủ tục hành chính cấp Xã/Phường. Bạn cần làm "
                 "thủ tục gì thì bấm **🎯 Tìm chính xác** để mình tra trong cơ sở dữ liệu nhé.")


def _chat(conn, inp: TurnInput, res: TurnResult, dev, lap,
          status: Callable[[str], None]) -> TurnResult:
    """Tin nhắn thường khi CHƯA có bảng — đúng Proposal slide 3:

        User prompt -> LLM 2 trả lời (bằng hiểu biết chung, KỂ CẢ câu hỏi thủ tục)
                    ║ song song: bộ nhận diện (luật CSDL, không LLM)
                    ╚► có vẻ hỏi thủ tục -> gắn "bạn dùng <Tìm chính xác> nhé" + chip 🎯

    Câu trả lời CÓ THỂ SAI (chưa tra CSDL), nên luôn mang nhãn
    `answer_source = "llm_only"` -> giao diện ghi "⚠️ AI tự trả lời, chưa qua CSDL".
    """
    res.intent = {"intent": "chat", "standalone_question": inp.question,
                  "answer_source": "llm_only"}

    t = time.time()
    guess = R.looks_like_procedure(conn, inp.question)
    dev.event("procedure_detector", ms=lap("understand", t), hit=bool(guess),
              label=(guess or {}).get("label", ""))

    status("Đang soạn trả lời…")
    t = time.time()
    # Chỉ vài lượt gần nhất: đủ để hiểu "cảm ơn" đang cảm ơn gì, không đủ để mô
    # hình nhỏ bị cuốn theo một đoạn hội thoại dài.
    history = [{"role": m["role"], "content": m["content"][:400]}
               for m in (inp.history or [])[-4:]]
    res.text = _llm_text(lambda: llm.chat("chat", RT.CHAT_SYSTEM, inp.question,
                                          history=history), fallback=CHAT_FALLBACK)
    res.kind = "chitchat"
    dev.event("chat", ms=lap("answer", t), chars=len(res.text))

    if guess:
        res.text = f"{res.text}\n\n{RT.EXACT_HINT}"
        # Giao diện vẽ chip "🎯 Tìm chính xác" gửi lại đúng câu này ở mode exact.
        res.table = {"kind": "exact_hint", "question": inp.question}
    return res


def _exact_used(conn, inp: TurnInput, res: TurnResult, dev, pending: dict) -> TurnResult:
    """🎯 lần hai trong cùng ô chat -> mời mở ô chat mới (mang theo câu hỏi) hoặc huỷ."""
    info = R.family_index(conn)["info"].get(pending["proc_id"], {})
    current = info.get("name") or pending["proc_id"]
    res.kind = "clarify"
    res.intent = {"intent": "exact_used", "standalone_question": inp.question,
                  "proc_id": pending["proc_id"]}
    res.text = RT.exact_used_text(current)
    res.table = {"kind": "exact_used", "current": current, "question": inp.question}
    dev.event("exact_used", proc_id=pending["proc_id"])
    return res
