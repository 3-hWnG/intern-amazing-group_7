"""Hàng đợi xử lý tuần tự, VẪN giữ được hiệu ứng gõ chữ.

Mentor yêu cầu xử lý 1-1; đồng đội lo khó dùng. Cách giải: worker giữ quyền gọi
LLM, nhưng đẩy từng mẩu chữ về cho request qua một hàng đợi riêng -> người dùng
vẫn thấy chữ hiện dần, chỉ là phải chờ tới lượt. Kèm vị trí trong hàng đợi để
người dùng biết còn bao lâu thay vì nhìn màn hình trắng.

Đổi QUEUE_CONCURRENCY trong config để chạy song song.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Callable

from config import QUEUE_CONCURRENCY, QUEUE_JOB_TIMEOUT, QUEUE_MAX_DEPTH

_DONE = object()      # sentinel báo hết luồng chữ


class QueueFull(Exception):
    pass


@dataclass
class Job:
    producer: Callable[[Callable[[str], None]], None]   # hàm ĐỒNG BỘ, nhận emit()
    out: asyncio.Queue = field(default_factory=asyncio.Queue)
    enqueued_at: float = field(default_factory=time.time)
    started_at: float = 0.0
    finished_at: float = 0.0
    position: int = 0
    error: str = ""


class QueueManager:
    def __init__(self, concurrency: int = QUEUE_CONCURRENCY,
                 max_depth: int = QUEUE_MAX_DEPTH,
                 job_timeout: int = QUEUE_JOB_TIMEOUT):
        self.concurrency = max(1, int(concurrency))
        self.max_depth = max(1, int(max_depth))
        self.job_timeout = job_timeout
        self._queue: asyncio.Queue[Job] = asyncio.Queue()
        self._workers: list[asyncio.Task] = []
        self._running = False

    # ---------------------------------------------------------- vòng đời --
    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._workers = [asyncio.create_task(self._worker(i))
                         for i in range(self.concurrency)]

    async def stop(self) -> None:
        self._running = False
        for w in self._workers:
            w.cancel()
        self._workers.clear()

    @property
    def depth(self) -> int:
        return self._queue.qsize()

    # ------------------------------------------------------------- gửi ----
    def submit(self, producer) -> Job:
        """Đẩy job vào hàng. Trả về Job để gọi stream()."""
        if self._queue.qsize() >= self.max_depth:
            raise QueueFull("Hệ thống đang quá tải, vui lòng thử lại sau ít phút.")
        job = Job(producer=producer)
        job.position = self._queue.qsize()
        self._queue.put_nowait(job)
        return job

    async def stream(self, job: Job):
        """Đọc từng mẩu chữ của job cho tới khi kết thúc."""
        while True:
            chunk = await job.out.get()
            if chunk is _DONE:
                break
            yield chunk

    # ---------------------------------------------------------- worker ----
    async def _worker(self, index: int) -> None:
        loop = asyncio.get_running_loop()
        while self._running:
            try:
                job = await self._queue.get()
            except asyncio.CancelledError:
                return

            job.started_at = time.time()

            def emit(chunk: str, _job=job) -> None:
                """Gọi từ luồng khác -> phải đẩy qua loop cho an toàn."""
                loop.call_soon_threadsafe(_job.out.put_nowait, chunk)

            try:
                await asyncio.wait_for(
                    asyncio.to_thread(job.producer, emit),
                    timeout=self.job_timeout,
                )
            except asyncio.TimeoutError:
                job.error = "timeout"
                loop.call_soon_threadsafe(
                    job.out.put_nowait,
                    "\n\n[Hệ thống xử lý quá lâu, vui lòng thử lại.]")
            except asyncio.CancelledError:
                return
            except Exception as exc:
                job.error = str(exc)
                loop.call_soon_threadsafe(
                    job.out.put_nowait, f"\n\n[Lỗi xử lý: {exc}]")
            finally:
                job.finished_at = time.time()
                loop.call_soon_threadsafe(job.out.put_nowait, _DONE)
                self._queue.task_done()


# Một thể hiện dùng chung toàn ứng dụng.
manager = QueueManager()
