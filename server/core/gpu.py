"""Bộ lập lịch GPU chung cho System 3 (Strict) và System 4 (Friendly) — G3.1 (P13, P14, D15).

Card 6 GB chỉ chạy một lời gọi model tại một thời điểm, nên MỌI lời gọi LLM của cả hai hệ xin một "chỗ" ở đây; phần luật
(tìm thủ tục, ghép câu trả lời bằng code, tìm web qua mạng) KHÔNG xin chỗ nên chạy song song, không phải chờ lượt LLM của người khác.

Ưu tiên (số nhỏ được phục vụ trước; cùng mức thì đến trước phục vụ trước):
  P_SHORT lời gọi NGẮN người dùng đang chờ: bước sinh chữ của Strict (~1–2,4 s, trần 200 token). Đi trước câu Friendly dài
          (5–14 s) — đo tải 10 người (G3.4): xếp cùng mức thì 13/20 lượt Strict chờ hết 7 s rồi mới trả bản code
  P0 câu trả lời người dùng đang chờ (Friendly, tìm web của Strict)
  P1 việc phụ trợ khi đang tương tác (công cụ bảng, phòng thử của dev)
  P2 việc nền: bộ nhớ, tóm tắt hội thoại
  P3 nạp tệp dữ liệu (kiểm tiêu đề bằng LLM, tạo vector)
Không giành chỗ đang chạy (không ngắt lời gọi dở); chỉ quyết định ai được vào tiếp theo.

Số chỗ: S4_CONCURRENCY / S3_QUEUE_CONCURRENCY (lấy số lớn hơn, mặc định 1). Card lớn + OLLAMA_NUM_PARALLEL=N thì đặt N.
Dùng: `with gpu.slot(gpu.P0, timeout=7): ...` (luồng thường) hoặc `async with gpu.aslot(gpu.P0): ...` (async).
Vị trí xếp hàng tính chung cả hai hệ: gpu.position(prio)."""
from __future__ import annotations

import asyncio
import heapq
import itertools
import os
import threading
import time
from contextlib import asynccontextmanager, contextmanager

P_SHORT, P0, P1, P2, P3 = -1, 0, 1, 2, 3


class Busy(TimeoutError):
    """Chờ quá hạn mà chưa tới lượt dùng GPU."""


def _slots() -> int:
    vals = [os.environ.get("S4_CONCURRENCY"), os.environ.get("S3_QUEUE_CONCURRENCY")]
    return max([1] + [int(v) for v in vals if v and v.strip().isdigit()])


class Scheduler:
    def __init__(self, slots: int | None = None):
        self.slots = max(1, slots or _slots())
        self._lock = threading.Lock()
        self._busy = 0
        self._heap: list = []          # (prio, seq, ticket)
        self._seq = itertools.count()
        self.served = {P_SHORT: 0, P0: 0, P1: 0, P2: 0, P3: 0}

    # ------------------------------------------------------------ thông tin
    def position(self, prio: int = P0) -> int:
        """Số lượt sẽ được phục vụ trước một người MỚI đến với mức ưu tiên prio (đang chạy + đang chờ cùng/cao hơn)."""
        with self._lock:
            ahead = sum(1 for p, _, t in self._heap if p <= prio and not t["dead"])
            return max(0, self._busy - self.slots + 1) + ahead if self._busy >= self.slots else ahead

    def state(self) -> dict:
        with self._lock:
            return {"slots": self.slots, "busy": self._busy, "waiting": [p for p, _, t in sorted(self._heap) if not t["dead"]],
                    "served": dict(self.served)}

    # ------------------------------------------------------------ cấp / trả
    def _try_take(self, prio: int, ticket: dict) -> bool:
        """Gọi khi giữ _lock. Được vào nếu còn chỗ và không ai ưu tiên hơn (hoặc cùng mức mà đến trước) đang chờ."""
        while self._heap and self._heap[0][2]["dead"]:
            heapq.heappop(self._heap)
        if self._busy < self.slots and (not self._heap or self._heap[0][2] is ticket):
            if self._heap and self._heap[0][2] is ticket:
                heapq.heappop(self._heap)
            self._busy += 1
            self.served[prio] = self.served.get(prio, 0) + 1
            return True
        return False

    def _wake(self) -> None:
        """Gọi khi giữ _lock: báo người đứng đầu hàng (nếu còn chỗ)."""
        while self._heap and self._heap[0][2]["dead"]:
            heapq.heappop(self._heap)
        if self._busy < self.slots and self._heap:
            t = self._heap[0][2]
            if t["event"] is not None:
                t["event"].set()
            else:
                loop, fut = t["loop"], t["future"]
                loop.call_soon_threadsafe(lambda f=fut: f.done() or f.set_result(True))

    def release(self) -> None:
        with self._lock:
            self._busy = max(0, self._busy - 1)
            self._wake()

    def acquire(self, prio: int = P0, timeout: float | None = None) -> None:
        """Chờ tới lượt (luồng thường). Quá `timeout` giây -> Busy."""
        ticket = {"dead": False, "event": threading.Event(), "loop": None, "future": None}
        deadline = None if timeout is None else time.monotonic() + timeout
        with self._lock:
            if not self._heap and self._try_take(prio, ticket):
                return
            heapq.heappush(self._heap, (prio, next(self._seq), ticket))
        while True:
            with self._lock:
                if self._try_take(prio, ticket):
                    return
                ticket["event"].clear()
            left = None if deadline is None else deadline - time.monotonic()
            if left is not None and left <= 0:
                with self._lock:
                    ticket["dead"] = True
                    self._wake()
                raise Busy("GPU đang bận")
            ticket["event"].wait(left if left is not None else 1.0)

    async def acquire_async(self, prio: int = P0, timeout: float | None = None) -> None:
        loop = asyncio.get_running_loop()
        ticket = {"dead": False, "event": None, "loop": loop, "future": None}
        deadline = None if timeout is None else time.monotonic() + timeout
        with self._lock:
            if not self._heap and self._try_take(prio, ticket):
                return
            heapq.heappush(self._heap, (prio, next(self._seq), ticket))
        try:
            while True:
                with self._lock:
                    if self._try_take(prio, ticket):
                        return
                    ticket["future"] = loop.create_future()
                left = None if deadline is None else deadline - time.monotonic()
                if left is not None and left <= 0:
                    raise Busy("GPU đang bận")
                try:
                    await asyncio.wait_for(ticket["future"], left if left is not None else 1.0)
                except asyncio.TimeoutError:
                    pass
        except BaseException:   # quá hạn / người dùng rời trang: bỏ vé, nhường chỗ cho người sau
            with self._lock:
                ticket["dead"] = True
                self._wake()
            raise

    @contextmanager
    def slot(self, prio: int = P0, timeout: float | None = None):
        self.acquire(prio, timeout)
        try:
            yield
        finally:
            self.release()

    @asynccontextmanager
    async def aslot(self, prio: int = P0, timeout: float | None = None):
        await self.acquire_async(prio, timeout)
        try:
            yield
        finally:
            self.release()


scheduler = Scheduler()
slot, aslot, position, state = scheduler.slot, scheduler.aslot, scheduler.position, scheduler.state
