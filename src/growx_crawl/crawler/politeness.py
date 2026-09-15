import asyncio
import time
from typing import Dict


class DomainPolitenessManager:
    def __init__(
        self,
        max_concurrency_per_domain: int = 2,
        delay_seconds: float = 0.5,
    ):
        self.max_concurrency_per_domain = max_concurrency_per_domain
        self.delay_seconds = delay_seconds
        self._semaphores: Dict[str, asyncio.Semaphore] = {}
        self._last_request_time: Dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def get_semaphore(self, domain: str) -> asyncio.Semaphore:
        async with self._lock:
            if domain not in self._semaphores:
                self._semaphores[domain] = asyncio.Semaphore(
                    self.max_concurrency_per_domain
                )
            return self._semaphores[domain]

    async def throttle(self, domain: str):
        sem = await self.get_semaphore(domain)
        await sem.acquire()
        try:
            now = time.monotonic()
            last_time = self._last_request_time.get(domain, 0.0)
            elapsed = now - last_time
            if elapsed < self.delay_seconds:
                await asyncio.sleep(self.delay_seconds - elapsed)
            self._last_request_time[domain] = time.monotonic()
        finally:
            sem.release()
