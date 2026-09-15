import asyncio
from datetime import datetime, timezone
import json
import time
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse
import uuid
from bs4 import BeautifulSoup
import httpx

from growx_crawl.crawler.fetcher import fetcher_pipeline
from growx_crawl.crawler.robots import robots_engine
from growx_crawl.crawler.scraper import ensure_base_href
from growx_crawl.storage.db import get_db


class MultiPageCrawlJob:
    def __init__(
        self,
        job_id: str,
        seed_url: str,
        max_depth: int = 5,
        max_pages: int = 50,
        respect_robots: bool = False,
        webhook_url: Optional[str] = None,
    ):
        self.job_id = job_id
        self.seed_url = seed_url
        self.max_depth = min(max_depth, 5)
        self.max_pages = min(max_pages, 50)
        self.respect_robots = respect_robots
        self.webhook_url = webhook_url
        self.status = "queued"
        self.pages_crawled = 0
        self.pages: List[Dict[str, Any]] = []
        self.errors: List[str] = []
        self.created_at = time.time()
        self.completed_at: Optional[float] = None


class MultiPageCrawler:
    """
    Capability 3: Multi-Page Crawl (up to 50 pages, 5 levels deep) with durable SQLite
    job persistence, robots.txt compliance, async polling, and target snapshots.
    """

    def __init__(self):
        self.jobs: Dict[str, MultiPageCrawlJob] = {}

    def create_job(
        self,
        seed_url: str,
        max_depth: int = 5,
        max_pages: int = 50,
        respect_robots: bool = False,
        webhook_url: Optional[str] = None,
    ) -> MultiPageCrawlJob:
        job_id = f"crawljobs_{uuid.uuid4().hex[:8]}"
        job = MultiPageCrawlJob(
            job_id=job_id,
            seed_url=seed_url,
            max_depth=max_depth,
            max_pages=max_pages,
            respect_robots=respect_robots,
            webhook_url=webhook_url,
        )
        self.jobs[job_id] = job

        # Persist to SQLite
        try:
            now_iso = datetime.now(timezone.utc).isoformat()
            config_json = json.dumps({
                "max_depth": job.max_depth,
                "max_pages": job.max_pages,
                "respect_robots": job.respect_robots,
                "webhook_url": job.webhook_url,
            })
            with get_db() as conn:
                conn.execute(
                    """
                    INSERT INTO crawl_jobs (
                        id, query, status, configuration, created_at
                    ) VALUES (?, ?, 'queued', ?, ?)
                    """,
                    (job_id, seed_url, config_json, now_iso),
                )
        except Exception:
            pass

        return job

    def get_job(self, job_id: str) -> Optional[MultiPageCrawlJob]:
        # Check in-memory cache first
        if job_id in self.jobs:
            return self.jobs[job_id]

        # Check SQLite persistence
        try:
            with get_db() as conn:
                row = conn.execute("SELECT * FROM crawl_jobs WHERE id = ?", (job_id,)).fetchone()
                if not row:
                    return None

                config = json.loads(row["configuration"]) if row["configuration"] else {}
                job = MultiPageCrawlJob(
                    job_id=row["id"],
                    seed_url=row["query"],
                    max_depth=config.get("max_depth", 5),
                    max_pages=config.get("max_pages", 50),
                    respect_robots=config.get("respect_robots", False),
                    webhook_url=config.get("webhook_url"),
                )
                job.status = row["status"]
                job.pages_crawled = row["processed_count"] or 0

                # Load targets/pages
                p_rows = conn.execute(
                    "SELECT target_id, url, title, status_code FROM pages WHERE job_id = ?",
                    (job_id,),
                ).fetchall()
                job.pages = [
                    {
                        "target_id": r["target_id"],
                        "url": r["url"],
                        "title": r["title"] or "",
                        "status": r["status_code"],
                    }
                    for r in p_rows
                ]

                # Cache in memory
                self.jobs[job_id] = job
                return job
        except Exception:
            return None

    def list_jobs(self, limit: int = 20) -> List[Dict[str, Any]]:
        # Query SQLite for full history across restarts
        try:
            with get_db() as conn:
                rows = conn.execute(
                    """
                    SELECT id, query, status, processed_count, created_at, started_at, finished_at
                    FROM crawl_jobs
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
                if rows:
                    return [
                        {
                            "job_id": r["id"],
                            "seed_url": r["query"],
                            "status": r["status"],
                            "pages_crawled": r["processed_count"] or 0,
                            "created_at": r["created_at"],
                            "started_at": r["started_at"],
                            "finished_at": r["finished_at"],
                        }
                        for r in rows
                    ]
        except Exception:
            pass

        # In-memory fallback
        sorted_jobs = sorted(self.jobs.values(), key=lambda j: j.created_at, reverse=True)[:limit]
        return [
            {
                "job_id": j.job_id,
                "seed_url": j.seed_url,
                "status": j.status,
                "pages_crawled": j.pages_crawled,
                "created_at": j.created_at,
                "duration_seconds": (j.completed_at - j.created_at) if j.completed_at else None,
            }
            for j in sorted_jobs
        ]

    async def execute_crawl(self, job_id: str) -> None:
        job = self.get_job(job_id)
        if not job:
            return

        job.status = "running"
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            with get_db() as conn:
                conn.execute(
                    "UPDATE crawl_jobs SET status = 'running', started_at = ? WHERE id = ?",
                    (now_iso, job_id),
                )
        except Exception:
            pass

        domain = urlparse(job.seed_url).netloc
        queue: List[tuple[str, int]] = [(job.seed_url, 0)]
        visited: Set[str] = set()

        try:
            while queue and job.pages_crawled < job.max_pages:
                current_url, depth = queue.pop(0)
                if current_url in visited or depth > job.max_depth:
                    continue

                visited.add(current_url)

                # Check robots.txt compliance if requested
                if job.respect_robots:
                    allowed = await robots_engine.can_fetch(current_url)
                    if not allowed:
                        job.errors.append(f"Blocked by robots.txt: {current_url}")
                        continue

                try:
                    res = await fetcher_pipeline.fetch_fast(current_url, timeout=15)
                    if res.status_code == 200:
                        soup = BeautifulSoup(res.html, "html.parser")
                        title = soup.title.string.strip() if soup.title and soup.title.string else ""
                        text_content = " ".join(soup.get_text().split())
                        target_id = f"tgt_{uuid.uuid4().hex[:10]}"
                        page_id = f"page_{uuid.uuid4().hex[:10]}"
                        page_now = datetime.now(timezone.utc).isoformat()

                        # Persist target and page snapshot to SQLite
                        try:
                            with get_db() as conn:
                                conn.execute(
                                    """
                                    INSERT INTO crawl_targets (
                                        id, job_id, url, domain, status, depth,
                                        discovered_at, started_at, completed_at
                                    ) VALUES (?, ?, ?, ?, 'completed', ?, ?, ?, ?)
                                    """,
                                    (target_id, job.job_id, current_url, domain, depth, page_now, page_now, page_now),
                                )
                                conn.execute(
                                    """
                                    INSERT INTO pages (
                                        id, job_id, target_id, url, status_code,
                                        content_type, html_content, title, text_content, created_at
                                    ) VALUES (?, ?, ?, ?, ?, 'text/html', ?, ?, ?, ?)
                                    """,
                                    (
                                        page_id,
                                        job.job_id,
                                        target_id,
                                        current_url,
                                        res.status_code,
                                        ensure_base_href(res.html, current_url),
                                        title,
                                        text_content[:2000],
                                        page_now,
                                    ),
                                )
                                conn.execute(
                                    "UPDATE crawl_jobs SET processed_count = processed_count + 1 WHERE id = ?",
                                    (job.job_id,),
                                )
                        except Exception:
                            pass

                        # Real-time search engine indexing
                        try:
                            from growx_crawl.search.indexer import document_indexer
                            document_indexer.index_document(
                                target_id=target_id,
                                url=current_url,
                                html=res.html,
                                fallback_title=title,
                                timestamp=page_now,
                            )
                        except Exception:
                            pass

                        job.pages.append({
                            "target_id": target_id,
                            "url": current_url,
                            "depth": depth,
                            "title": title,
                            "status": res.status_code,
                            "latency_ms": res.latency_ms,
                        })
                        job.pages_crawled += 1

                        # Discover links within domain
                        if depth < job.max_depth:
                            for a in soup.find_all("a", href=True):
                                href = a["href"].strip()
                                abs_link = urljoin(current_url, href)
                                if urlparse(abs_link).netloc == domain and abs_link not in visited:
                                    queue.append((abs_link, depth + 1))
                except Exception as e:
                    job.errors.append(f"Failed {current_url}: {str(e)}")

            job.status = "completed"
        except Exception as e:
            job.status = "failed"
            job.errors.append(str(e))
        finally:
            job.completed_at = time.time()
            finish_iso = datetime.now(timezone.utc).isoformat()
            try:
                with get_db() as conn:
                    conn.execute(
                        "UPDATE crawl_jobs SET status = ?, finished_at = ?, processed_count = ? WHERE id = ?",
                        (job.status, finish_iso, job.pages_crawled, job.job_id),
                    )
            except Exception:
                pass

            # Dispatch webhook if provided
            if job.webhook_url:
                try:
                    async with httpx.AsyncClient(timeout=10) as client:
                        await client.post(
                            job.webhook_url,
                            json={
                                "event": "crawl.completed",
                                "job_id": job.job_id,
                                "pages_crawled": job.pages_crawled,
                                "status": job.status,
                            },
                        )
                except Exception:
                    pass


multi_page_crawler = MultiPageCrawler()
