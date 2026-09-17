"""
Base persistent worker implementation for GrowX.
Handles worker lifecycle, continuous heartbeat loop, atomic job claiming, and graceful shutdown.
"""

import asyncio
import logging
import os
import signal
import socket
import sys
from typing import Any, Dict, List, Optional

from growx_crawl.jobs.models import JobEntity, WorkerType
from growx_crawl.jobs.queue import JobQueueService, job_queue_service
from growx_crawl.shared.ids import generate_id

logger = logging.getLogger("growx_crawl.workers.base")


class BaseWorker:
    def __init__(
        self,
        worker_type: WorkerType,
        accepted_job_types: List[str],
        worker_id: Optional[str] = None,
        queue_service: Optional[JobQueueService] = None,
        poll_interval: float = 2.0,
        lease_seconds: int = 300,
        heartbeat_interval: float = 20.0,
    ):
        self.worker_type = worker_type
        self.accepted_job_types = accepted_job_types
        self.worker_id = worker_id or generate_id("wrk")
        self.queue = queue_service or job_queue_service
        self.poll_interval = poll_interval
        self.lease_seconds = lease_seconds
        self.heartbeat_interval = heartbeat_interval
        self.is_running = False
        self.hostname = socket.gethostname()
        self.pid = os.getpid()
        self._current_job: Optional[JobEntity] = None
        self._heartbeat_task: Optional[asyncio.Task] = None

    def handle_signal(self, sig=None, frame=None):
        logger.info(f"[WORKER {self.worker_id}] Received shutdown signal ({sig}). Draining...")
        self.is_running = False

    async def start(self):
        """Main worker process loop."""
        self.is_running = True
        loop = asyncio.get_running_loop()
        for s in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(s, self.handle_signal)
            except (NotImplementedError, RuntimeError):
                pass  # Windows compatibility fallback

        # Register worker in registry
        self.queue.register_worker(
            worker_id=self.worker_id,
            worker_type=self.worker_type.value if isinstance(self.worker_type, WorkerType) else str(self.worker_type),
            hostname=self.hostname,
            process_id=self.pid,
            version="1.0.0",
        )
        logger.info(f"[WORKER {self.worker_id}] Started {self.worker_type} worker (PID {self.pid}) accepting {self.accepted_job_types}")

        try:
            while self.is_running:
                # Periodic maintenance: heartbeat worker registration & reclaim expired leases
                self.queue.heartbeat_worker(self.worker_id, current_job_id=self._current_job.id if self._current_job else None)
                self.queue.reclaim_expired_leases()
                self.queue.reap_dead_workers()

                # Attempt to claim next job
                job = self.queue.claim(
                    worker_id=self.worker_id,
                    accepted_types=self.accepted_job_types,
                    lease_seconds=self.lease_seconds,
                )

                if not job:
                    await asyncio.sleep(self.poll_interval)
                    continue

                self._current_job = job
                logger.info(f"[WORKER {self.worker_id}] Processing job {job.id} ({job.job_type})")

                # Launch background job heartbeat task
                self._heartbeat_task = asyncio.create_task(self._maintain_job_heartbeat(job.id))

                try:
                    result = await self.process_job(job)
                    self.queue.complete(job.id, self.worker_id, result)
                except Exception as e:
                    logger.error(f"[WORKER {self.worker_id}] Error processing job {job.id}: {e}", exc_info=True)
                    self.queue.fail(job.id, self.worker_id, str(e), can_retry=True)
                finally:
                    if self._heartbeat_task and not self._heartbeat_task.done():
                        self._heartbeat_task.cancel()
                    self._current_job = None

        finally:
            logger.info(f"[WORKER {self.worker_id}] Stopped cleanly.")

    async def _maintain_job_heartbeat(self, job_id: str):
        """Continuously renews the lease while the task is executing."""
        try:
            while self.is_running and self._current_job and self._current_job.id == job_id:
                await asyncio.sleep(self.heartbeat_interval)
                self.queue.heartbeat(job_id, self.worker_id, lease_seconds=self.lease_seconds)
                self.queue.heartbeat_worker(self.worker_id, current_job_id=job_id)
        except asyncio.CancelledError:
            pass

    async def process_job(self, job: JobEntity) -> Dict[str, Any]:
        """Override in subclasses to implement job execution."""
        raise NotImplementedError("Subclasses must implement process_job")
