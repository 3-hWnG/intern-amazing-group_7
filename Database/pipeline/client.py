"""Lớp mạng DUY NHẤT của pipeline. Mọi request ra ngoài đều đi qua đây.

Nguồn là API JSON của Cổng DVC Quốc gia, KHÔNG phải HTML — cổng đã là React SPA,
HTML trả về chỉ có <div id="root"></div>. Xem PHASE1_PLAN.md §2.

Nguyên tắc:
  · retry + backoff cho 429/500/502/503/504
  · rate-limit mặc định 2 req/s, MỘT luồng — đây là cổng nhà nước, không đập
  · timeout rõ ràng, không treo vô hạn
  · TLS verify LUÔN BẬT
"""

from __future__ import annotations

import logging
import random
import threading
import time

import httpx

BASE_URL = "https://dichvucong.gov.vn/api/v1"

# Endpoint tìm được bằng cách đọc ngược JS bundle của cổng (xem PHASE1_PLAN.md).
EP_CATALOG = "/submitting/formality/list-all-public-formality-by-citizen"
EP_DETAIL = "/configuring/formality/get-formality-by-citizen"
EP_ATTACHMENT = "/submitting/preview-attachment"

RETRY_STATUS = {429, 500, 502, 503, 504}

log = logging.getLogger("pipeline.client")


class RateLimiter:
    """Chặn tốc độ đơn giản, an toàn khi nhiều luồng (hiện dùng 1 luồng)."""

    def __init__(self, rps: float) -> None:
        self._min_gap = 1.0 / rps if rps > 0 else 0.0
        self._lock = threading.Lock()
        self._last = 0.0

    def wait(self) -> None:
        with self._lock:
            gap = time.monotonic() - self._last
            if gap < self._min_gap:
                time.sleep(self._min_gap - gap)
            self._last = time.monotonic()


class DvcClient:
    """Client cho dichvucong.gov.vn. Dùng như context manager."""

    def __init__(
        self,
        rps: float = 2.0,
        timeout: float = 40.0,
        max_retries: int = 4,
        user_agent: str | None = None,
    ) -> None:
        self._limiter = RateLimiter(rps)
        self._max_retries = max_retries
        self._client = httpx.Client(
            base_url=BASE_URL,
            timeout=timeout,
            follow_redirects=True,
            headers={
                "Content-Type": "application/json; charset=UTF-8",
                "Accept": "application/json;odata=verbose",
                "Origin": "https://dichvucong.gov.vn",
                "Referer": "https://dichvucong.gov.vn/",
                # Nói rõ mình là ai. Đây là project sinh viên, không giấu danh tính.
                "User-Agent": user_agent
                or ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "ThuTucHanhChinh-StudentProject/1.0 (+nhom7; research use)"),
            },
        )

    # -- vòng đời -----------------------------------------------------------
    def __enter__(self) -> "DvcClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    # -- lõi ----------------------------------------------------------------
    def _request(self, path: str, payload: dict) -> httpx.Response:
        """POST có retry. Ném exception nếu hết lượt thử."""
        last_err: Exception | None = None
        for attempt in range(self._max_retries + 1):
            self._limiter.wait()
            try:
                resp = self._client.post(path, json=payload)
            except httpx.RequestError as exc:          # lỗi mạng / timeout
                last_err = exc
            else:
                if resp.status_code not in RETRY_STATUS:
                    resp.raise_for_status()
                    return resp
                last_err = httpx.HTTPStatusError(
                    f"HTTP {resp.status_code}", request=resp.request, response=resp)
                # Cổng bảo chờ bao lâu thì chờ đúng bấy nhiêu.
                retry_after = resp.headers.get("Retry-After")
                if retry_after and retry_after.isdigit():
                    time.sleep(min(int(retry_after), 60))
                    continue

            if attempt < self._max_retries:
                # backoff luỹ thừa + jitter để nhiều tiến trình không dồn cùng lúc
                delay = min(2.0 ** attempt, 30.0) + random.uniform(0, 0.5)
                log.warning("thử lại %s sau %.1fs (lần %d/%d): %s",
                            path, delay, attempt + 1, self._max_retries, last_err)
                time.sleep(delay)

        raise RuntimeError(f"thất bại sau {self._max_retries + 1} lần: {path}") from last_err

    def post_json(self, path: str, payload: dict) -> dict:
        """POST và trả về phần `data`. Ném lỗi nếu cổng báo code != OK."""
        body = self._request(path, payload).json()
        if body.get("code") not in ("OK", None):
            raise RuntimeError(f"API trả về {body.get('code')}: {body.get('message')}")
        return body.get("data") or {}

    # -- API cụ thể ---------------------------------------------------------
    def list_catalog_page(
        self,
        last_id: str = "",
        limit: int = 20,
        department_code: str = "",
        category_id: str = "",
        query: str = "",
        level: str = "",
    ) -> dict:
        """Một trang danh mục. Phân trang bằng con trỏ `lastId`, không phải số trang.

        `level` = cấp thực hiện: COMMUNE (xã/phường) · PROVINCE · MINISTRY.
        Đã kiểm chứng: level="COMMUNE" tương đương cờ isWard trong chi tiết
        (402/402 khớp), cho 1.313 thủ tục toàn quốc.
        """
        body = {
            "limit": limit,
            "lastId": last_id,
            "q": query,
            "categoryId": category_id,
            "departmentCode": department_code,
        }
        if level:
            body["level"] = level
        return self.post_json(EP_CATALOG, body)

    def get_detail(self, formality_id: str) -> dict:
        """Chi tiết đầy đủ của một thủ tục."""
        return self.post_json(EP_DETAIL, {"id": formality_id})

    def download_attachment(self, file_id: str) -> tuple[bytes, str]:
        """Tải một tệp đính kèm. Trả về (nội dung, content-type).

        LƯU Ý: tệp KHÔNG có URL công khai tĩnh — bắt buộc POST kèm fileId.
        Vì vậy UI không thể trỏ thẳng <a href> sang cổng; ETL phải tải về.
        """
        resp = self._request(EP_ATTACHMENT, {"fileId": file_id})
        return resp.content, resp.headers.get("content-type", "")
