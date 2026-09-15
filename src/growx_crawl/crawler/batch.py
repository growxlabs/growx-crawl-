import asyncio
from datetime import datetime, timezone
import json
import time
from typing import Any, Dict, List, Optional
import uuid
import httpx

from growx_crawl.crawler.fetcher import fetcher_pipeline
from growx_crawl.crawler.robots import robots_engine
from growx_crawl.storage.db import get_db


class BatchJob:
    def __init__(
        self,
        batch_id: str,
        urls: List[str],
        respect_robots: bool = False,
        webhook_url: Optional[str] = None,
    ):
        self.batch_id = batch_id
        self.total_urls = len(urls)
        self.urls = urls[:100]  # Cap at 100
        self.respect_robots = respect_robots
        self.webhook_url = webhook_url
        self.status = "processing"
        self.completed_count = 0
        self.results: List[Dict[str, Any]] = []
        self.created_at = time.time()
        self.completed_at: Optional[float] = None


class BatchScraper:
    """
    Capability 4: Batch Scraping up to 100 URLs in parallel with durable SQLite persistence,
    robots.txt compliance, async polling, and webhook dispatch.
    """

    def __init__(self):
        self.jobs: Dict[str, BatchJob] = {}

    def create_batch(
        self,
        urls: List[str],
        respect_robots: bool = False,
        webhook_url: Optional[str] = None,
    ) -> BatchJob:
        batch_id = f"batch_{uuid.uuid4().hex[:8]}"
        job = BatchJob(
            batch_id=batch_id,
            urls=urls,
            respect_robots=respect_robots,
            webhook_url=webhook_url,
        )
        self.jobs[batch_id] = job

        # Persist to SQLite
        try:
            now_iso = datetime.now(timezone.utc).isoformat()
            with get_db() as conn:
                conn.execute(
                    """
                    INSERT INTO batch_jobs (
                        id, total_urls, completed_count, status, webhook_url, results, created_at
                    ) VALUES (?, ?, 0, 'processing', ?, '[]', ?)
                    """,
                    (batch_id, job.total_urls, webhook_url, now_iso),
                )
        except Exception:
            pass

        return job

    def get_batch(self, batch_id: str) -> Optional[BatchJob]:
        # In-memory check
        if batch_id in self.jobs:
            return self.jobs[batch_id]

        # SQLite fallback across restarts
        try:
            with get_db() as conn:
                row = conn.execute("SELECT * FROM batch_jobs WHERE id = ?", (batch_id,)).fetchone()
                if not row:
                    return None

                job = BatchJob(
                    batch_id=row["id"],
                    urls=[],
                    webhook_url=row["webhook_url"],
                )
                job.total_urls = row["total_urls"]
                job.completed_count = row["completed_count"]
                job.status = row["status"]
                job.results = json.loads(row["results"]) if row["results"] else []
                self.jobs[batch_id] = job
                return job
        except Exception:
            return None

    def list_batches(self, limit: int = 20) -> List[Dict[str, Any]]:
        try:
            with get_db() as conn:
                rows = conn.execute(
                    """
                    SELECT id, total_urls, completed_count, status, created_at, completed_at
                    FROM batch_jobs
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
                if rows:
                    return [
                        {
                            "batch_id": r["id"],
                            "total_urls": r["total_urls"],
                            "completed_count": r["completed_count"],
                            "status": r["status"],
                            "created_at": r["created_at"],
                            "completed_at": r["completed_at"],
                        }
                        for r in rows
                    ]
        except Exception:
            pass

        return [
            {
                "batch_id": j.batch_id,
                "total_urls": j.total_urls,
                "completed_count": j.completed_count,
                "status": j.status,
                "created_at": j.created_at,
            }
            for j in list(self.jobs.values())[:limit]
        ]

    async def execute_batch(self, batch_id: str, concurrency: int = 10) -> None:
        job = self.get_batch(batch_id)
        if not job:
            return

        semaphore = asyncio.Semaphore(min(concurrency, 25))

        async def worker(url: str):
            async with semaphore:
                if job.respect_robots:
                    allowed = await robots_engine.can_fetch(url)
                    if not allowed:
                        job.results.append({
                            "url": url,
                            "status": 403,
                            "error": "Blocked by robots.txt compliance rule",
                        })
                        job.completed_count += 1
                        return

                try:
                    res = await fetcher_pipeline.fetch_fast(url, timeout=20)
                    job.results.append({
                        "url": url,
                        "status": res.status_code,
                        "latency_ms": res.latency_ms,
                        "content_length": len(res.html),
                    })
                except Exception as e:
                    job.results.append({"url": url, "status": 500, "error": str(e)})
                finally:
                    job.completed_count += 1

        tasks = [worker(u) for u in job.urls]
        await asyncio.gather(*tasks, return_exceptions=True)
        job.status = "completed"
        job.completed_at = time.time()
        now_iso = datetime.now(timezone.utc).isoformat()

        # Update SQLite
        try:
            with get_db() as conn:
                conn.execute(
                    """
                    UPDATE batch_jobs
                    SET status = 'completed', completed_count = ?, results = ?, completed_at = ?
                    WHERE id = ?
                    """,
                    (job.completed_count, json.dumps(job.results), now_iso, batch_id),
                )
        except Exception:
            pass

        if job.webhook_url:
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    await client.post(
                        job.webhook_url,
                        json={
                            "event": "batch.completed",
                            "batch_id": job.batch_id,
                            "total_urls": job.total_urls,
                            "completed": job.completed_count,
                        },
                    )
            except Exception:
                pass


batch_scraper = BatchScraper()
