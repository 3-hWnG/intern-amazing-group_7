"""Một lượt hỏi trong lĩnh vực ABI — server/chat.py gọi prepare() thay cho bước "tìm trong bộ dữ liệu" của Friendly.

Dữ liệu = phiên bản ĐANG DÙNG (abi.com.vn hoặc staging, chọn trong Quản lý lĩnh vực / Quản trị → Dữ liệu ABI).
Thứ tự:
  1. router nhận ý định bằng code. Hiểu trọn câu hỏi (plain) + ⚙ ABI_CODE_ANSWER -> trả lời bằng code, không gọi AI.
  2. còn lại: thẻ dữ kiện của ý định (nếu có) là đoạn [1], cộng các đoạn tìm được trong chỉ mục của phiên bản đang dùng
     -> AI (model trên máy) trả lời (Chuyên gia). KHÔNG gọi trợ lý AI của web (tốn token của chủ web; leader cấm 17/10/2026).
"""
from __future__ import annotations

import time

from ..server import search, settings
from . import normalize, router, store, tools

CARD_MAX = 6000   # ký tự (~2.000 token): thẻ dữ kiện + vài đoạn tìm được + lịch sử vẫn vừa ngữ cảnh 8192 token
NOT_SYNCED = ("Dữ liệu abi.com.vn chưa được đồng bộ về máy nên chưa trả lời được. Dev bấm \"Đồng bộ abi.com.vn\" ở dòng lĩnh vực ABI "
              "trong Quản lý lĩnh vực (cần khoá API ở ⚙; lần đầu khoảng 3 phút), rồi hỏi lại.")


def search_text(squery: str, data: dict) -> str:
    """"Trung tâm" không kèm tên khác = Trung tâm Ươm tạo (ABI): ghép tên đầy đủ vào câu tìm. Đo 16/10: "Trung tâm được thành lập
    năm nào?" từng tìm trúng trang đối tác "Trung tâm Nghiên cứu và Phát triển NN CNC" (2005) và AI trả lời theo trang đó."""
    q = " ".join(router.words(squery))
    name = (data.get("center") or {}).get("name") or ""
    if not name or " trung tam " not in f" {q} ":
        return squery
    others = [" ".join(router.words(x["name"]))[:40] for x in data.get("catalog") or [] if router.words(x["name"])[:2] == ["trung", "tam"]]
    if any(o and o in q for o in others) or " ".join(router.words(name)) in q:
        return squery   # đã nêu tên một trung tâm cụ thể
    return f"{squery} {name}"


def prepare(user_id: int, text: str, squery: str, dataset_ids: list[int], history: list[dict] | None = None,
            code_answer: bool | None = None) -> dict:
    """Trả {"answer": câu trả lời bằng code hoặc None, "sources", "evidence", "info", "extra": lời dặn thêm cho AI}.
    code_answer: từ hồ sơ lĩnh vực ABI (G4.3); None = theo ⚙ ABI_CODE_ANSWER."""
    t0 = time.perf_counter()
    data, now = store.data(), tools.now_vn()
    info: dict = {"abi": {"synced_at": (data or {}).get("synced_at"), "version": store.active_id(), "source": (data or {}).get("source")}}
    if not data:
        info["abi"]["error"] = "chưa đồng bộ"
        return {"answer": NOT_SYNCED, "sources": [], "evidence": [], "info": info, "extra": []}
    extra = [tools.today_line(now) + " " + tools.updated_line(data).strip("_") +
             " Câu hỏi về thời gian (sắp tới, đã qua) phải so với ngày hôm nay.",
             # đo 16/10: AI viết dài (hỏi số người thì kể cả 12 tên) là phần chậm nhất của câu trả lời (~55 token/giây)
             "Trả lời đúng trọng tâm câu hỏi, ngắn gọn; không liệt kê thêm thông tin người dùng không hỏi.",
             f"\"Trung tâm\" trong câu hỏi (không kèm tên khác) là {(data.get('center') or {}).get('name') or 'Trung tâm Ươm tạo'}; "
             "thông tin của đối tác hay trung tâm khác trong dữ liệu không phải của Trung tâm."]
    # câu hiện tại trước; chỉ khi nó không đủ ý (vd. "còn tháng 11 thì sao?") mới dùng câu đã ghép với câu hỏi trước
    r = router.route(text, data, now) or (router.route(squery, data, now) if squery != text else None)
    if r:
        info["abi"].update(intent=r["intent"], plain=r["plain"])
    if r and r["plain"] and (settings.get("ABI_CODE_ANSWER") if code_answer is None else code_answer):
        info["abi"]["code_answer"] = True
        info["abi"]["ms"] = int((time.perf_counter() - t0) * 1000)
        return {"answer": r["fact"]["answer"], "sources": r["fact"]["sources"], "evidence": [], "info": info, "extra": extra}
    evidence = []
    if r:
        f = r["fact"]
        url = f["card_url"]
        if url and url.startswith("/"):   # đường dẫn trang danh sách -> link trên đúng nguồn (bản thật / staging)
            url = normalize.link(data, url)
        evidence.append({"id": None, "title": f["card_title"], "dataset": data.get("site_url", "abi.com.vn").split("//")[-1],
                         "text": f["text"][:CARD_MAX], "score": None, "full": True, "url": url})
    if dataset_ids:
        found, sinfo = search.search(user_id, search_text(squery, data), dataset_ids)
        for e in found:
            e["url"] = (e.get("fields") or {}).get("Link")
        evidence += found[:max(1, settings.get("RETRIEVAL_TOP_K") - (1 if r else 0))]
        info.update(sinfo)
    else:
        info["abi"]["index"] = "chưa có chỉ mục tìm kiếm (đồng bộ chưa dựng xong hoặc thiếu Ollama)"
    info["abi"]["ms"] = int((time.perf_counter() - t0) * 1000)
    return {"answer": None, "sources": [], "evidence": evidence, "info": info, "extra": extra}
