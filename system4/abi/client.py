"""Lớp mạng DUY NHẤT của lĩnh vực ABI. Mọi request ra abi.com.vn / staging.abi.com.vn đều đi qua đây.

Web là React SPA: HTML không có nội dung, dữ liệu nằm ở API JSON. Chủ web đã cho phép chính thức (16/10/2026,
docs/SYSTEM4_ABI.md mục 8) danh sách endpoint đọc dữ liệu, với quy ước:
  · khoá API (từ 17/10): header "Authorization: Bearer <khoá>" — khoá ở ⚙ ABI_API_KEY hoặc biến môi trường ABI_API_KEY,
    chỉ nằm trên máy (runtime/settings.json), không bao giờ vào git; cùng một khoá cho bản thật và staging
  · User-Agent định danh: "AHBI-Assistant-Bot/1.0 (+liên hệ của nhóm)" — liên hệ ở ⚙ ABI_BOT_CONTACT
  · tối đa 2 request/giây (MAX_RPS, không vượt được kể cả khi gọi Client(rps=…)), quét định kỳ 6 tiếng
  · không hiển thị email / số điện thoại riêng của cán bộ (sync.py bỏ ngay khi tải về)
KHÔNG BAO GIỜ gọi trợ lý AI của web (/rag/...): tốn token (tiền) của chủ web — leader cấm (17/10). Client chặn cứng.
Ngoài ra: chỉ GET, retry + backoff cho 429/5xx và lỗi mạng, timeout rõ ràng, TLS verify luôn bật.
"""
from __future__ import annotations

import logging
import os
import random
import threading
import time

import httpx

# Hai nguồn: bản thật (tự đồng bộ theo lịch) và staging (môi trường thử nghiệm của đội làm web, chỉ đồng bộ khi bấm nút)
SOURCES = {
    "prod": {"label": "abi.com.vn", "api": "https://api.abi.com.vn/api/v1", "site": "https://abi.com.vn"},
    "staging": {"label": "staging.abi.com.vn", "api": "https://api-staging.abi.com.vn/api/v1", "site": "https://staging.abi.com.vn"},
}
BASE_URL = SOURCES["prod"]["api"]
SITE_URL = SOURCES["prod"]["site"]
RETRY_STATUS = {429, 500, 502, 503, 504}
MAX_RPS = 2.0                                   # thoả thuận với chủ web
BOT_NAME = "AHBI-Assistant-Bot/1.0"             # tên chủ web đề nghị
DEFAULT_CONTACT = "https://github.com/3-hWnG/intern-amazing-group_7"   # khi chưa điền ⚙ ABI_BOT_CONTACT
FORBIDDEN = ("/rag",)                           # trợ lý AI của web: không bao giờ gọi

log = logging.getLogger("system4.abi.client")


def _setting(key: str) -> str:
    try:
        from ..server import settings
        return (settings.get(key) or "").strip()
    except Exception:   # chạy ngoài server, thiếu cài đặt
        return ""


def user_agent() -> str:
    return f"{BOT_NAME} (+{_setting('ABI_BOT_CONTACT') or DEFAULT_CONTACT})"


def api_key() -> str:
    return (os.environ.get("ABI_API_KEY") or "").strip() or _setting("ABI_API_KEY")


def key_hint() -> str:
    """Cho giao diện / nhật ký: chỉ cho biết có khoá hay không và 4 ký tự cuối, không bao giờ lộ cả khoá."""
    k = api_key()
    return f"đã có (…{k[-4:]})" if k else "chưa có"


class AbiError(RuntimeError):
    """API trả lỗi không thử lại được (4xx). code = mã lỗi trong {"error": {"code": ...}} nếu có."""

    def __init__(self, message: str, status: int | None = None, code: str | None = None):
        super().__init__(message)
        self.status, self.code = status, code


class Client:
    """Dùng như context manager. source: "prod" | "staging". transport: chỉ để test (httpx.MockTransport)."""

    def __init__(self, source: str = "prod", rps: float = MAX_RPS, timeout: float = 20.0, max_retries: int = 3, transport=None):
        if source not in SOURCES:
            raise ValueError(f"nguồn lạ: {source}")
        if transport is None:   # mạng thật: không bao giờ quá MAX_RPS (rps <= 0 = không chờ, chỉ cho API giả trong test)
            rps = min(rps, MAX_RPS) if rps > 0 else MAX_RPS
        self.source = source
        self._gap = 1.0 / rps if rps > 0 else 0.0
        self._last = 0.0
        self._lock = threading.Lock()
        self._max_retries = max_retries
        headers = {"Accept": "application/json", "User-Agent": user_agent()}
        if api_key():
            headers["Authorization"] = f"Bearer {api_key()}"
        self._http = httpx.Client(base_url=SOURCES[source]["api"], timeout=timeout, follow_redirects=True, transport=transport,
                                  headers=headers)
        self.requests = 0   # đếm request thật đã gửi (báo cáo đồng bộ)

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        self._http.close()

    def _wait(self) -> None:
        with self._lock:
            gap = time.monotonic() - self._last
            if gap < self._gap:
                time.sleep(self._gap - gap)
            self._last = time.monotonic()

    def get(self, path: str, **params) -> dict:
        if path.startswith(FORBIDDEN):
            raise AbiError(f"{path}: không gọi trợ lý AI của web (tốn token của chủ web)", None, "FORBIDDEN_BY_TEAM")
        params = {k: v for k, v in params.items() if v is not None}
        last: Exception | None = None
        for attempt in range(self._max_retries + 1):
            self._wait()
            self.requests += 1
            try:
                resp = self._http.get(path, params=params)
            except httpx.RequestError as e:   # mất mạng / hết giờ
                last = e
            else:
                if resp.status_code not in RETRY_STATUS:
                    try:
                        data = resp.json()
                    except ValueError:
                        raise AbiError(f"{path}: trả về không phải JSON (HTTP {resp.status_code})", resp.status_code) from None
                    if resp.status_code >= 400:
                        err = (data.get("error") or {}) if isinstance(data, dict) else {}
                        hint = " — kiểm khoá API ở ⚙ (ABI_API_KEY)" if resp.status_code in (401, 403) else ""
                        raise AbiError(f"{path}: HTTP {resp.status_code} {err.get('code') or ''} {err.get('message') or ''}".strip() + hint,
                                       resp.status_code, err.get("code"))
                    return data
                last = AbiError(f"{path}: HTTP {resp.status_code}", resp.status_code)
                ra = resp.headers.get("Retry-After")
                if ra and ra.isdigit() and attempt < self._max_retries:
                    time.sleep(min(int(ra), 60))
                    continue
            if attempt < self._max_retries:
                delay = min(2.0 ** attempt, 20.0) + random.uniform(0, 0.5)
                log.warning("thử lại %s sau %.1fs (lần %d/%d): %s", path, delay, attempt + 1, self._max_retries, last)
                time.sleep(delay)
        raise AbiError(f"{path}: thất bại sau {self._max_retries + 1} lần ({last})") from last

    def paged(self, path: str, limit: int, **params) -> list[dict]:
        """Mọi trang của một danh sách {"data": [...], "meta": {"pageCount": n}}."""
        out, page = [], 1
        while True:
            r = self.get(path, page=page, limit=limit, **params)
            items = r.get("data") or []
            out += items
            pages = int((r.get("meta") or {}).get("pageCount") or 1)
            if page >= pages or not items:
                return out
            page += 1
