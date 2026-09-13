"""Tra cứu ngoài - CHỈ nhận kết quả từ danh sách nguồn chính thống.

Bản cũ đẩy nguyên câu hỏi của công dân ra DuckDuckGo và khi lỗi thì bảo mô hình
"dùng kiến thức pháp luật chung" mà không nói cho người dùng biết. Đây là chỗ
duy nhất có thể sinh ra khẳng định pháp lý không nguồn, nên nó được siết lại:
lọc theo domain, và luôn trả về danh sách nguồn để hiển thị.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urlparse

from config import (WEB_SEARCH_ALLOWLIST, WEB_SEARCH_ENABLED,
                    WEB_SEARCH_MAX_RESULTS, WEB_SEARCH_QUERY_SITES,
                    WEB_SEARCH_STRICT, WEB_SEARCH_TIMEOUT)


@dataclass
class WebResult:
    context: str = ""
    sources: list[str] = field(default_factory=list)
    ok: bool = False
    error: str = ""


def _domain_allowed(url: str) -> bool:
    try:
        host = (urlparse(url).hostname or "").lower()
    except Exception:
        return False
    return any(host == d or host.endswith("." + d) for d in WEB_SEARCH_ALLOWLIST)


def search(query: str, max_results: int = WEB_SEARCH_MAX_RESULTS) -> WebResult:
    if not WEB_SEARCH_ENABLED:
        return WebResult(ok=False, error="web search đang tắt")
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        try:
            from ddgs import DDGS  # tên gói mới
        except ImportError as exc:
            return WebResult(ok=False, error=f"thiếu thư viện tìm kiếm: {exc}")

    def _run(q: str, n: int):
        """Gọi DDGS, chịu được khác biệt giữa các phiên bản thư viện."""
        try:
            client = DDGS(timeout=WEB_SEARCH_TIMEOUT)
        except TypeError:
            client = DDGS()                       # bản cũ không có timeout
        return client.text(q, max_results=n) or []

    def _collect(raw, strict: bool):
        chunks, sources = [], []
        for r in raw:
            url = r.get("href") or r.get("url") or ""
            if strict and not _domain_allowed(url):
                continue
            body = (r.get("body") or r.get("snippet") or "").strip()
            if not body:
                continue
            chunks.append(body)
            host = urlparse(url).hostname or url
            if host not in sources:
                sources.append(host)
            if len(chunks) >= max_results:
                break
        return chunks, sources

    # Lượt 1: truy vấn THƯỜNG (không nhét site: vào chuỗi), lọc theo allowlist.
    try:
        raw = _run(query, max_results * 5)
    except Exception as exc:
        print("[websearch] lỗi:", exc)
        return WebResult(ok=False, error=str(exc))

    chunks, sources = _collect(raw, strict=WEB_SEARCH_STRICT)

    # Lượt 2: nếu chưa có gì, thử thêm MỘT site: duy nhất (OR nhiều site làm
    # DuckDuckGo trả rỗng - đây chính là lỗi cũ).
    if not chunks and WEB_SEARCH_STRICT:
        for domain in WEB_SEARCH_ALLOWLIST[:WEB_SEARCH_QUERY_SITES]:
            try:
                raw = _run(f"{query} site:{domain}", max_results * 2)
            except Exception:
                continue
            chunks, sources = _collect(raw, strict=True)
            if chunks:
                break

    if not chunks:
        return WebResult(ok=False, error="không có kết quả từ nguồn chính thống")
    return WebResult(context="\n\n".join(chunks), sources=sources, ok=True)
