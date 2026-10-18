"""Dùng lại câu trả lời đã được 👍 (quyết định của trưởng nhóm 18/10, sau G3.4): người khác hỏi Y CHANG thì trả ngay,
không xếp hàng GPU, không gọi model. Câu hỏi được hỏi nhiều sẽ nhanh dần.

Chỉ dùng lại khi câu trả lời KHÔNG phụ thuộc người hỏi (eligible):
  - câu đầu tiên của hội thoại (không có ngữ cảnh trước), không phải lượt tạo lại (↻ = muốn AI viết lại);
  - AI chung: không dùng bộ dữ liệu riêng, không tìm web, không phải lĩnh vực ABI (dữ liệu theo ngày);
  - lời dặn không có điều nhớ / tóm tắt của người dùng; câu hỏi tiếng Việt, không chứa CCCD/SĐT, không phải "hãy nhớ/quên…".
Khoá = câu hỏi chuẩn hoá (chữ thường, gộp khoảng trắng, bỏ dấu câu cuối; GIỮ dấu tiếng Việt) + lĩnh vực + dấu cài đặt
(model, tên/giới thiệu doanh nghiệp, guardrail, guardrail của lĩnh vực): đổi cài đặt thì câu cũ không được dùng.
Có người 👎 bản dùng lại -> câu gốc thôi được phục vụ. Hết hạn sau ANSWER_CACHE_DAYS ngày. Công tắc: ANSWER_CACHE trong ⚙."""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata

from . import db, memory, settings
from .db import mask_pii

_TRAIL = re.compile(r"[\s?.!…,;:]+$")


def qkey(text: str) -> str:
    t = unicodedata.normalize("NFC", text or "").lower()
    return _TRAIL.sub("", re.sub(r"\s+", " ", t).strip())


def fingerprint(dom: dict) -> str:
    parts = [settings.get("FRIENDLY_MODEL"), settings.get("BUSINESS_NAME"), settings.get("BUSINESS_DESCRIPTION"),
             settings.get("STRICT_BUSINESS_FACTS"), settings.get("GUARDRAILS"), dom.get("guardrail") or ""]
    return hashlib.sha256(json.dumps(parts, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()[:16]


def eligible(text: str, history_path: list, evidence, web: bool, abi_mode: bool, info: dict) -> bool:
    if history_path or web or abi_mode or evidence is not None:
        return False
    if info.get("memories") or info.get("summary") or info.get("foreign") or info.get("block"):
        return False
    if mask_pii(text) != text or any(memory.triggers(text)):
        return False
    return bool(qkey(text))


def lookup(text: str, dom: dict) -> dict | None:
    """Câu trả lời 👍 còn dùng được cho câu hỏi này, hoặc None. Bản dùng lại cũng được 👍/👎: gốc = context.cached_from."""
    if not settings.get("ANSWER_CACHE"):
        return None
    rows = db.run("SELECT msg_key, answer, context, value FROM feedback_log WHERE engine='friendly' AND qkey=? AND domain_id=? "
                  "AND created_at >= datetime('now', ?) ORDER BY created_at DESC",
                  (qkey(text), dom["id"], f"-{int(settings.get('ANSWER_CACHE_DAYS'))} days"), many=True)
    fp, blocked, good = fingerprint(dom), set(), []
    for r in rows:
        ctx = json.loads(r["context"] or "{}")
        root = ctx.get("cached_from") or r["msg_key"]
        if r["value"] < 0:
            blocked.add(root)
        elif ctx.get("cache_fp") == fp and r["answer"].strip():
            good.append((root, r, ctx))
    for root, r, ctx in good:
        if root not in blocked:
            return {"from": root, "answer": r["answer"], "choices": ctx.get("choices") or []}
    return None


def like_context(meta: dict) -> dict:
    """Phần context ghi kèm 👍/👎 để lookup dùng (chỉ khi câu trả lời eligible lúc sinh ra)."""
    if not meta.get("cacheable"):
        return {}
    out = {"cache_fp": meta.get("cache_fp"), "choices": meta.get("choices") or []}
    if (meta.get("cached") or {}).get("from"):
        out["cached_from"] = meta["cached"]["from"]
    return out
