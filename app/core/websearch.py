"""Tra cứu ngoài - CHỈ nhận kết quả từ danh sách nguồn chính thống.

Bản cũ đẩy nguyên câu hỏi của công dân ra DuckDuckGo và khi lỗi thì bảo mô hình
"dùng kiến thức pháp luật chung" mà không nói cho người dùng biết. Đây là chỗ
duy nhất có thể sinh ra khẳng định pháp lý không nguồn, nên nó được siết lại:
lọc theo domain, và luôn trả về danh sách nguồn để hiển thị.

v6.2 — thêm NHẬT KÝ CHẨN ĐOÁN.

Trước đây khi tra hỏng, tất cả những gì hệ thống nói được là "không có kết quả".
Không phân biệt nổi bốn tình huống hoàn toàn khác nhau:

    1. thiếu thư viện
    2. thư viện ném lỗi (chặn tốc độ, đổi API, mất mạng)
    3. tra ra kết quả nhưng KHÔNG cái nào thuộc allowlist  <- rất hay gặp
    4. tra ra thật sự rỗng

Giờ mỗi lần thử được ghi lại: truy vấn gì, backend nào, mấy kết quả thô, mấy
cái qua được allowlist, lỗi gì. Xem ở bảng Dev hoặc POST /api/dev/websearch.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urlparse

from config import (WEB_SEARCH_ALLOWLIST, WEB_SEARCH_BACKENDS,
                    WEB_SEARCH_ENABLED, WEB_SEARCH_MAX_RESULTS,
                    WEB_SEARCH_PLAIN_FALLBACK, WEB_SEARCH_QUERY_HINT,
                    WEB_SEARCH_QUERY_SITES, WEB_SEARCH_REPORT_BLOCKED,
                    WEB_SEARCH_RETURN_URLS, WEB_SEARCH_STRICT,
                    WEB_SEARCH_TIMEOUT)


@dataclass
class Attempt:
    """Một lần gọi thư viện tìm kiếm."""
    query: str
    backend: str
    raw: int = 0                  # số kết quả thô
    allowed: int = 0              # số kết quả qua được allowlist
    blocked_hosts: list[str] = field(default_factory=list)
    error: str = ""

    def describe(self) -> str:
        if self.error:
            return f"[{self.backend}] {self.query!r} -> LỖI: {self.error}"
        if self.raw and not self.allowed:
            hosts = ", ".join(self.blocked_hosts[:5]) or "?"
            return (f"[{self.backend}] {self.query!r} -> {self.raw} kết quả, "
                    f"0 qua allowlist (bị loại: {hosts})")
        return (f"[{self.backend}] {self.query!r} -> {self.raw} kết quả, "
                f"{self.allowed} qua allowlist")


@dataclass
class WebResult:
    context: str = ""
    sources: list[str] = field(default_factory=list)      # URL đầy đủ để bấm vào
    titles: list[str] = field(default_factory=list)
    ok: bool = False
    error: str = ""
    attempts: list[Attempt] = field(default_factory=list)
    blocked_by_allowlist: bool = False   # tra ĐƯỢC nhưng nguồn không chính thống

    def report(self) -> str:
        """Nhật ký nhiều dòng cho bảng Dev."""
        lines = [a.describe() for a in self.attempts]
        if self.ok:
            lines.append(f"=> ĐẠT, {len(self.sources)} nguồn: {', '.join(self.sources)}")
        else:
            lines.append(f"=> HỎNG: {self.error}")
        return "\n".join(lines)


def _domain_allowed(url: str) -> bool:
    try:
        host = (urlparse(url).hostname or "").lower()
    except Exception:
        return False
    return any(host == d or host.endswith("." + d) for d in WEB_SEARCH_ALLOWLIST)


def _load_client():
    """Trả về (lớp DDGS, tên gói) hoặc (None, thông báo lỗi)."""
    try:
        from ddgs import DDGS                     # tên gói MỚI
        return DDGS, "ddgs"
    except ImportError:
        pass
    try:
        from duckduckgo_search import DDGS        # tên gói cũ
        return DDGS, "duckduckgo_search"
    except ImportError as exc:
        return None, (f"thiếu thư viện tìm kiếm ({exc}). Cài bằng:\n"
                      f"  .venv\\Scripts\\python.exe -m pip install ddgs")


def _call(DDGS, query: str, n: int, backend: str):
    """Gọi thư viện, chịu được khác biệt giữa các phiên bản."""
    try:
        client = DDGS(timeout=WEB_SEARCH_TIMEOUT)
    except TypeError:
        client = DDGS()                           # bản cũ không nhận timeout
    if backend and backend != "auto":
        try:
            return client.text(query, max_results=n, backend=backend) or []
        except TypeError:
            pass                                  # bản cũ không có tham số backend
    return client.text(query, max_results=n) or []


def search(query: str, max_results: int = WEB_SEARCH_MAX_RESULTS) -> WebResult:
    if not WEB_SEARCH_ENABLED:
        return WebResult(ok=False, error="web search đang tắt (WEB_SEARCH_ENABLED=False)")

    query = (query or "").strip()
    if not query:
        return WebResult(ok=False, error="truy vấn rỗng")

    DDGS, label = _load_client()
    if DDGS is None:
        return WebResult(ok=False, error=label)

    result = WebResult()
    saw_raw = False

    def try_once(q: str, n: int, backend: str) -> bool:
        """Trả về True nếu lấy được nội dung hợp lệ."""
        nonlocal saw_raw
        attempt = Attempt(query=q, backend=f"{label}/{backend}")
        result.attempts.append(attempt)
        try:
            raw = _call(DDGS, q, n, backend)
        except Exception as exc:
            attempt.error = f"{type(exc).__name__}: {exc}"
            return False

        attempt.raw = len(raw)
        saw_raw = saw_raw or bool(raw)
        chunks, sources, titles = [], [], []
        for r in raw:
            url = r.get("href") or r.get("url") or ""
            host = (urlparse(url).hostname or url or "?").lower()
            if WEB_SEARCH_STRICT and not _domain_allowed(url):
                if host not in attempt.blocked_hosts:
                    attempt.blocked_hosts.append(host)
                continue
            body = (r.get("body") or r.get("snippet") or "").strip()
            if not body:
                continue
            title = (r.get("title") or "").strip()
            # Ghi rõ NGUỒN của từng đoạn ngay trong ngữ cảnh. Không có nó, mô
            # hình trộn số liệu của nhiều trang vào nhau mà không biết mình
            # đang trộn — đúng lỗi "thẻ tạm trú cho người nước ngoài 145 USD"
            # bị gán cho thủ tục gia hạn tạm trú trong nước.
            chunks.append(f"[Nguồn: {host}] {title}\n{body}" if title
                          else f"[Nguồn: {host}] {body}")
            link = url if WEB_SEARCH_RETURN_URLS and url else host
            if link not in sources:
                sources.append(link)
                titles.append(title or host)
            if len(chunks) >= max_results:
                break

        attempt.allowed = len(chunks)
        if chunks:
            result.context = "\n\n".join(chunks)
            result.sources = sources
            result.titles = titles
            result.ok = True
            return True
        return False

    # Lượt 1: BÁM NGUỒN CHÍNH THỐNG ngay trong truy vấn.
    # Truy vấn trần cho 20 kết quả mà chỉ 4 cái qua được allowlist — phí, và
    # dễ lôi về nhầm chuyện (thẻ tạm trú cho người nước ngoài thay vì thủ tục
    # gia hạn tạm trú trong nước).
    hinted = f"{query} {WEB_SEARCH_QUERY_HINT}".strip() if WEB_SEARCH_QUERY_HINT else query
    for backend in WEB_SEARCH_BACKENDS:
        if try_once(hinted, max_results * 4, backend):
            return result

    # Lượt 2: từng site: cụ thể (ghép nhiều site bằng OR làm câu quá dài,
    # DuckDuckGo hay trả rỗng — đó là lỗi của bản đầu tiên).
    if WEB_SEARCH_STRICT:
        backend = WEB_SEARCH_BACKENDS[0] if WEB_SEARCH_BACKENDS else "auto"
        for domain in WEB_SEARCH_ALLOWLIST[:WEB_SEARCH_QUERY_SITES]:
            if try_once(f"{query} site:{domain}", max_results * 2, backend):
                return result

    # Lượt 3: truy vấn TRẦN, vẫn lọc allowlist. Có câu chỉ tìm thấy kiểu này.
    if WEB_SEARCH_PLAIN_FALLBACK:
        for backend in WEB_SEARCH_BACKENDS[:1]:
            if try_once(query, max_results * 5, backend):
                return result

    # Phân biệt rõ BỐN kiểu hỏng — đây là thứ bản cũ không nói được.
    errors = [a.error for a in result.attempts if a.error]
    blocked = [h for a in result.attempts for h in a.blocked_hosts]
    if errors and not saw_raw:
        result.error = f"thư viện tìm kiếm lỗi: {errors[0]}"
    elif saw_raw and blocked and WEB_SEARCH_REPORT_BLOCKED:
        result.blocked_by_allowlist = True
        result.error = (f"tìm thấy kết quả nhưng KHÔNG nguồn nào nằm trong "
                        f"allowlist ({len(set(blocked))} domain bị loại, ví dụ: "
                        f"{', '.join(sorted(set(blocked))[:3])})")
    elif saw_raw:
        result.error = "có kết quả nhưng không trích được nội dung"
    else:
        result.error = "không tìm thấy kết quả nào"
    return result


def selftest(query: str = "thủ tục cấp hộ chiếu phổ thông") -> dict:
    """Chạy thử và trả về toàn bộ chẩn đoán. Dùng cho /api/dev/websearch."""
    DDGS, label = _load_client()
    result = search(query)
    return {
        "query": query,
        "library": label if DDGS is not None else None,
        "library_error": None if DDGS is not None else label,
        "enabled": WEB_SEARCH_ENABLED,
        "strict": WEB_SEARCH_STRICT,
        "timeout": WEB_SEARCH_TIMEOUT,
        "backends": list(WEB_SEARCH_BACKENDS),
        "allowlist": list(WEB_SEARCH_ALLOWLIST),
        "ok": result.ok,
        "error": result.error,
        "blocked_by_allowlist": result.blocked_by_allowlist,
        "sources": result.sources,
        "context_chars": len(result.context),
        "attempts": [
            {"query": a.query, "backend": a.backend, "raw": a.raw,
             "allowed": a.allowed, "blocked_hosts": a.blocked_hosts,
             "error": a.error, "text": a.describe()}
            for a in result.attempts
        ],
        "report": result.report(),
    }
