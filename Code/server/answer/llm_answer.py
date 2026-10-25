"""Phase 11: LLM có kiểm soát cho so sánh / giải thích điều kiện.
LLM chỉ nhận các đoạn dữ liệu đã trích (id d1..dn) và trả {points:[{text,cites}]}; code bỏ mọi ý không có cites hợp lệ
hoặc vi phạm verify_point. Lỗi/timeout/hết ý -> trả [] để người gọi dùng bản bằng code (không bao giờ làm hỏng câu trả lời)."""
from __future__ import annotations

from .verifier import verify_point

from config import ANSWER_LLM_TIMEOUT as TIMEOUT, ANSWER_LLM_NUM_PREDICT as NUM_PREDICT, ANSWER_LLM_PASSAGE_CHARS, ANSWER_LLM_TURN_BUDGET   # 7.0 s mặc định (trước P24: 5.0 s cứng trong file này); ANSWER_LLM_TIMEOUT đổi được
MAX_PASSAGE = ANSWER_LLM_PASSAGE_CHARS
MAX_POINTS = 6
SCHEMA = {"type": "object", "required": ["points"], "properties": {"points": {"type": "array", "items": {
    "type": "object", "required": ["text", "cites"],
    "properties": {"text": {"type": "string"}, "cites": {"type": "array", "items": {"type": "string"}}}}}}}
SYSTEM = ("Trợ lý thủ tục hành chính. CHỈ dùng các đoạn [d1], [d2]... bên dưới, không thêm kiến thức ngoài. "
          "Trả JSON {\"points\":[{\"text\":\"...\",\"cites\":[\"d1\"]}]}: tối đa 3 ý, mỗi ý MỘT câu ngắn (dưới 30 từ), kèm id đoạn căn cứ. "
          "Chỉ nêu số tiền, ngày, thời hạn, tên văn bản có trong đoạn; không nói 'miễn phí' nếu đoạn không nói.")   # Phase 27: rút ngắn (trước: 3 ý/2 câu không giới hạn, dài gấp đôi), xem P27_REPORT


_ready_at = [0.0, 0.0]      # [lần cuối thấy model đã nạp, lần cuối kích hoạt nạp nền]


def _ready(llm) -> bool:
    """Phase 27: model Ollama chưa nạp (nguội: máy rảnh > LLM_KEEP_ALIVE, bị đẩy khỏi GPU, Ollama vừa tắt) thì KHÔNG đợi hết timeout 7 s rồi mới rơi về bản code:
    trả lời ngay bằng code và nạp model ở nền cho lượt sau (đo: lượt nguội timeout 2/2). Chỉ áp cho client thật (core.llm); LLM giả của test luôn 'sẵn sàng'.
    ponytail: dò /api/ps mỗi 5 s; model đang nạp dở coi như chưa sẵn sàng."""
    if getattr(llm, "__module__", "") != "core.llm":
        return True
    import threading, time
    from core.llm import loaded_models, model_name, warm_up
    now = time.monotonic()
    if now - _ready_at[0] < 5.0:
        return True
    if model_name() in loaded_models():
        _ready_at[0] = now
        return True
    if now - _ready_at[1] > 30.0:
        _ready_at[1] = now
        threading.Thread(target=warm_up, daemon=True).start()
    return False


def budgeted(llm, total: float = ANSWER_LLM_TURN_BUDGET):
    """Bọc llm cho MỘT lượt: tổng thời gian chờ LLM <= total giây (mỗi lần gọi chỉ được phần còn lại, dưới 1 s thì không gọi). None -> None.
    Một lượt có thể gọi LLM nhiều lần (điều kiện từng task + so sánh); không có trần chung thì 3 lần x 7 s = 21 s."""
    if llm is None:
        return None
    import time
    end = time.monotonic() + total

    def call(system, user, **kw):
        left = end - time.monotonic()
        if left < 1.0:
            raise TimeoutError("hết ngân sách thời gian LLM của lượt")
        kw["timeout"] = min(kw.get("timeout") or left, left)
        return llm(system, user, **kw)
    call.__module__ = getattr(llm, "__module__", "")      # _ready() vẫn nhận ra client thật
    return call


def compose(llm, passages: list[dict], request: str, question: str = "", issues: list | None = None) -> list[dict]:
    """passages: [{label, text}] -> [{text, cites:[label...]}] đã kiểm. issues (tuỳ chọn) nhận lý do bỏ ý."""
    issues = issues if issues is not None else []
    passages = [{"label": p["label"], "text": p["text"][:MAX_PASSAGE]} for p in passages if p["text"].strip()]
    if llm is None or not passages:
        return []
    if not _ready(llm):
        issues.append("llm chưa nạp, dùng bản bằng code")
        return []
    ids = {f"d{i}": p for i, p in enumerate(passages, 1)}
    user = "\n".join(f"[{i}] ({p['label']}) {p['text']}" for i, p in ids.items()) + f"\n\nYêu cầu: {request}\nCâu hỏi: {question}"
    try:
        raw = llm(SYSTEM, user, schema=SCHEMA, timeout=TIMEOUT, **({"num_predict": NUM_PREDICT} if NUM_PREDICT else {}))
        pts = raw.get("points") if isinstance(raw, dict) else None
        if not isinstance(pts, list):
            raise ValueError("không có points")
    except Exception as e:                                   # LLMError, timeout, JSON hỏng...
        issues.append(f"llm lỗi, dùng bản bằng code: {type(e).__name__}")
        return []
    out = []
    for p in pts[:MAX_POINTS]:
        text = p.get("text") if isinstance(p, dict) else None
        cites = p.get("cites") if isinstance(p, dict) else None
        if not isinstance(text, str) or not text.strip() or not isinstance(cites, list):
            issues.append("bỏ ý: sai định dạng")
            continue
        cites = [c.strip("[] ") for c in cites if isinstance(c, str)]
        if not cites or any(c not in ids for c in cites):
            issues.append(f"bỏ ý không có cites hợp lệ: {text[:60]}")
            continue
        bad = verify_point(text, " ".join(ids[c]["text"] + " " + ids[c]["label"] for c in cites), question)
        if bad:
            issues.append(f"bỏ ý ({bad[0]}): {text[:60]}")
            continue
        out.append({"text": text.strip(), "cites": sorted({ids[c]["label"] for c in cites})})
    return out


def render(points: list[dict]) -> str:
    return "\n".join(f"- {p['text']} (theo: {'; '.join(p['cites'])})" for p in points)
