"""
GrowX Data Factory Repository.
Provides dual-mode persistence (SQLite / In-Memory) for runs, checkpoints,
failed jobs, and morning intelligence summaries.
"""

import json
import sqlite3
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from growx_crawl.data_factory.models import (
    DataFactoryCheckpoint,
    DataFactoryRun,
    FailedJob,
    FactoryStage,
    MorningSummary,
    RunStatus,
    RunType,
)


class DataFactoryRepository(ABC):
    """Abstract interface for Data Factory persistence."""

    @abstractmethod
    def save_run(self, run: DataFactoryRun) -> None:
        pass

    @abstractmethod
    def get_run(self, run_id: str) -> Optional[DataFactoryRun]:
        pass

    @abstractmethod
    def list_runs(self, limit: int = 50, status: Optional[str] = None) -> List[DataFactoryRun]:
        pass

    @abstractmethod
    def save_checkpoint(self, checkpoint: DataFactoryCheckpoint) -> None:
        pass

    @abstractmethod
    def get_checkpoints(self, run_id: str) -> List[DataFactoryCheckpoint]:
        pass

    @abstractmethod
    def save_failed_job(self, job: FailedJob) -> None:
        pass

    @abstractmethod
    def list_failed_jobs(self, run_id: Optional[str] = None) -> List[FailedJob]:
        pass

    @abstractmethod
    def save_summary(self, summary: MorningSummary) -> None:
        pass

    @abstractmethod
    def get_summary(self, run_id: str) -> Optional[MorningSummary]:
        pass


class InMemoryDataFactoryRepository(DataFactoryRepository):
    """Fast in-memory repository for unit testing and ephemeral runs."""

    def __init__(self):
        self._runs: Dict[str, DataFactoryRun] = {}
        self._checkpoints: Dict[str, List[DataFactoryCheckpoint]] = {}
        self._failed_jobs: List[FailedJob] = []
        self._summaries: Dict[str, MorningSummary] = {}

    def save_run(self, run: DataFactoryRun) -> None:
        self._runs[run.id] = run

    def get_run(self, run_id: str) -> Optional[DataFactoryRun]:
        return self._runs.get(run_id)

    def list_runs(self, limit: int = 50, status: Optional[str] = None) -> List[DataFactoryRun]:
        runs = list(self._runs.values())
        if status:
            runs = [r for r in runs if r.status.value == status or r.status == status]
        runs.sort(key=lambda r: r.started_at, reverse=True)
        return runs[:limit]

    def save_checkpoint(self, checkpoint: DataFactoryCheckpoint) -> None:
        run_cps = self._checkpoints.setdefault(checkpoint.run_id, [])
        # Replace if stage already present
        for i, cp in enumerate(run_cps):
            if cp.stage == checkpoint.stage:
                run_cps[i] = checkpoint
                return
        run_cps.append(checkpoint)

    def get_checkpoints(self, run_id: str) -> List[DataFactoryCheckpoint]:
        return self._checkpoints.get(run_id, [])

    def save_failed_job(self, job: FailedJob) -> None:
        self._failed_jobs.append(job)

    def list_failed_jobs(self, run_id: Optional[str] = None) -> List[FailedJob]:
        if run_id:
            return [j for j in self._failed_jobs if j.run_id == run_id]
        return list(self._failed_jobs)

    def save_summary(self, summary: MorningSummary) -> None:
        self._summaries[summary.run_id] = summary

    def get_summary(self, run_id: str) -> Optional[MorningSummary]:
        return self._summaries.get(run_id)


