"""queue_manager.py — Hàng đợi xử lý bất đồng bộ (Rate Limiting & Queue Position)."""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Tuple
import asyncio
import time
import uuid

from config import QUEUE_CONCURRENCY


@dataclass
class QueueJob:
    job_id: str
    func: Callable
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]
    future: asyncio.Future
    created_at: float = field(default_factory=time.time)


class RequestQueueManager:
    def __init__(self, concurrency: int = QUEUE_CONCURRENCY):
        self.concurrency = concurrency
        self.queue: asyncio.Queue[QueueJob] = asyncio.Queue()
        self.workers: list[asyncio.Task] = []
        self._running = False

    async def start(self):
        if self._running:
            return
        self._running = True
        for i in range(self.concurrency):
            t = asyncio.create_task(self._worker_loop(i))
            self.workers.append(t)

    async def stop(self):
        self._running = False
        for t in self.workers:
            t.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()

    async def _worker_loop(self, worker_id: int):
        while self._running:
            try:
                job = await self.queue.get()
            except asyncio.CancelledError:
                break
            try:
                if asyncio.iscoroutinefunction(job.func):
                    res = await job.func(*job.args, **job.kwargs)
                else:
                    loop = asyncio.get_running_loop()
                    res = await loop.run_in_executor(None, lambda: job.func(*job.args, **job.kwargs))
                if not job.future.done():
                    job.future.set_result(res)
            except Exception as e:
                if not job.future.done():
                    job.future.set_exception(e)
            finally:
                self.queue.task_done()

    async def enqueue(self, func: Callable, *args, **kwargs) -> Tuple[Any, int]:
        """Đưa tác vụ vào hàng đợi và trả về (kết_quả, vị_trí_ban_đầu)."""
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        job = QueueJob(
            job_id=str(uuid.uuid4()),
            func=func,
            args=args,
            kwargs=kwargs,
            future=future
        )
        current_pos = self.queue.qsize() + 1
        await self.queue.put(job)
        res = await future
        return res, current_pos


queue_manager = RequestQueueManager()
