"""Phase 11: LLM có kiểm soát cho so sánh / giải thích điều kiện.
LLM chỉ nhận các đoạn dữ liệu đã trích (id d1..dn) và trả {points:[{text,cites}]}; code bỏ mọi ý không có cites hợp lệ
hoặc vi phạm verify_point. Lỗi/timeout/hết ý -> trả [] để người gọi dùng bản bằng code (không bao giờ làm hỏng câu trả lời)."""
from __future__ import annotations

from .verifier import verify_point

TIMEOUT = 5.0   # ponytail: hạ từ 20 s; quá hạn thì giữ câu trả lời bằng code
MAX_PASSAGE = 700
MAX_POINTS = 6
SCHEMA = {"type": "object", "required": ["points"], "properties": {"points": {"type": "array", "items": {
    "type": "object", "required": ["text", "cites"],
    "properties": {"text": {"type": "string"}, "cites": {"type": "array", "items": {"type": "string"}}}}}}}
SYSTEM = ("Bạn là trợ lý thủ tục hành chính. CHỈ dùng các đoạn dữ liệu [d1], [d2]... dưới đây, tuyệt đối không thêm kiến thức ngoài. "
          "Trả JSON {\"points\":[{\"text\":\"...\",\"cites\":[\"d1\"]}]}: mỗi ý ngắn gọn, một hai câu, kèm id đoạn làm căn cứ. "
          "Chỉ nêu số tiền, ngày, thời hạn, tên văn bản có trong đoạn đã trích. Không có dữ liệu thì không nêu; không được nói 'miễn phí' "
          "nếu đoạn dữ liệu không nói. Không nêu ý nào không có đoạn làm căn cứ.")


def compose(llm, passages: list[dict], request: str, question: str = "", issues: list | None = None) -> list[dict]:
    """passages: [{label, text}] -> [{text, cites:[label...]}] đã kiểm. issues (tuỳ chọn) nhận lý do bỏ ý."""
    issues = issues if issues is not None else []
    passages = [{"label": p["label"], "text": p["text"][:MAX_PASSAGE]} for p in passages if p["text"].strip()]
    if llm is None or not passages:
        return []
    ids = {f"d{i}": p for i, p in enumerate(passages, 1)}
    user = "\n".join(f"[{i}] ({p['label']}) {p['text']}" for i, p in ids.items()) + f"\n\nYêu cầu: {request}\nCâu hỏi: {question}"
    try:
        raw = llm(SYSTEM, user, schema=SCHEMA, timeout=TIMEOUT)
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