class SqliteDataFactoryRepository(DataFactoryRepository):
    """Durable SQLite implementation for Data Factory runs and checkpoints."""

    def __init__(self, db_path: str = "growx_canonical.db"):
        self.db_path = db_path
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        from growx_crawl.storage.sqlite.canonical import init_sqlite_canonical_tables
        with sqlite3.connect(self.db_path) as conn:
            init_sqlite_canonical_tables(conn)

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def save_run(self, run: DataFactoryRun) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO data_factory_runs (
                    id, run_type, status, started_at, completed_at, plan_version,
                    checkpoint, discovery_count, crawl_count, entity_count,
                    verification_count, quality_pass_count, error_count,
                    estimated_cost, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.id,
                    run.run_type.value,
                    run.status.value,
                    run.started_at,
                    run.completed_at,
                    run.plan_version,
                    run.checkpoint.value,
                    run.discovery_count,
                    run.crawl_count,
                    run.entity_count,
                    run.verification_count,
                    run.quality_pass_count,
                    run.error_count,
                    run.estimated_cost,
                    json.dumps(run.metadata_json),
                ),
            )

    def get_run(self, run_id: str) -> Optional[DataFactoryRun]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM data_factory_runs WHERE id = ?", (run_id,)).fetchone()
            if not row:
                return None
            return DataFactoryRun(
                id=row["id"],
                run_type=RunType(row["run_type"]),
                status=RunStatus(row["status"]),
                started_at=row["started_at"],
                completed_at=row["completed_at"],
                plan_version=row["plan_version"],
                checkpoint=FactoryStage(row["checkpoint"]),
                discovery_count=row["discovery_count"],
                crawl_count=row["crawl_count"],
                entity_count=row["entity_count"],
                verification_count=row["verification_count"],
                quality_pass_count=row["quality_pass_count"],
                error_count=row["error_count"],
                estimated_cost=row["estimated_cost"],
                metadata_json=json.loads(row["metadata_json"] or "{}"),
            )

    def list_runs(self, limit: int = 50, status: Optional[str] = None) -> List[DataFactoryRun]:
        with self._get_conn() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM data_factory_runs WHERE status = ? ORDER BY started_at DESC LIMIT ?",
                    (status, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM data_factory_runs ORDER BY started_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()

            return [
                DataFactoryRun(
                    id=row["id"],
                    run_type=RunType(row["run_type"]),
                    status=RunStatus(row["status"]),
                    started_at=row["started_at"],
                    completed_at=row["completed_at"],
                    plan_version=row["plan_version"],
                    checkpoint=FactoryStage(row["checkpoint"]),
                    discovery_count=row["discovery_count"],
                    crawl_count=row["crawl_count"],
                    entity_count=row["entity_count"],
                    verification_count=row["verification_count"],
                    quality_pass_count=row["quality_pass_count"],
                    error_count=row["error_count"],
                    estimated_cost=row["estimated_cost"],
                    metadata_json=json.loads(row["metadata_json"] or "{}"),
                )
                for row in rows
            ]

    def save_checkpoint(self, checkpoint: DataFactoryCheckpoint) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO data_factory_checkpoints (
                    run_id, stage, cursor, status, processed_count, failed_count,
                    updated_at, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    checkpoint.run_id,
                    checkpoint.stage.value,
                    checkpoint.cursor,
                    checkpoint.status,
                    checkpoint.processed_count,
                    checkpoint.failed_count,
                    checkpoint.updated_at,
                    json.dumps(checkpoint.metadata_json),
                ),
            )

    def get_checkpoints(self, run_id: str) -> List[DataFactoryCheckpoint]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM data_factory_checkpoints WHERE run_id = ?",
                (run_id,),
            ).fetchall()
            return [
                DataFactoryCheckpoint(
                    run_id=row["run_id"],
                    stage=FactoryStage(row["stage"]),
                    cursor=row["cursor"],
                    status=row["status"],
                    processed_count=row["processed_count"],
                    failed_count=row["failed_count"],
                    updated_at=row["updated_at"],
                    metadata_json=json.loads(row["metadata_json"] or "{}"),
                )
                for row in rows
            ]

    def save_failed_job(self, job: FailedJob) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO data_factory_failed_jobs (
                    id, run_id, stage, subject_id, error_code, attempts,
                    last_error, created_at, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.id,
                    job.run_id,
                    job.stage.value,
                    job.subject_id,
                    job.error_code,
                    job.attempts,
                    job.last_error,
                    job.created_at,
                    json.dumps(job.metadata_json),
                ),
            )

    def list_failed_jobs(self, run_id: Optional[str] = None) -> List[FailedJob]:
        with self._get_conn() as conn:
            if run_id:
                rows = conn.execute(
                    "SELECT * FROM data_factory_failed_jobs WHERE run_id = ? ORDER BY created_at DESC",
                    (run_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM data_factory_failed_jobs ORDER BY created_at DESC",
                ).fetchall()

            return [
                FailedJob(
                    id=row["id"],
                    run_id=row["run_id"],
                    stage=FactoryStage(row["stage"]),
                    subject_id=row["subject_id"],
                    error_code=row["error_code"],
                    attempts=row["attempts"],
                    last_error=row["last_error"],
                    created_at=row["created_at"],
                    metadata_json=json.loads(row["metadata_json"] or "{}"),
                )
                for row in rows
            ]

    def save_summary(self, summary: MorningSummary) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO data_factory_summaries (
                    run_id, started_at, completed_at, queries_run, new_domains,
                    companies_created, companies_updated, people_created,
                    facts_added, facts_changed, verified_companies,
                    quality_trusted_entities, errors, estimated_cost,
                    report_markdown, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    summary.run_id,
                    summary.started_at,
                    summary.completed_at,
                    summary.queries_run,
                    summary.new_domains,
                    summary.companies_created,
                    summary.companies_updated,
                    summary.people_created,
                    summary.facts_added,
                    summary.facts_changed,
                    summary.verified_companies,
                    summary.quality_trusted_entities,
                    summary.errors,
                    summary.estimated_cost,
                    summary.report_markdown,
                    json.dumps(summary.metadata_json),
                ),
            )

    def get_summary(self, run_id: str) -> Optional[MorningSummary]:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM data_factory_summaries WHERE run_id = ?",
                (run_id,),
            ).fetchone()
            if not row:
                return None
            total_co = row["companies_created"] + row["companies_updated"]
            cost_per = round(row["estimated_cost"] / max(1, total_co), 4)
            return MorningSummary(
                run_id=row["run_id"],
                started_at=row["started_at"],
                completed_at=row["completed_at"],
                queries_run=row["queries_run"],
                new_domains=row["new_domains"],
                companies_created=row["companies_created"],
                companies_updated=row["companies_updated"],
                people_created=row["people_created"],
                facts_added=row["facts_added"],
                facts_changed=row["facts_changed"],
                verified_companies=row["verified_companies"],
                quality_trusted_entities=row["quality_trusted_entities"],
                errors=row["errors"],
                estimated_cost=row["estimated_cost"],
                cost_per_company=cost_per,
                report_markdown=row["report_markdown"],
                metadata_json=json.loads(row["metadata_json"] or "{}"),
            )
