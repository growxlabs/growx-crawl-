"""
Persistent Job and Worker Repositories for SQLite and PostgreSQL.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
import json
import logging
import sqlite3
from typing import Any, Dict, List, Optional

from growx_crawl.jobs.models import (
    JobEntity,
    PersistentJobStatus,
    PersistentJobType,
    WorkerEntity,
    WorkerStatus,
)
from growx_crawl.storage.db import get_db
from growx_crawl.storage.sqlite.canonical import init_sqlite_canonical_tables

logger = logging.getLogger("growx_crawl.jobs.repository")


class BaseJobRepository(ABC):
    @abstractmethod
    def enqueue(self, job: JobEntity) -> JobEntity:
        pass

    @abstractmethod
    def get(self, job_id: str) -> Optional[JobEntity]:
        pass

    @abstractmethod
    def claim_next(
        self,
        worker_id: str,
        accepted_types: List[str],
        lease_seconds: int = 300,
    ) -> Optional[JobEntity]:
        pass

    @abstractmethod
    def heartbeat_lease(self, job_id: str, worker_id: str, lease_seconds: int = 300) -> bool:
        pass

    @abstractmethod
    def complete(self, job_id: str, worker_id: str, result: Dict[str, Any]) -> Optional[JobEntity]:
        pass

    @abstractmethod
    def fail(
        self,
        job_id: str,
        worker_id: str,
        reason: str,
        can_retry: bool = True,
    ) -> Optional[JobEntity]:
        pass

    @abstractmethod
    def reclaim_expired(self) -> int:
        pass

    @abstractmethod
    def list_jobs(
        self,
        status: Optional[PersistentJobStatus] = None,
        job_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[JobEntity]:
        pass

    @abstractmethod
    def get_queue_depth(self) -> Dict[str, int]:
        pass

    # Worker lifecycle
    @abstractmethod
    def upsert_worker(self, worker: WorkerEntity) -> WorkerEntity:
        pass

    @abstractmethod
    def heartbeat_worker(self, worker_id: str, current_job_id: Optional[str] = None) -> bool:
        pass

    @abstractmethod
    def list_workers(self, worker_type: Optional[str] = None) -> List[WorkerEntity]:
        pass

    @abstractmethod
    def reap_dead_workers(self, timeout_seconds: int = 90) -> int:
        pass


class SqliteJobRepository(BaseJobRepository):
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        with get_db(self.db_path) as conn:
            init_sqlite_canonical_tables(conn)

    def enqueue(self, job: JobEntity) -> JobEntity:
        now_str = datetime.now(timezone.utc).isoformat()
        job.created_at = job.created_at or now_str
        job.updated_at = now_str
        with get_db(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO jobs (
                    id, job_type, status, priority, payload_json, result_json,
                    claimed_by_worker_id, claimed_at, lease_expires_at, heartbeat_at,
                    started_at, finished_at, retry_count, max_retries, failure_reason,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.id,
                    job.job_type,
                    job.status.value,
                    job.priority,
                    json.dumps(job.payload_json),
                    json.dumps(job.result_json),
                    job.claimed_by_worker_id,
                    job.claimed_at,
                    job.lease_expires_at,
                    job.heartbeat_at,
                    job.started_at,
                    job.finished_at,
                    job.retry_count,
                    job.max_retries,
                    job.failure_reason,
                    job.created_at,
                    job.updated_at,
                ),
            )
        return job

    def get(self, job_id: str) -> Optional[JobEntity]:
        with get_db(self.db_path) as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            if not row:
                return None
            return self._row_to_job(row)

    def claim_next(
        self,
        worker_id: str,
        accepted_types: List[str],
        lease_seconds: int = 300,
    ) -> Optional[JobEntity]:
        now = datetime.now(timezone.utc)
        now_str = now.isoformat()
        lease_exp = datetime.fromtimestamp(now.timestamp() + lease_seconds, timezone.utc).isoformat()

        placeholders = ",".join(["?"] * len(accepted_types))
        with get_db(self.db_path) as conn:
            # Atomic select for eligible jobs
            query = f"""
                SELECT id FROM jobs
                WHERE status IN ('queued', 'retrying')
                AND job_type IN ({placeholders})
                ORDER BY priority DESC, created_at ASC
                LIMIT 1
            """
            row = conn.execute(query, tuple(accepted_types)).fetchone()
            if not row:
                return None

            job_id = row["id"]
            # Attempt atomic update
            res = conn.execute(
                """
                UPDATE jobs
                SET status = 'claimed',
                    claimed_by_worker_id = ?,
                    claimed_at = ?,
                    lease_expires_at = ?,
                    heartbeat_at = ?,
                    started_at = COALESCE(started_at, ?),
                    updated_at = ?
                WHERE id = ? AND status IN ('queued', 'retrying')
                """,
                (worker_id, now_str, lease_exp, now_str, now_str, now_str, job_id),
            )
            if res.rowcount == 0:
                return None  # Claimed concurrently

            updated_row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            return self._row_to_job(updated_row)

    def heartbeat_lease(self, job_id: str, worker_id: str, lease_seconds: int = 300) -> bool:
        now = datetime.now(timezone.utc)
        now_str = now.isoformat()
        lease_exp = datetime.fromtimestamp(now.timestamp() + lease_seconds, timezone.utc).isoformat()

        with get_db(self.db_path) as conn:
            res = conn.execute(
                """
                UPDATE jobs
                SET lease_expires_at = ?,
                    heartbeat_at = ?,
                    status = 'running',
                    updated_at = ?
                WHERE id = ? AND claimed_by_worker_id = ? AND status IN ('claimed', 'running')
                """,
                (lease_exp, now_str, now_str, job_id, worker_id),
            )
            return res.rowcount > 0

    def complete(self, job_id: str, worker_id: str, result: Dict[str, Any]) -> Optional[JobEntity]:
        now_str = datetime.now(timezone.utc).isoformat()
        with get_db(self.db_path) as conn:
            conn.execute(
                """
                UPDATE jobs
                SET status = 'completed',
                    result_json = ?,
                    finished_at = ?,
                    updated_at = ?
                WHERE id = ? AND claimed_by_worker_id = ?
                """,
                (json.dumps(result), now_str, now_str, job_id, worker_id),
            )
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            return self._row_to_job(row) if row else None

    def fail(
        self,
        job_id: str,
        worker_id: str,
        reason: str,
        can_retry: bool = True,
    ) -> Optional[JobEntity]:
        now_str = datetime.now(timezone.utc).isoformat()
        with get_db(self.db_path) as conn:
            row = conn.execute("SELECT retry_count, max_retries FROM jobs WHERE id = ?", (job_id,)).fetchone()
            if not row:
                return None

            cur_retries = row["retry_count"] + 1
            max_retries = row["max_retries"]

            new_status = PersistentJobStatus.RETRYING.value if (can_retry and cur_retries <= max_retries) else PersistentJobStatus.FAILED.value
            conn.execute(
                """
                UPDATE jobs
                SET status = ?,
                    retry_count = ?,
                    failure_reason = ?,
                    claimed_by_worker_id = NULL,
                    lease_expires_at = NULL,
                    finished_at = CASE WHEN ? = 'failed' THEN ? ELSE finished_at END,
                    updated_at = ?
                WHERE id = ?
                """,
                (new_status, cur_retries, reason, new_status, now_str, now_str, job_id),
            )
            updated = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            return self._row_to_job(updated) if updated else None

    def reclaim_expired(self) -> int:
        now_str = datetime.now(timezone.utc).isoformat()
        with get_db(self.db_path) as conn:
            # Find all claimed/running jobs whose lease expired
            expired = conn.execute(
                """
                SELECT id, retry_count, max_retries FROM jobs
                WHERE status IN ('claimed', 'running')
                AND lease_expires_at IS NOT NULL
                AND lease_expires_at < ?
                """,
                (now_str,),
            ).fetchall()

            reclaimed = 0
            for r in expired:
                cur_retries = r["retry_count"] + 1
                max_retries = r["max_retries"]
                new_status = PersistentJobStatus.RETRYING.value if cur_retries <= max_retries else PersistentJobStatus.FAILED.value
                reason = "Worker lease expired; reclaimed automatically by supervisor."
                conn.execute(
                    """
                    UPDATE jobs
                    SET status = ?,
                        retry_count = ?,
                        failure_reason = ?,
                        claimed_by_worker_id = NULL,
                        lease_expires_at = NULL,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (new_status, cur_retries, reason, now_str, r["id"]),
                )
                reclaimed += 1
            return reclaimed

    def list_jobs(
        self,
        status: Optional[PersistentJobStatus] = None,
        job_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[JobEntity]:
        with get_db(self.db_path) as conn:
            clauses = []
            params = []
            if status:
                clauses.append("status = ?")
                params.append(status.value if isinstance(status, PersistentJobStatus) else str(status))
            if job_type:
                clauses.append("job_type = ?")
                params.append(job_type)

            where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
            params.append(limit)
            rows = conn.execute(
                f"SELECT * FROM jobs {where} ORDER BY created_at DESC LIMIT ?",
                tuple(params),
            ).fetchall()
            return [self._row_to_job(r) for r in rows]

    def get_queue_depth(self) -> Dict[str, int]:
        with get_db(self.db_path) as conn:
            rows = conn.execute("SELECT status, COUNT(*) as count FROM jobs GROUP BY status").fetchall()
            res = {s.value: 0 for s in PersistentJobStatus}
            for r in rows:
                res[r["status"]] = r["count"]
            return res

    # Workers
    def upsert_worker(self, worker: WorkerEntity) -> WorkerEntity:
        now_str = datetime.now(timezone.utc).isoformat()
        worker.last_heartbeat_at = now_str
        with get_db(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO workers (
                    id, worker_type, hostname, process_id, status, current_job_id,
                    version, started_at, last_heartbeat_at, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status = excluded.status,
                    current_job_id = excluded.current_job_id,
                    last_heartbeat_at = excluded.last_heartbeat_at,
                    metadata_json = excluded.metadata_json
                """,
                (
                    worker.id,
                    worker.worker_type,
                    worker.hostname,
                    worker.process_id,
                    worker.status.value,
                    worker.current_job_id,
                    worker.version,
                    worker.started_at,
                    worker.last_heartbeat_at,
                    json.dumps(worker.metadata_json),
                ),
            )
        return worker

    def heartbeat_worker(self, worker_id: str, current_job_id: Optional[str] = None) -> bool:
        now_str = datetime.now(timezone.utc).isoformat()
        with get_db(self.db_path) as conn:
            res = conn.execute(
                """
                UPDATE workers
                SET last_heartbeat_at = ?,
                    current_job_id = COALESCE(?, current_job_id),
                    status = 'active'
                WHERE id = ?
                """,
                (now_str, current_job_id, worker_id),
            )
            return res.rowcount > 0

    def list_workers(self, worker_type: Optional[str] = None) -> List[WorkerEntity]:
        with get_db(self.db_path) as conn:
            if worker_type:
                rows = conn.execute("SELECT * FROM workers WHERE worker_type = ? ORDER BY started_at DESC", (worker_type,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM workers ORDER BY started_at DESC").fetchall()
            return [self._row_to_worker(r) for r in rows]

    def reap_dead_workers(self, timeout_seconds: int = 90) -> int:
        now = datetime.now(timezone.utc)
        cutoff = datetime.fromtimestamp(now.timestamp() - timeout_seconds, timezone.utc).isoformat()
        with get_db(self.db_path) as conn:
            res = conn.execute(
                """
                UPDATE workers
                SET status = 'offline', current_job_id = NULL
                WHERE status IN ('active', 'busy', 'idle')
                AND last_heartbeat_at < ?
                """,
                (cutoff,),
            )
            return res.rowcount

    def _row_to_job(self, r: sqlite3.Row) -> JobEntity:
        return JobEntity(
            id=r["id"],
            job_type=r["job_type"],
            status=PersistentJobStatus(r["status"]),
            priority=r["priority"],
            payload_json=json.loads(r["payload_json"] or "{}"),
            result_json=json.loads(r["result_json"] or "{}"),
            claimed_by_worker_id=r["claimed_by_worker_id"],
            claimed_at=r["claimed_at"],
            lease_expires_at=r["lease_expires_at"],
            heartbeat_at=r["heartbeat_at"],
            started_at=r["started_at"],
            finished_at=r["finished_at"],
            retry_count=r["retry_count"],
            max_retries=r["max_retries"],
            failure_reason=r["failure_reason"],
            created_at=r["created_at"],
            updated_at=r["updated_at"],
        )

    def _row_to_worker(self, r: sqlite3.Row) -> WorkerEntity:
        return WorkerEntity(
            id=r["id"],
            worker_type=r["worker_type"],
            hostname=r["hostname"] or "localhost",
            process_id=r["process_id"],
            status=WorkerStatus(r["status"]),
            current_job_id=r["current_job_id"],
            version=r["version"] or "1.0.0",
            started_at=r["started_at"],
            last_heartbeat_at=r["last_heartbeat_at"],
            metadata_json=json.loads(r["metadata_json"] or "{}"),
        )
