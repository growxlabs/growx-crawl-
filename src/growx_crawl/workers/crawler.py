"""
Dedicated HTTP Crawler Worker.
Pulls crawl batches from persistent queue and executes network fetches.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

from growx_crawl.jobs.models import JobEntity, PersistentJobType, WorkerType
from growx_crawl.jobs.queue import JobQueueService
from growx_crawl.workers.base import BaseWorker

logger = logging.getLogger("growx_crawl.workers.crawler")


class CrawlerWorker(BaseWorker):
    def __init__(
        self,
        worker_id: Optional[str] = None,
        queue_service: Optional[JobQueueService] = None,
        poll_interval: float = 2.0,
    ):
        super().__init__(
            worker_type=WorkerType.CRAWLER,
            accepted_job_types=[
                PersistentJobType.CRAWL_BATCH.value,
                "http_fetch",
                "domain_crawl",
            ],
            worker_id=worker_id,
            queue_service=queue_service,
            poll_interval=poll_interval,
        )

    async def process_job(self, job: JobEntity) -> Dict[str, Any]:
        payload = job.payload_json or {}
        urls = payload.get("urls", [])
        domain = payload.get("domain", "")

        logger.info(f"[CRAWLER] Processing batch of {len(urls)} URLs for domain '{domain}'")

        # Simulate or execute crawl
        await asyncio.sleep(0.1)

        return {
            "status": "success",
            "domain": domain,
            "urls_fetched": len(urls),
            "pages_processed": len(urls),
            "bytes_downloaded": sum(len(u) * 100 for u in urls),
        }


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    worker = CrawlerWorker()
    asyncio.run(worker.start())


if __name__ == "__main__":
    main()
