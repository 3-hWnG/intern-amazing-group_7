"""Hồ sơ lĩnh vực v1 (G4.3, P29, D14): mỗi lĩnh vực tự chọn cách trả lời. Lưu ở cột JSON `domains.profile` (chỉ các mục đã đổi);
giá trị mặc định tính theo loại lĩnh vực. Model vẫn là cấu hình chung của cả hệ (⚙).

  answer_mode      "free"     : có bộ dữ liệu đang bật thì trả lời từ dữ liệu, không có thì AI chung (hành vi trước G4.3; mặc định lĩnh vực mềm)
                   "grounded" : CHỈ trả lời từ dữ liệu; không có dữ liệu / không tìm thấy thì nói không có (mặc định lĩnh vực cứng, D14)
                   "verbatim" : không gọi AI — code trích nguyên các đoạn tìm được kèm nguồn
  require_citation câu trả lời từ dữ liệu phải ghi số đoạn [n]; thiếu thì AI viết lại một lần (mặc định: lĩnh vực cứng)
  clarify          AI được hỏi lại khi câu chưa rõ (tắt: trả lời luôn với thông tin đang có)
  retrieval        {"top_k": 1–20, "rerank": bool} — đổi tạm số đoạn / xếp hạng lại cho lĩnh vực này (trống = theo ⚙)
  tools            ["table"]: công cụ bảng (vẫn cần ⚙ TABLE_TOOL bật)
  persona          vai trò riêng của lĩnh vực, thêm vào lời dặn
  web_allowed      cho dùng nút "Tìm web" trong lĩnh vực này
  code_answer      (chỉ ABI) trả lời bằng code khi hiểu trọn câu hỏi; mặc định lấy ⚙ ABI_CODE_ANSWER (giữ hành vi cũ)
Guardrail của lĩnh vực vẫn ở cột `domains.guardrail` (sửa ở ô Guardrail như trước)."""
from __future__ import annotations

import json

from . import settings

MODES = ("free", "grounded", "verbatim")
KEYS = ("answer_mode", "require_citation", "clarify", "retrieval", "tools", "persona", "web_allowed", "code_answer")


def defaults(d: dict) -> dict:
    hard = d.get("kind") == "hard"
    p = {"answer_mode": "grounded" if hard else "free", "require_citation": hard, "clarify": True, "retrieval": {},
         "tools": ["table"], "persona": "", "web_allowed": True}
    if d.get("engine") == "abi":
        p["code_answer"] = bool(settings.get("ABI_CODE_ANSWER"))
    return p


def stored(d: dict) -> dict:
    try:
        v = json.loads(d.get("profile") or "{}")
        return v if isinstance(v, dict) else {}
    except ValueError:
        return {}


def get(d: dict) -> dict:
    return {**defaults(d), **{k: v for k, v in stored(d).items() if k in KEYS}}


def validate(p: dict, d: dict) -> dict:
    """Kiểm và chuẩn hoá phần profile gửi lên (chỉ các khoá đã biết). Sai -> ValueError (thông báo tiếng Việt)."""
    if not isinstance(p, dict):
        raise ValueError("profile phải là một đối tượng JSON")
    bad = [k for k in p if k not in KEYS]
    if bad:
        raise ValueError(f"không có mục {', '.join(bad)} (có: {', '.join(KEYS)})")
    out = {}
    for k, v in p.items():
        if k == "answer_mode":
            if v not in MODES:
                raise ValueError(f"answer_mode phải là một trong {', '.join(MODES)}")
        elif k in ("require_citation", "clarify", "web_allowed", "code_answer"):
            if not isinstance(v, bool):
                raise ValueError(f"{k} phải là true/false")
            if k == "code_answer" and d.get("engine") != "abi":
                raise ValueError("code_answer chỉ dùng cho lĩnh vực ABI")
        elif k == "retrieval":
            if not isinstance(v, dict) or any(x not in ("top_k", "rerank") for x in v):
                raise ValueError('retrieval phải dạng {"top_k": số, "rerank": true/false}')
            if "top_k" in v and not (isinstance(v["top_k"], int) and 1 <= v["top_k"] <= 20):
                raise ValueError("retrieval.top_k phải từ 1 đến 20")
            if "rerank" in v and not isinstance(v["rerank"], bool):
                raise ValueError("retrieval.rerank phải là true/false")
        elif k == "tools":
            if not isinstance(v, list) or any(x not in ("table",) for x in v):
                raise ValueError('tools chỉ gồm "table"')
        elif k == "persona":
            if not isinstance(v, str) or len(v) > 1000:
                raise ValueError("persona là chữ, tối đa 1000 ký tự")
            v = v.strip()
        out[k] = v
    return out


def search_overrides(p: dict) -> dict | None:
    r = p.get("retrieval") or {}
    o = {}
    if "top_k" in r:
        o["RETRIEVAL_TOP_K"] = r["top_k"]
    if "rerank" in r:
        o["RERANKER_ENABLED"] = r["rerank"]
    return o or None


NO_CLARIFY = ("Trong lĩnh vực này KHÔNG hỏi lại người dùng: trả lời tốt nhất có thể với thông tin đang có và nói rõ còn thiếu thông tin gì "
              '("ask_back" = false, "choices" rỗng).')
CITE = "Mỗi ý lấy từ dữ liệu PHẢI ghi số đoạn [n] ngay sau ý đó; câu trả lời không có số đoạn nào sẽ bị viết lại."
CITE_RETRY = "Câu trả lời trước KHÔNG ghi số đoạn nguồn. Viết lại, ghi [n] ngay sau mỗi ý lấy từ dữ liệu."


def verbatim(evidence: list[dict], chars: int) -> str:
    """answer_mode=verbatim: code trích nguyên các đoạn tìm được (không gọi AI)."""
    if not evidence:
        return "Mình không tìm thấy đoạn dữ liệu nào liên quan đến câu hỏi này trong lĩnh vực này."
    parts = [f"**[{i}] {e['title']}**\n{(e['text'] if e.get('full') else e['text'][:chars]).strip()}" for i, e in enumerate(evidence, 1)]
    return "Các đoạn dữ liệu liên quan nhất (trích nguyên văn):\n\n" + "\n\n".join(parts)
