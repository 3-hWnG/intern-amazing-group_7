"""Lớp mạng DUY NHẤT của lĩnh vực ABI. Mọi request ra abi.com.vn đều đi qua đây.

Web abi.com.vn là React SPA: HTML không có nội dung, dữ liệu nằm ở API JSON (tìm bằng cách đọc JS của web, xem
docs/PLAN_ABI_LINH_VUC.md mục 1.3). Chỉ dùng API công khai (GET, không đăng nhập); không đụng /admin.

Nguyên tắc (giống system4/scraper/client.py):
  · retry + backoff cho 429/5xx và lỗi mạng
  · tối đa 2 request/giây, một luồng — web của cơ quan nhà nước, không đập
  · timeout rõ ràng, TLS verify luôn bật
  · body luôn là JSON UTF-8 (gõ tiếng Việt thẳng vào curl trên Windows gửi sai byte)
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
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "InstantSpecialist-Team7/1.0 (student project; abi.com.vn public data sync)")

log = logging.getLogger("system4.abi.client")


class AbiError(RuntimeError):
    """API trả lỗi không thử lại được (4xx). code = mã lỗi trong {"error": {"code": ...}} nếu có."""

    def __init__(self, message: str, status: int | None = None, code: str | None = None):
        super().__init__(message)
        self.status, self.code = status, code


class Client:
    """Dùng như context manager. transport: chỉ để test (httpx.MockTransport)."""

    def __init__(self, rps: float = 2.0, timeout: float = 20.0, max_retries: int = 3, transport=None):
        self._gap = 1.0 / rps if rps > 0 else 0.0
        self._last = 0.0
        self._lock = threading.Lock()
        self._max_retries = max_retries
        self._http = httpx.Client(base_url=BASE_URL, timeout=timeout, follow_redirects=True, transport=transport,
                                  headers={"Accept": "application/json", "User-Agent": USER_AGENT})
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
