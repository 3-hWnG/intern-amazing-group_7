"""Một lượt hỏi trong lĩnh vực ABI — server/chat.py gọi prepare() thay cho bước "tìm trong bộ dữ liệu" của Friendly.

Thứ tự:
  1. router nhận ý định bằng code. Hiểu trọn câu hỏi (plain) + ⚙ ABI_CODE_ANSWER -> trả lời bằng code, không gọi AI.
  2. còn lại: thẻ dữ kiện của ý định (nếu có) là đoạn [1], cộng các đoạn tìm được trong bộ dữ liệu ABI -> AI trả lời (Chuyên gia).
  3. không tìm được gì và ⚙ ABI_REMOTE_RAG bật -> hỏi trợ lý RAG của chủ web (có giới hạn tần suất), đưa kết quả cho AI diễn đạt.
"""
from __future__ import annotations

import time

from ..server import search, settings
from . import remote, router, store, tools

CARD_MAX = 6000   # ký tự (~2.000 token): thẻ dữ kiện + vài đoạn tìm được + lịch sử vẫn vừa ngữ cảnh 8192 token
NOT_SYNCED = ("Dữ liệu abi.com.vn chưa được đồng bộ về máy nên chưa trả lời được. Dev bấm \"Đồng bộ ngay\" ở dòng lĩnh vực ABI "
              "trong Quản lý lĩnh vực (mất khoảng 3 phút), rồi hỏi lại.")


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


def prepare(user_id: int, text: str, squery: str, dataset_ids: list[int], history: list[dict] | None = None) -> dict:
    """Trả {"answer": câu trả lời bằng code hoặc None, "sources", "evidence", "info", "extra": lời dặn thêm cho AI}."""
    t0 = time.perf_counter()
    data, now = store.data(), tools.now_vn()
    info: dict = {"abi": {"synced_at": (data or {}).get("synced_at")}}
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
    if r and r["plain"] and settings.get("ABI_CODE_ANSWER"):
        info["abi"]["code_answer"] = True
        info["abi"]["ms"] = int((time.perf_counter() - t0) * 1000)
        return {"answer": r["fact"]["answer"], "sources": r["fact"]["sources"], "evidence": [], "info": info, "extra": extra}
    evidence = []
    if r:
        f = r["fact"]
        evidence.append({"id": None, "title": f["card_title"], "dataset": "abi.com.vn", "text": f["text"][:CARD_MAX], "score": None,
                         "full": True, "url": f["card_url"]})
    if dataset_ids:
        found, sinfo = search.search(user_id, search_text(squery, data), dataset_ids)
        for e in found:
            e["url"] = (e.get("fields") or {}).get("Link")
        evidence += found[:max(1, settings.get("RETRIEVAL_TOP_K") - (1 if r else 0))]
        info.update(sinfo)
    else:
        info["abi"]["index"] = "chưa có chỉ mục tìm kiếm (đồng bộ chưa dựng xong hoặc thiếu Ollama)"
    if not evidence and settings.get("ABI_REMOTE_RAG"):
        blocked = {p["url"] for p in data.get("posts") or [] if p.get("excluded")}
        rem = remote.ask(text, history=history, blocked_urls=blocked)
        info["abi"]["remote"] = {k: v for k, v in rem.items() if k != "answer"}
        if rem.get("ok"):
            evidence.append(remote.evidence(rem))
    info["abi"]["ms"] = int((time.perf_counter() - t0) * 1000)
    return {"answer": None, "sources": [], "evidence": evidence, "info": info, "extra": extra}
