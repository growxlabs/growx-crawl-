"""
Persistent Job Queue Service.
High-level service orchestrating job submission, atomic claims, worker leasing, and fault recovery.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional

from growx_crawl.jobs.models import (
    JobEntity,
    PersistentJobStatus,
    PersistentJobType,
    WorkerEntity,
    WorkerStatus,
    WorkerType,
)
from growx_crawl.jobs.repository import BaseJobRepository, SqliteJobRepository

logger = logging.getLogger("growx_crawl.jobs.queue")


class JobQueueService:
    def __init__(self, repository: Optional[BaseJobRepository] = None):
        self.repo = repository or SqliteJobRepository()

    def enqueue(
        self,
        job_type: str,
        payload: Optional[Dict[str, Any]] = None,
        priority: int = 50,
        max_retries: int = 3,
    ) -> JobEntity:
        """Submits a persistent task into the durable job queue."""
        job = JobEntity(
            job_type=job_type,
            priority=priority,
            payload_json=payload or {},
            max_retries=max_retries,
            status=PersistentJobStatus.QUEUED,
        )
        saved = self.repo.enqueue(job)
        logger.info(f"[JOB_QUEUE] Enqueued job {saved.id} (type={job_type}, priority={priority})")
        return saved

    def claim(
        self,
        worker_id: str,
        accepted_types: List[str],
        lease_seconds: int = 300,
    ) -> Optional[JobEntity]:
        """Atomically leases the highest-priority eligible job for the worker."""
        job = self.repo.claim_next(
            worker_id=worker_id,
            accepted_types=accepted_types,
            lease_seconds=lease_seconds,
        )
        if job:
            logger.debug(f"[JOB_QUEUE] Worker {worker_id} claimed job {job.id} ({job.job_type})")
        return job

    def heartbeat(self, job_id: str, worker_id: str, lease_seconds: int = 300) -> bool:
        """Renews the lease deadline for a currently executing job."""
        return self.repo.heartbeat_lease(job_id=job_id, worker_id=worker_id, lease_seconds=lease_seconds)

    def complete(self, job_id: str, worker_id: str, result: Optional[Dict[str, Any]] = None) -> Optional[JobEntity]:
        """Marks a job as successfully completed with its structured result artifact."""
        res = self.repo.complete(job_id=job_id, worker_id=worker_id, result=result or {})
        logger.info(f"[JOB_QUEUE] Job {job_id} completed successfully by worker {worker_id}")
        return res

    def fail(
        self,
        job_id: str,
        worker_id: str,
        reason: str,
        can_retry: bool = True,
    ) -> Optional[JobEntity]:
        """Marks a job as failed or retrying depending on remaining retry budget."""
        res = self.repo.fail(job_id=job_id, worker_id=worker_id, reason=reason, can_retry=can_retry)
        logger.warning(f"[JOB_QUEUE] Job {job_id} failed on worker {worker_id}: {reason} (status={res.status.value if res else 'unknown'})")
        return res

    def reclaim_expired_leases(self) -> int:
        """Scans for jobs whose worker lease expired without renewal and safely returns them to queue."""
        count = self.repo.reclaim_expired()
        if count > 0:
            logger.warning(f"[JOB_QUEUE] Reclaimed {count} abandoned job(s) from expired worker leases.")
        return count

    def get_job(self, job_id: str) -> Optional[JobEntity]:
        return self.repo.get(job_id)

    def list_jobs(
        self,
        status: Optional[PersistentJobStatus] = None,
        job_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[JobEntity]:
        return self.repo.list_jobs(status=status, job_type=job_type, limit=limit)

    def get_queue_depth(self) -> Dict[str, int]:
        return self.repo.get_queue_depth()

    # Worker Registry
    def register_worker(
        self,
        worker_id: str,
        worker_type: str,
        hostname: str = "localhost",
        process_id: Optional[int] = None,
        version: str = "1.0.0",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WorkerEntity:
        """Registers or refreshes an active worker process registration."""
        worker = WorkerEntity(
            id=worker_id,
            worker_type=worker_type,
            hostname=hostname,
            process_id=process_id,
            status=WorkerStatus.ACTIVE,
            version=version,
            metadata_json=metadata or {},
        )
        return self.repo.upsert_worker(worker)

    def heartbeat_worker(self, worker_id: str, current_job_id: Optional[str] = None) -> bool:
        return self.repo.heartbeat_worker(worker_id=worker_id, current_job_id=current_job_id)

    def reap_dead_workers(self, timeout_seconds: int = 90) -> int:
        return self.repo.reap_dead_workers(timeout_seconds=timeout_seconds)

    def list_workers(self, worker_type: Optional[str] = None) -> List[WorkerEntity]:
        return self.repo.list_workers(worker_type=worker_type)


job_queue_service = JobQueueService()

__all__ = [
    "JobQueueService",
    "job_queue_service",
]
