"""Tìm web bằng DuckDuckGo (ddgs). Dùng chung cho Friendly (system4/server/websearch.py) và nút "Tìm web" của Strict.
Port gọn từ System 1 (V10.6 mcp_search/engine.py): chỉ ddgs, không lọc tên miền (không còn yêu cầu .gov.vn).
ponytail: chỉ dùng đoạn trích của ddgs, chưa đọc cả trang (trafilatura)."""
from __future__ import annotations
import re
import time
import unicodedata
from urllib.parse import urlparse

from . import llm
from config import WEBSEARCH_MODEL

MODEL_PROVIDER = None   # System 4 gán hàm trả model chọn ở ⚙ (WEBSEARCH_MODEL); không có thì dùng biến môi trường S3_WEBSEARCH_MODEL

_cache: dict[tuple, tuple[float, list[dict]]] = {}   # (truy vấn, n) -> (lúc lưu, kết quả); tránh gọi lại khi sinh lại câu trả lời


def host_of(url: str) -> str:
    return (urlparse(url).hostname or "").removeprefix("www.")


def search(query: str, n: int = 5, timeout: int = 8) -> tuple[list[dict], dict]:
    """(evidence, info). evidence = [{id None, title, dataset (tên miền), url, text, score None}] (cùng dạng search.py của System 4).
    Lỗi mạng / bị giới hạn: evidence rỗng và info["error"] có lý do (không ném lỗi)."""
    t0, info = time.perf_counter(), {"web": True, "query": query}
    hit = _cache.get((query, n))
    if hit and time.time() - hit[0] < 600:
        return hit[1], {**info, "cached": True, "ms": 0}
    rows, err = [], ""
    for _ in (1, 2):   # thử lại 1 lần (DuckDuckGo hay từ chối lẻ tẻ)
        try:
            from ddgs import DDGS
            rows = DDGS(timeout=timeout).text(query, region="vn-vi", max_results=n) or []
            err = ""
            break
        except Exception as e:   # noqa: BLE001 - mọi lỗi mạng/thư viện đều thành "không có kết quả" kèm lý do
            err = f"{type(e).__name__}: {e}"[:200]
    ev, seen = [], set()
    for r in rows:
        url = (r.get("href") or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        ev.append({"id": None, "title": (r.get("title") or host_of(url)).strip(), "dataset": host_of(url), "url": url,
                   "text": (r.get("body") or "").strip(), "score": None})
    if ev:
        _cache[(query, n)] = (time.time(), ev)
    return ev, {**info, "n": len(ev), "error": err, "ms": int((time.perf_counter() - t0) * 1000)}


def model_name() -> str:
    return (MODEL_PROVIDER() if MODEL_PROVIDER else "") or WEBSEARCH_MODEL


def _plain(t: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFD", t.lower().replace("đ", "d")).encode("ascii", "ignore").decode()).strip()


_BAD = re.compile(r"(?<![a-z])(okay|let's|the user|i need to|first, i)(?![a-z])|toi (can|phai) (tra loi|xem|kiem tra|doc)|toi da 6 cau|ghi so nguon|chi dua vao cac ket qua")


def leaked(answer: str, question: str) -> bool:
    """Câu trả lời là rác: rỗng, lặp lại câu hỏi, viết bằng tiếng Anh, hoặc đọc lại luật/suy luận của chính model (model "suy nghĩ" hay bị)."""
    a, q = _plain(answer), _plain(question)
    return len(a) < 15 or bool(_BAD.search(a)) or (a.startswith(q[:30]) and len(a) <= len(q) + 40)


_SCHEMA = {"type": "object", "required": ["answer"], "properties": {"answer": {"type": "string"}}}
_SYSTEM = ("Bạn trả lời câu hỏi CHỈ dựa vào các kết quả tìm kiếm web được đưa. Không dùng kiến thức ngoài, không suy đoán. "
           "Viết tiếng Việt, tối đa 6 câu, ghi số nguồn [1], [2]… ngay sau ý lấy từ nguồn đó. "
           "Kết quả web có thể cũ hoặc sai: nếu các nguồn mâu thuẫn hoặc không đủ để trả lời thì nói rõ.")


def web_block(question: str, n: int = 5, timeout: int = 8) -> tuple[dict, dict]:
    """Khối trả lời từ web cho Strict: {title, text, sources[{label,url}]}. Không có kết quả -> khối báo không tìm thấy (không bịa)."""
    ev, info = search(question, n, timeout)
    if not ev:
        why = "không có mạng hoặc DuckDuckGo từ chối" if info.get("error") else "không có kết quả"
        return {"title": "Tra cứu thêm trên web", "text": f"Không tra được trên web ({why}).", "sources": []}, info
    ctx = "\n\n".join(f"[{i}] {e['title']} ({e['dataset']})\n{e['text']}" for i, e in enumerate(ev, 1))
    t0 = time.perf_counter()
    try:
        # ép đầu ra JSON: model dùng chung có thể là loại "suy nghĩ" (qwen3:4b); think=False không chặn được, nó viết suy luận vào câu trả lời
        d = llm.chat_json(_SYSTEM, f"Kết quả tìm kiếm:\n{ctx}\n\nCâu hỏi: {question}", _SCHEMA, think=False, timeout=60,
                          model=model_name())
        text = str(d.get("answer") or "").strip()
        if leaked(text, question):   # lớp bảo vệ: không in câu rác, chỉ đưa danh sách nguồn
            info["leaked"] = text[:200]
            text = "Đã tìm thấy các trang sau nhưng chưa tóm tắt được. Bạn mở nguồn bên dưới để xem."
    except llm.LLMError as e:
        info["error"] = str(e)[:200]
        text = "Đã tìm thấy các trang sau nhưng chưa tóm tắt được (mô hình không phản hồi)."
    info["llm_ms"] = int((time.perf_counter() - t0) * 1000)
    return {"title": "Tra cứu thêm trên web", "text": text,
            "sources": [{"label": f"[{i}] {e['title']} — {e['dataset']}", "url": e["url"]} for i, e in enumerate(ev, 1)]}, info
