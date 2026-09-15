import asyncio
import signal
from typing import Awaitable, Callable, List, TypeVar

T = TypeVar("T")


class AsyncWorkerPool:
    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.semaphore = asyncio.Semaphore(max_workers)
        self.is_cancelled = False
        self._active_tasks: List[asyncio.Task] = []

    def handle_shutdown(self, signum=None, frame=None):
        self.is_cancelled = True
        for task in self._active_tasks:
            if not task.done():
                task.cancel()

    async def map(
        self,
        worker_func: Callable[[T], Awaitable[None]],
        items: List[T],
    ) -> None:
        loop = asyncio.get_running_loop()
        try:
            loop.add_signal_handler(signal.SIGINT, self.handle_shutdown)
            loop.add_signal_handler(signal.SIGTERM, self.handle_shutdown)
        except (NotImplementedError, RuntimeError):
            # Signal handlers might not be supported on Windows main thread loop in all contexts
            pass

        async def worker_wrapper(item: T):
            if self.is_cancelled:
                return
            async with self.semaphore:
                if self.is_cancelled:
                    return
                try:
                    await worker_func(item)
                except asyncio.CancelledError:
                    self.is_cancelled = True
                except Exception:
                    pass

        tasks = [asyncio.create_task(worker_wrapper(item)) for item in items]
        self._active_tasks = tasks
        await asyncio.gather(*tasks, return_exceptions=True)
