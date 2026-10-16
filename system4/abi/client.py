"""Lớp mạng DUY NHẤT của lĩnh vực ABI. Mọi request ra abi.com.vn đều đi qua đây.

Web abi.com.vn là React SPA: HTML không có nội dung, dữ liệu nằm ở API JSON (tìm bằng cách đọc JS của web, xem
docs/PLAN_ABI_LINH_VUC.md mục 1.3). Chỉ dùng API công khai (GET, không đăng nhập); không đụng /admin.

Chủ web đã cho phép chính thức (16/10/2026, docs/SYSTEM4_ABI.md mục 8) với quy ước:
  · User-Agent định danh: "AHBI-Assistant-Bot/1.0 (+liên hệ của nhóm)" — liên hệ đặt ở ⚙ ABI_BOT_CONTACT
  · tối đa 2 request/giây (MAX_RPS, không vượt được kể cả khi gọi Client(rps=…)), quét định kỳ 6 tiếng
  · không hiển thị email / số điện thoại riêng của cán bộ (sync.py bỏ ngay khi tải về)
Ngoài ra: retry + backoff cho 429/5xx và lỗi mạng, timeout rõ ràng, TLS verify luôn bật,
body luôn là JSON UTF-8 (gõ tiếng Việt thẳng vào curl trên Windows gửi sai byte).
"""
from __future__ import annotations

import logging
import random
import threading
import time

import httpx

BASE_URL = "https://api.abi.com.vn/api/v1"
SITE_URL = "https://abi.com.vn"
RETRY_STATUS = {429, 500, 502, 503, 504}
MAX_RPS = 2.0                                   # thoả thuận với chủ web
BOT_NAME = "AHBI-Assistant-Bot/1.0"             # tên chủ web đề nghị
DEFAULT_CONTACT = "https://github.com/3-hWnG/intern-amazing-group_7"   # khi chưa điền ⚙ ABI_BOT_CONTACT


def user_agent() -> str:
    try:
        from ..server import settings
        contact = (settings.get("ABI_BOT_CONTACT") or "").strip()
    except Exception:   # chạy ngoài server, thiếu cài đặt
        contact = ""
    return f"{BOT_NAME} (+{contact or DEFAULT_CONTACT})"

log = logging.getLogger("system4.abi.client")


class AbiError(RuntimeError):
    """API trả lỗi không thử lại được (4xx). code = mã lỗi trong {"error": {"code": ...}} nếu có."""

    def __init__(self, message: str, status: int | None = None, code: str | None = None):
        super().__init__(message)
        self.status, self.code = status, code


class Client:
    """Dùng như context manager. transport: chỉ để test (httpx.MockTransport)."""

    def __init__(self, rps: float = MAX_RPS, timeout: float = 20.0, max_retries: int = 3, transport=None):
        if transport is None:   # mạng thật: không bao giờ quá MAX_RPS (rps <= 0 = không chờ, chỉ cho API giả trong test)
            rps = min(rps, MAX_RPS) if rps > 0 else MAX_RPS
        self._gap = 1.0 / rps if rps > 0 else 0.0
        self._last = 0.0
        self._lock = threading.Lock()
        self._max_retries = max_retries
        self._http = httpx.Client(base_url=BASE_URL, timeout=timeout, follow_redirects=True, transport=transport,
                                  headers={"Accept": "application/json", "User-Agent": user_agent()})
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

    def _request(self, method: str, path: str, params: dict | None = None, body: dict | None = None) -> dict:
        last: Exception | None = None
        for attempt in range(self._max_retries + 1):
            self._wait()
            self.requests += 1
            try:
                resp = self._http.request(method, path, params=params, json=body)
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
                        raise AbiError(f"{path}: HTTP {resp.status_code} {err.get('code') or ''} {err.get('message') or ''}".strip(),
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

    def get(self, path: str, **params) -> dict:
        return self._request("GET", path, params={k: v for k, v in params.items() if v is not None})

    def post(self, path: str, body: dict) -> dict:
        return self._request("POST", path, body=body)

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
