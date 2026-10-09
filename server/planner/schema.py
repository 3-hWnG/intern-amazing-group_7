"""Hợp đồng JSON của Planner. Enum ở đây là NGUỒN DUY NHẤT (prompt + validate đều đọc từ đây)."""

ACTIONS = ["ask_field", "find_procedure", "check_condition", "compare", "provide_info",
           "clarify_reply", "correct_previous", "chitchat", "out_of_scope"]
FIELDS = ["components", "fees", "processing_time", "address", "online", "methods", "files",
          "agency", "steps", "explanation", "meta"]
QUANTITY = ["none", "amount", "duration", "copies", "deadline", "age"]
EVIDENCE = ["none", "source", "legal_basis"]
RELATION = ["independent", "compare", "depends_on"]
MAX_TASKS = 3

FIELD_HELP = {
    "components": "giấy tờ/hồ sơ phải nộp", "fees": "lệ phí/phí", "processing_time": "thời hạn giải quyết",
    "address": "nộp ở đâu", "online": "nộp trực tuyến", "methods": "hình thức nộp",
    "files": "biểu mẫu/tờ khai tải về", "agency": "cơ quan giải quyết", "steps": "các bước/quy trình",
    "explanation": "là gì/điều kiện/đối tượng", "meta": "căn cứ pháp lý/văn bản/quyết định",
}

# JSON schema truyền vào Ollama `format` (ràng buộc giải mã). Khoá ngắn để bớt token đầu ra.
PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "tasks": {
            "type": "array", "maxItems": MAX_TASKS,
            "items": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ACTIONS},
                    "cand": {"type": "integer"},          # chỉ số ứng viên; -1 = không có; -2 = thủ tục đang nói (last)
                    "fields": {"type": "array", "items": {"type": "string", "enum": FIELDS}},
                    "quantity": {"type": "string", "enum": QUANTITY},
                    "conditions": {"type": "array", "items": {"type": "string"}},
                    "facts": {"type": "array", "items": {"type": "string"}},
                    "evidence": {"type": "string", "enum": EVIDENCE},
                    "relation": {"type": "string", "enum": RELATION},
                },
                "required": ["action", "cand", "fields"],
            },
        },
        "clarify": {"type": "boolean"},
    },
    "required": ["tasks", "clarify"],
}

# Phase 19 (hybrid): bản GỌN của hợp đồng + `confidence` (0..1, cả kế hoạch). Merge chỉ dùng action/cand/fields nên bỏ quantity/conditions/facts/evidence/relation/clarify
# (tiết kiệm token: 220 token ~ 4-5 s trên GTX 1660 Super; bản đầy đủ bị cắt cụt JSON ở câu 2-3 ý). Không đụng PLAN_SCHEMA của nhánh LLM cũ.
# ponytail: LLM không đề xuất conditions/relation (luật đã làm; Policy kiểm căn cứ) ; thêm lại khi cần LLM tách điều kiện tốt hơn luật.
HYBRID_SCHEMA = {
    "type": "object",
    "properties": {
        "tasks": {"type": "array", "maxItems": MAX_TASKS, "items": {
            "type": "object",
            "properties": {"action": {"type": "string", "enum": ACTIONS}, "cand": {"type": "integer"},
                           "fields": {"type": "array", "items": {"type": "string", "enum": FIELDS}}},
            "required": ["action", "cand", "fields"]}},
        "confidence": {"type": "number"},
    },
    "required": ["tasks", "confidence"],
}
