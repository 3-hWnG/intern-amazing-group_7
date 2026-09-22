"""HỆ THỐNG 2 — RETRIEVAL (CSDL thủ tục nội bộ). Hệ thống MẶC ĐỊNH.

Chạy song song Hệ thống 1 (`system_websearch.py`): cùng nhận `TurnInput`, cùng
trả `TurnResult`, người dùng chọn bằng nút "Web search". Sơ đồ đầy đủ +
các quyết định thiết kế: Documentation/PHASE2_RETRIEVAL.md.

    [ Người dân hỏi ]  "t người bình định muốn dk kết hôn"
          │
          ▼
    [ LLM 1: rút khoá ]  -> {"primary_keyword": "đăng ký kết hôn",
          │                  "domain": "Hộ tịch", "entities": ["Bình Định"]}
          │  CHỈ hiểu câu hỏi. Không sinh câu trả lời. `domain` phải CHỌN trong
          │  103 lĩnh vực có thật -> mô hình 1.5B không trỏ được vào thứ không có.
          ▼
    [ Tra CSDL — không qua LLM ]  FTS5 ba tầng, mỗi kết quả kèm `confident`
          │
          ├─ 0 kết quả  -> LLM 1 sinh lại khoá (tối đa 3 lượt) -> vẫn không có:
          │                xin lỗi, NÊU RÕ khoá đã tìm + câu hỏi gốc (để debug được)
          │
          ├─ nhiều ứng viên / còn phân nhánh -> HỎI MCQ (tối đa 2 vòng)
          │                trạng thái nằm ở app.db (`retrieval_pending`), vì một
          │                lượt HTTP không giữ được trạng thái giữa các vòng
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
import sqlite3
import time
from typing import Callable

import developer_mode
from config import (PROCEDURES_DB_PATH, RETRIEVAL_ENABLED,
                    RETRIEVAL_FOLLOWUP_ENABLED, RETRIEVAL_MAX_KEY_ATTEMPTS,
                    RETRIEVAL_MAX_MCQ_ROUNDS, SYSTEM_RETRIEVAL)
from core import llm, procedure_table
from core.turn import TurnInput, TurnResult
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
        # Bảng rỗng cũng coi như chưa có CSDL: đỡ trả lời "không tìm thấy" 1.407 lần.
        if R.count_active(conn) == 0:
            conn.close()
            return None
    except Exception:
        return None
    _local.conn = conn
    return conn


def _domains(conn: sqlite3.Connection, limit: int = 103) -> list[str]:
    """Danh sách lĩnh vực THẬT để LLM 1 chọn. Lấy từ CSDL, không hardcode."""
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

    # Tỉnh trong hồ sơ người dùng là ngữ cảnh phụ, KHÔNG phải bộ lọc:
    # 100% bản ghi có province = NULL nên không có gì để lọc theo.
    if profile.get("province") and profile["province"] not in entities:
        entities.append(profile["province"])

    return {"primary_keyword": keyword, "domain": domain, "entities": entities[:5]}


# ---------------------------------------------------------------------------
# 2. Truy vấn CSDL — KHÔNG qua LLM
# ---------------------------------------------------------------------------
def lookup(keys: dict, conn: sqlite3.Connection | None = None,
           limit: int = 8) -> list[dict]:
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


def _rank_by_entities(hits: list[dict], entities: list[str], conn) -> list[dict]:
    """Xếp lại ứng viên theo các chi tiết phụ người dân có nhắc.

    Chỉ CỘNG ĐIỂM, không loại bỏ: "Bình Định" không lọc được theo tỉnh (cột
    province rỗng toàn bộ) nhưng "có yếu tố nước ngoài" hay "lưu động" thì nằm
    ngay trong TÊN thủ tục — dùng được.
    """
    if not entities:
        return hits
    from Database.pipeline.textutil import fold
    folded = [fold(e) for e in entities]

    def bonus(h: dict) -> int:
        hay = fold(f"{h['name']} {h.get('domain', '')}")
        return sum(1 for e in folded if e and e in hay)

    return sorted(hits, key=lambda h: (-bonus(h), h["score"]))


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
    """Hỏi tiếp sau khi đã có bảng: trả lời CHỈ trong phạm vi bảng."""
    text = procedure_table.to_text(table)
    return llm.chat("answer", RT.CARE_SYSTEM, RT.care_user(question, text),
                    history=None).strip()


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

        # ── A. Đang chờ người dùng trả lời MCQ? ─────────────────────────
        if pending and pending.get("axis"):
            picked_value = _match_answer(inp.question, pending["options"])
            if picked_value is not None:
                dev.event("mcq_answer", axis=pending["axis"], value=str(picked_value))
                return _resolve(conn, inp, res, dev, lap, pending, picked_value, status)
            # Không khớp lựa chọn nào -> coi như câu hỏi MỚI, bỏ vòng MCQ cũ.
            dev.event("mcq_abandoned", question=inp.question[:120])
            RetrievalPending.clear(conv_id)
            pending = None

        # ── B. Đã có bảng rồi -> chế độ chăm sóc khách hàng (LLM 2) ─────
        if pending and pending.get("proc_id") and not pending.get("axis"):
            return _care(conn, inp, res, dev, lap, pending, status)

        # ── C. Câu hỏi mới: LLM 1 -> tra CSDL ───────────────────────────
        status("Đang xác định thủ tục bạn cần…")
        domains = _domains(conn)
        hits, keys, tried, best_keys = [], {}, [], {}

        # Dừng khi có kết quả CHẮC CHẮN, không phải khi có kết quả bất kỳ:
        # tầng 3 của FTS là OR nên gần như luôn moi ra thứ gì đó. Kết quả
        # không chắc vẫn giữ lại làm phương án cuối, nhưng thử diễn đạt khác
        # trước đã — sinh lại một lần rẻ hơn nhiều so với hỏi người dân.
        for attempt in range(1, RETRIEVAL_MAX_KEY_ATTEMPTS + 1):
            t = time.time()
            k = extract_keys(inp.question, inp.history, inp.profile, domains,
                             tried if attempt > 1 else None)
            dev.event("extract_keys", ms=lap("understand", t), attempt=attempt, **k)

            t = time.time()
            h = lookup(k, conn)
            confident = any(x.get("confident") for x in h)
            dev.event("lookup", ms=lap("search", t), attempt=attempt, n_hits=len(h),
                      confident=confident, keyword=k["primary_keyword"])

            if h and not hits:                 # giữ phương án cuối đầu tiên tìm được
                hits, best_keys = h, k
            if confident:
                hits, best_keys = h, k
                break
            tried.append(k["primary_keyword"])
            if attempt < RETRIEVAL_MAX_KEY_ATTEMPTS:
                status(f"Chưa chắc — đang thử cách diễn đạt khác ({attempt}/{RETRIEVAL_MAX_KEY_ATTEMPTS})…")

        keys = best_keys or k
        res.intent = {"intent": "retrieval", "standalone_question": inp.question, **keys}

        # Không ra gì cả -> xin lỗi, NÊU RÕ khoá đã tìm + câu hỏi gốc.
        if not hits:
            res.kind = "no_evidence"
            res.text = RT.not_found_text(" / ".join(dict.fromkeys(tried)), inp.question)
            dev.event("not_found", tried=tried)
            if conv_id:
                RetrievalPending.clear(conv_id)
            return res

        hits = _rank_by_entities(hits, keys.get("entities", []), conn)
        low_conf = not any(x.get("confident") for x in hits)
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
    """Có ứng viên rồi: hỏi MCQ tiếp, hay dựng bảng luôn?"""
    picked = dict(picked or {})
    conv_id = inp.conversation_id

    # Còn nhiều thủ tục khác nhau -> phải hỏi "thủ tục nào" TRƯỚC mọi trục khác.
    # Không ứng viên nào chắc chắn -> vẫn hỏi, kèm lối thoát "không cái nào đúng".
    proc_axes = R.axes_for_candidates(hits, low_confidence)
    if proc_axes and rounds < RETRIEVAL_MAX_MCQ_ROUNDS and R.AXIS_PROCEDURE not in picked:
        axis = proc_axes[0]
        if conv_id:
            RetrievalPending.save(
                conv_id, question=inp.question, keys=keys,
                candidates=[{"proc_id": h["proc_id"], "name": h["name"],
                             "domain": h.get("domain", "")} for h in hits],
                axis=axis["axis"], options=axis["options"], picked=picked,
                rounds=rounds + 1)
        _mcq_result(res, axis)
        dev.event("mcq_ask", axis=axis["axis"], n_options=len(axis["options"]))
        return res

    proc_id = picked.get(R.AXIS_PROCEDURE) or hits[0]["proc_id"]
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

    # Chưa chốt thủ tục nào (không nên xảy ra) -> tra lại từ ứng viên đã lưu.
    hits = pending.get("candidates") or []
    if not hits:
        res.kind = "no_evidence"
        res.text = RT.not_found_text(keys.get("primary_keyword", ""), original.question)
        return res
    return _deliver(conn, original, res, dev, lap, keys, hits[0]["proc_id"],
                    picked, memory, status, rounds, hits)


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

    # Boundary control: hỏi sang thủ tục KHÁC -> mời mở ô chat mới.
    status("Đang kiểm tra câu hỏi…")
    t = time.time()
    if is_new_procedure(conn, inp.question, proc_id):
        res.kind = "clarify"
        res.text = RT.NEW_PROCEDURE_TEXT
        res.table = {"kind": "new_procedure", "current": record["name"]}
        dev.event("new_procedure", ms=lap("understand", t), proc_id=proc_id)
        return res
    dev.event("boundary_ok", ms=lap("understand", t))

    if not RETRIEVAL_FOLLOWUP_ENABLED:
        res.kind = "answer"
        res.table = table
        res.text = procedure_table.summary_line(table)
        return res

    status("Đang trả lời dựa trên bảng thông tin…")
    t = time.time()
    res.text = follow_up(inp.question, inp.history, table)
    res.kind = "answer"
    dev.event("follow_up", ms=lap("answer", t), chars=len(res.text))
    return res
