"""Tắt các cài đặt NV5 cho test NV1–NV3: các test đó kiểm hành vi gốc (lời dặn, khuôn JSON "answer"…).
Từ NV5 mặc định đã BẬT (cấu hình thắng bộ đo); tính năng NV5 được kiểm riêng ở test_nv5.py."""
OFF = {"PROMPT_CACHE_ORDER": False, "JSON_PLAN_FIRST": False, "GREETING_MODE": "off", "GROUNDING_CHECK": "off",
       "AMBIGUITY_CHECK": False, "TABLE_TOOL": False, "STRICT_BUSINESS_FACTS": False, "SEARCH_FOLLOWUP": False,
       "RERANK_RESCUE": False, "KEEP_MODELS_LOADED": False}


def apply():
    from system3.system4.server import settings
    settings.save(OFF)
