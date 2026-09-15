import asyncio
from typing import Dict, List, Set
from growx_crawl.events.models import CrawlEvent


class CrawlEventBroadcaster:
    _subscribers: Dict[str, Set[asyncio.Queue]] = {}
    _recent_events: Dict[str, List[CrawlEvent]] = {}

    @classmethod
    def subscribe(cls, job_id: str) -> asyncio.Queue:
        if job_id not in cls._subscribers:
            cls._subscribers[job_id] = set()
        queue: asyncio.Queue = asyncio.Queue()
        cls._subscribers[job_id].add(queue)
        return queue

    @classmethod
    def unsubscribe(cls, job_id: str, queue: asyncio.Queue):
        if job_id in cls._subscribers:
            cls._subscribers[job_id].discard(queue)
            if not cls._subscribers[job_id]:
                del cls._subscribers[job_id]

    @classmethod
    def publish(cls, event: CrawlEvent):
        job_id = event.job_id
        if job_id not in cls._recent_events:
            cls._recent_events[job_id] = []
        cls._recent_events[job_id].append(event)
        # Retain last 50 events
        if len(cls._recent_events[job_id]) > 50:
            cls._recent_events[job_id] = cls._recent_events[job_id][-50:]

        if job_id in cls._subscribers:
            for queue in list(cls._subscribers[job_id]):
                try:
                    queue.put_nowait(event)
                except Exception:
                    pass

    @classmethod
    def get_recent_events(cls, job_id: str) -> List[CrawlEvent]:
        return cls._recent_events.get(job_id, [])
