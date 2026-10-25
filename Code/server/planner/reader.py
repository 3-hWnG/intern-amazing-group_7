"""Phương án C của đợt sửa câu khó (24/10/2026): model 4B ĐỌC câu của người dân và phân loại ý định + gọi tên thủ tục bằng chữ;
luật và DB vẫn chọn thủ tục (model không bao giờ ghi mã thủ tục) và Policy vẫn quyết định trả lời / từ chối.

    intent: thu_tuc | tinh_trang | khieu_nai | luat | noi_bo | khac      procedure: tên thủ tục ngắn (chữ) hoặc ""

Cách dùng kết quả (planner.plan): intent khác "thu_tuc" -> Plan.intent (Policy từ chối kèm lý do); intent "thu_tuc" có tên thủ tục ->
xếp hạng TÊN đó bằng bộ xếp hạng luật trên cùng kho; tên khớp chắc mà luật trên cả câu chọn thủ tục khác (không nằm trong 3 thủ tục
đầu của tên) -> đổi sang thủ tục của tên. Lỗi / quá hạn -> giữ kế hoạch luật.
Bật: S3_READER=1. Model: S3_READER_MODEL (mặc định LLM_MODEL = qwen3:4b-instruct). S3_READER_CACHE=<tệp jsonl>: ghi / phát lại kết quả
(đo nhiều lần trên dev không gọi lại model, máy đỡ nóng).
"""
from __future__ import annotations

import hashlib
import json
import os
import threading

INTENTS = ("thu_tuc", "tinh_trang", "khieu_nai", "luat", "noi_bo", "khac")
REASON = {"tinh_trang": "status", "khieu_nai": "complaint", "luat": "legal", "noi_bo": "internal", "khac": "off_topic"}
SCHEMA = {"type": "object", "properties": {"intent": {"type": "string", "enum": list(INTENTS)}, "procedure": {"type": "string"}},
          "required": ["intent", "procedure"]}
SYSTEM = """Bạn đọc câu hỏi người dân gửi bộ phận một cửa và PHÂN LOẠI câu hỏi. Không trả lời câu hỏi. Trả JSON {"intent", "procedure"}.
intent:
- "thu_tuc": người hỏi muốn biết cách làm, giấy tờ, nơi nộp, thời gian, lệ phí hoặc điều kiện của một thủ tục hành chính (kể cả khi kể hoàn cảnh dài).
- "tinh_trang": hỏi hồ sơ CỦA CHÍNH MÌNH đã nộp đang ở đâu, bao giờ nhận, bị lỗi gì, đã có kết quả chưa.
- "khieu_nai": phản ánh, khiếu nại, tố cáo, kiến nghị, đề nghị cơ quan xem xét giải quyết, góp ý chính sách.
- "luat": hỏi quy định pháp luật, xử phạt, vi phạm, quyền và nghĩa vụ, giải thích luật, mà không hỏi cách làm thủ tục.
- "noi_bo": chế độ, lương, phụ cấp, tuyển sinh, tuyển dụng, nghỉ hưu của cán bộ, chiến sĩ trong ngành Công an, quân đội.
- "khac": không phải câu hỏi về thủ tục hành chính.
procedure: khi intent là "thu_tuc", ghi tên thủ tục ngắn gọn theo cách gọi chính thức hiện nay (ví dụ "cấp lại thẻ căn cước", "đăng ký thường trú",
"đăng ký tạm trú", "đăng ký khai sinh", "cấp bản sao trích lục hộ tịch", "chứng thực bản sao", "đăng ký xe", "cấp giấy chứng nhận quyền sử dụng đất").
Các trường hợp khác để "".
Ví dụ:
"Mình mất thẻ căn cước rồi, làm lại thì cần mang gì?" -> {"intent": "thu_tuc", "procedure": "cấp lại thẻ căn cước"}
"Hồ sơ đăng ký kết hôn em nộp tuần trước sao giờ chưa thấy báo kết quả?" -> {"intent": "tinh_trang", "procedure": ""}
"Cán bộ phường hướng dẫn sai làm tôi phải đi lại nhiều lần, đề nghị xem xét." -> {"intent": "khieu_nai", "procedure": ""}
"Đi xe máy không đội mũ bảo hiểm bị phạt bao nhiêu tiền?" -> {"intent": "luat", "procedure": ""}
"Chiến sĩ nghĩa vụ công an khi xuất ngũ được hưởng chế độ gì?" -> {"intent": "noi_bo", "procedure": ""}
"Cho tôi hỏi giá vàng hôm nay." -> {"intent": "khac", "procedure": ""}"""
_lock = threading.Lock()
_cache: dict | None = None


def enabled() -> bool:
    return os.environ.get("S3_READER", "0") == "1"


def _cache_path() -> str | None:
    return os.environ.get("S3_READER_CACHE") or None


def _load_cache() -> dict:
    global _cache
    if _cache is None:
        _cache = {}
        p = _cache_path()
        if p and os.path.exists(p):
            for line in open(p, encoding="utf-8"):
                try:
                    d = json.loads(line)
                    _cache[d["key"]] = d["out"]
                except (ValueError, KeyError):
                    pass
    return _cache


def read(question: str, llm_chat_json=None) -> dict | None:
    """-> {"intent", "procedure"} hoặc None (lỗi / quá hạn / JSON hỏng)."""
    model = os.environ.get("S3_READER_MODEL") or None
    key = hashlib.sha1(f"{model}|{question}".encode("utf-8")).hexdigest()
    with _lock:
        c = _load_cache()
        if key in c:
            return c[key]
    if llm_chat_json is None:
        from core.llm import chat_json as llm_chat_json
    try:
        raw = llm_chat_json(SYSTEM, question[:1800], schema=SCHEMA, think=False, timeout=float(os.environ.get("S3_READER_TIMEOUT", "20")),
                            num_predict=60, model=model)
    except Exception:
        return None
    if not isinstance(raw, dict) or raw.get("intent") not in INTENTS:
        return None
    out = {"intent": raw["intent"], "procedure": str(raw.get("procedure") or "")[:120]}
    with _lock:
        c[key] = out
        p = _cache_path()
        if p:
            with open(p, "a", encoding="utf-8") as f:
                f.write(json.dumps({"key": key, "q": question[:200], "out": out}, ensure_ascii=False) + "\n")
    return out
