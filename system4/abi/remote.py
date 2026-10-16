"""Trợ lý RAG của chủ web: POST https://api.abi.com.vn/api/v1/rag/query — chỉ là nguồn DỰ PHÒNG (⚙ ABI_REMOTE_RAG).

Sự thật đã kiểm (docs/PLAN_ABI_LINH_VUC.md mục 1.1–1.2, kiểm lại 16/10 sau khi chủ web chỉnh: vẫn như cũ):
  - chỉ nhận POST, body {"query", "locale": "vi", "context"?, "sessionId"?}; mở bằng trình duyệt (GET) -> 404; không có khoá riêng
  - giới hạn khoảng 3–4 câu liên tiếp, nghỉ vài phút mới hỏi lại được; chạm giới hạn vẫn trả HTTP 201 với
    responseKind = "service_error" -> phải xem responseKind, không xem mã HTTP; gặp service_error thì nghỉ COOLDOWN giây
  - không có dữ liệu cơ cấu tổ chức và đọc bài tin cũ -> không dùng cho câu đếm (router đã lo bằng code); câu trả lời dẫn bài
    bị loại (normalize.excluded: bài cũ, trang mẫu) thì bỏ
  - "context" (đọc từ khung chat của web, RagConversation-*.js, hàm M): các cặp {"role": "user"|"assistant", "content"} của tối đa
    3 lượt gần nhất, mỗi tin <= 2.000 ký tự, tổng <= 8.000; bỏ câu chào / câu báo lỗi. Gửi đúng như vậy cho câu hỏi tiếp.
"""
from __future__ import annotations

import threading
import time
from collections import deque

from ..server import settings
from .client import SITE_URL, AbiError, Client

WINDOW = 300          # giây: cửa sổ đếm số câu đã hỏi
COOLDOWN = 300        # giây nghỉ sau service_error
CACHE_TTL = 600
CTX_TURNS, CTX_MSG_MAX, CTX_TOTAL_MAX = 3, 2000, 8000
_lock = threading.Lock()
_calls: deque = deque()
_state = {"cooldown_until": 0.0, "last": None}
_cache: dict[str, tuple[float, dict | None]] = {}


def status() -> dict:
    now = time.time()
    with _lock:
        while _calls and now - _calls[0] > WINDOW:
            _calls.popleft()
        return {"calls_in_window": len(_calls), "cooldown_s": max(0, int(_state["cooldown_until"] - now)), "last": _state["last"]}


def _take_slot() -> str | None:
    now = time.time()
    with _lock:
        if now < _state["cooldown_until"]:
            return "đang nghỉ sau khi chạm hạn mức"
        while _calls and now - _calls[0] > WINDOW:
            _calls.popleft()
        if len(_calls) >= settings.get("ABI_REMOTE_MAX_PER_5MIN"):
            return "đã dùng hết lượt trong 5 phút"
        _calls.append(now)
        return None


def context(history: list[dict]) -> list[dict]:
    """Lịch sử hội thoại (System 4: {role, content, status, meta}) -> "context" theo đúng cách khung chat của web dựng."""
    pairs, q = [], None
    for m in history or []:
        if m.get("role") == "user":
            q = m
        elif q is not None and m.get("role") == "assistant":
            meta = m.get("meta") or {}
            if m.get("status", "done") == "done" and not meta.get("small_talk") and not meta.get("guard") and (m.get("content") or "").strip():
                pairs.append([{"role": "user", "content": q["content"].strip()[:CTX_MSG_MAX]},
                              {"role": "assistant", "content": m["content"].strip()[:CTX_MSG_MAX]}])
            q = None
    out, total = [], 0
    for p in reversed(pairs[-CTX_TURNS:]):
        size = sum(len(x["content"]) for x in p)
        if total + size > CTX_TOTAL_MAX:
            break
        out = p + out
        total += size
    return out


def ask(question: str, client: Client | None = None, history: list[dict] | None = None,
        blocked_urls: set[str] | None = None) -> dict:
    """Trả {"ok": bool, "kind", "answer", "citations": [{title, url}], "why"}; không ném lỗi.
    blocked_urls: link các bài bị loại (bài cũ, trang mẫu) — trợ lý web dẫn bài nào trong đó thì không dùng câu trả lời."""
    ctx = context(history or [])
    key = " ".join(question.lower().split()) if not ctx else None   # câu hỏi tiếp phụ thuộc ngữ cảnh: không dùng bộ nhớ đệm
    hit = _cache.get(key) if key else None
    if hit and time.time() - hit[0] < CACHE_TTL and hit[1]:
        return {**hit[1], "cached": True}
    why = _take_slot()
    if why:
        return {"ok": False, "why": why}
    c = client or Client(rps=1, timeout=15, max_retries=0)
    t0 = time.perf_counter()
    body = {"query": question.strip()[:1000], "locale": "vi", **({"context": ctx} if ctx else {})}
    try:
        d = (c.post("/rag/query", body).get("data") or {})
    except AbiError as e:
        return {"ok": False, "why": str(e)}
    finally:
        if client is None:
            c.close()
    kind = d.get("responseKind")
    res = {"ok": kind == "grounded_answer", "kind": kind, "context_mode": d.get("contextMode"), "context_turns": len(ctx) // 2,
           "answer": (d.get("answer") or "").strip(),
           "citations": [{"title": x.get("title") or "", "url": SITE_URL + x["url"] if str(x.get("url", "")).startswith("/") else x.get("url")}
                         for x in d.get("citations") or [] if x.get("url")],
           "ms": int((time.perf_counter() - t0) * 1000)}
    with _lock:
        _state["last"] = {"kind": kind, "at": time.strftime("%H:%M:%S")}
        if kind == "service_error":
            _state["cooldown_until"] = time.time() + COOLDOWN
    bad = [x["url"] for x in res["citations"] if x["url"] in (blocked_urls or set())]
    if res["ok"] and bad:
        res.update(ok=False, why="trợ lý của web dẫn bài cũ / trang mẫu: " + ", ".join(bad))
    elif not res["ok"]:
        res["why"] = {"service_error": "trợ lý của web đang chạm hạn mức", "no_match": "trợ lý của web không tìm thấy",
                      "out_of_scope": "ngoài phạm vi trợ lý của web"}.get(kind, f"trợ lý của web trả {kind}")
    elif key:
        _cache[key] = (time.time(), res)
    return res


def evidence(res: dict) -> dict:
    """Câu trả lời của trợ lý web -> một đoạn dữ liệu cho AI (ghi rõ nguồn là trợ lý của web, không phải dữ liệu gốc)."""
    cites = "\n".join(f"- {c['title']}: {c['url']}" for c in res.get("citations") or [])
    return {"id": None, "title": "Trợ lý tra cứu trên abi.com.vn", "dataset": "abi.com.vn (trợ lý của web)", "score": None, "full": True,
            "text": res["answer"] + (f"\nNguồn trợ lý dẫn:\n{cites}" if cites else ""),
            "url": (res.get("citations") or [{}])[0].get("url") or SITE_URL}
