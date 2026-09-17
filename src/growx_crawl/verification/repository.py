"""
GrowX Verification Repository.
Defines storage interfaces and SQLite/Postgres persistence for verification runs,
checks, denormalized current states, and policies.
"""

import json
import sqlite3
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from growx_crawl.shared.time import utc_iso_now
from growx_crawl.verification.models import (
    VerificationCheckEntity,
    VerificationPolicy,
    VerificationResultEntity,
    VerificationRunEntity,
    VerificationStateEntity,
    VerificationStatus,
)


class BaseVerificationRepository(ABC):
    @abstractmethod
    def save_run(self, run: VerificationRunEntity) -> None:
        pass

    @abstractmethod
    def get_run(self, run_id: str) -> Optional[VerificationRunEntity]:
        pass

    @abstractmethod
    def list_runs(self, subject_type: str, subject_id: str, limit: int = 50) -> List[VerificationRunEntity]:
        pass

    @abstractmethod
    def save_check(self, check: VerificationCheckEntity) -> None:
        pass

    @abstractmethod
    def list_checks(self, run_id: str) -> List[VerificationCheckEntity]:
        pass

    @abstractmethod
    def save_state(self, state: VerificationStateEntity) -> None:
        pass

    @abstractmethod
    def get_state(self, subject_type: str, subject_id: str, verification_type: str = "standard") -> Optional[VerificationStateEntity]:
        pass

    @abstractmethod
    def save_result(self, result: VerificationResultEntity) -> None:
        """Helper to save run, checks, and state atomically from a single result."""
        pass


class InMemoryVerificationRepository(BaseVerificationRepository):
    """In-memory implementation for testing and local zero-dependency operation."""

    def __init__(self):
        self._runs: Dict[str, VerificationRunEntity] = {}
        self._checks: Dict[str, List[VerificationCheckEntity]] = {}
        self._states: Dict[str, VerificationStateEntity] = {}

    def save_run(self, run: VerificationRunEntity) -> None:
        self._runs[run.id] = run

    def get_run(self, run_id: str) -> Optional[VerificationRunEntity]:
        return self._runs.get(run_id)

    def list_runs(self, subject_type: str, subject_id: str, limit: int = 50) -> List[VerificationRunEntity]:
        return [
            r for r in self._runs.values()
            if r.subject_type == subject_type and r.subject_id == subject_id
        ][:limit]

    def save_check(self, check: VerificationCheckEntity) -> None:
        self._checks.setdefault(check.verification_run_id, []).append(check)

    def list_checks(self, run_id: str) -> List[VerificationCheckEntity]:
        return self._checks.get(run_id, [])

    def save_state(self, state: VerificationStateEntity) -> None:
        key = f"{state.subject_type}:{state.subject_id}:{state.verification_type}"
        self._states[key] = state

    def get_state(self, subject_type: str, subject_id: str, verification_type: str = "standard") -> Optional[VerificationStateEntity]:
        key = f"{subject_type}:{subject_id}:{verification_type}"
        return self._states.get(key)

    def save_result(self, result: VerificationResultEntity) -> None:
        run = VerificationRunEntity(
            id=result.id,
            subject_type=result.subject_type,
            subject_id=result.subject_id,
            verification_type=result.verification_type,
            policy_id=result.policy_name,
            policy_version=result.policy_version,
            status=result.status,
            confidence=result.confidence,
            started_at=result.verified_at,
            completed_at=result.verified_at,
            valid_until=result.valid_until,
            metadata_json=result.metadata_json,
        )
        self.save_run(run)

        for chk in result.checks:
            chk.verification_run_id = result.id
            self.save_check(chk)

        state = VerificationStateEntity(
            subject_type=result.subject_type,
            subject_id=result.subject_id,
            verification_type=result.verification_type,
            latest_run_id=result.id,
            status=result.status,
            confidence=result.confidence,
            last_verified_at=result.verified_at,
            valid_until=result.valid_until,
            updated_at=utc_iso_now(),
            metadata_json=result.details_json,
        )
        self.save_state(state)


class SqliteVerificationRepository(BaseVerificationRepository):
    """Production SQLite verification repository using canonical tables."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def save_run(self, run: VerificationRunEntity) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO canonical_verification_runs (
                    id, subject_type, subject_id, verification_type, policy_id,
                    policy_version, status, confidence, started_at, completed_at,
                    valid_until, error_code, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.id, run.subject_type, run.subject_id, run.verification_type,
                    run.policy_id, run.policy_version, run.status.value if hasattr(run.status, "value") else str(run.status),
                    run.confidence, run.started_at, run.completed_at, run.valid_until,
                    run.error_code, json.dumps(run.metadata_json),
                ),
            )

    def get_run(self, run_id: str) -> Optional[VerificationRunEntity]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM canonical_verification_runs WHERE id = ?", (run_id,)).fetchone()
            if not row:
                return None
            return VerificationRunEntity(
                id=row["id"],
                subject_type=row["subject_type"],
                subject_id=row["subject_id"],
                verification_type=row["verification_type"],
                policy_id=row["policy_id"],
                policy_version=row["policy_version"],
                status=VerificationStatus(row["status"]),
                confidence=float(row["confidence"]),
                started_at=row["started_at"],
                completed_at=row["completed_at"],
                valid_until=row["valid_until"],
                error_code=row["error_code"],
                metadata_json=json.loads(row["metadata_json"] or "{}"),
            )

    def list_runs(self, subject_type: str, subject_id: str, limit: int = 50) -> List[VerificationRunEntity]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM canonical_verification_runs WHERE subject_type = ? AND subject_id = ? ORDER BY started_at DESC LIMIT ?",
                (subject_type, subject_id, limit),
            ).fetchall()
            return [
                VerificationRunEntity(
                    id=r["id"],
                    subject_type=r["subject_type"],
                    subject_id=r["subject_id"],
                    verification_type=r["verification_type"],
                    policy_id=r["policy_id"],
                    policy_version=r["policy_version"],
                    status=VerificationStatus(r["status"]),
                    confidence=float(r["confidence"]),
                    started_at=r["started_at"],
                    completed_at=r["completed_at"],
                    valid_until=r["valid_until"],
                    error_code=r["error_code"],
                    metadata_json=json.loads(r["metadata_json"] or "{}"),
                )
                for r in rows
            ]

    def save_check(self, check: VerificationCheckEntity) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO canonical_verification_checks (
                    id, verification_run_id, check_type, status, score,
                    reason_code, evidence_ids, duration_ms, created_at, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    check.id, check.verification_run_id, check.check_type, check.status,
                    check.score, check.reason_code, json.dumps(check.evidence_ids),
                    check.duration_ms, check.created_at, json.dumps(check.metadata_json),
                ),
            )

    def list_checks(self, run_id: str) -> List[VerificationCheckEntity]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM canonical_verification_checks WHERE verification_run_id = ?",
                (run_id,),
            ).fetchall()
            return [
                VerificationCheckEntity(
                    id=r["id"],
                    verification_run_id=r["verification_run_id"],
                    check_type=r["check_type"],
                    status=r["status"],
                    score=float(r["score"]),
                    reason_code=r["reason_code"],
                    evidence_ids=json.loads(r["evidence_ids"] or "[]"),
                    duration_ms=int(r["duration_ms"]),
                    created_at=r["created_at"],
                    metadata_json=json.loads(r["metadata_json"] or "{}"),
                )
                for r in rows
            ]

    def save_state(self, state: VerificationStateEntity) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO canonical_verification_state (
                    subject_type, subject_id, verification_type, latest_run_id,
                    status, confidence, last_verified_at, valid_until, updated_at, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    state.subject_type, state.subject_id, state.verification_type,
                    state.latest_run_id, state.status.value if hasattr(state.status, "value") else str(state.status),
                    state.confidence, state.last_verified_at, state.valid_until,
                    state.updated_at, json.dumps(state.metadata_json),
                ),
            )

    def get_state(self, subject_type: str, subject_id: str, verification_type: str = "standard") -> Optional[VerificationStateEntity]:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM canonical_verification_state WHERE subject_type = ? AND subject_id = ? AND verification_type = ?",
                (subject_type, subject_id, verification_type),
            ).fetchone()
            if not row:
                return None
            return VerificationStateEntity(
                subject_type=row["subject_type"],
                subject_id=row["subject_id"],
                verification_type=row["verification_type"],
                latest_run_id=row["latest_run_id"],
                status=VerificationStatus(row["status"]),
                confidence=float(row["confidence"]),
                last_verified_at=row["last_verified_at"],
                valid_until=row["valid_until"],
                updated_at=row["updated_at"],
                metadata_json=json.loads(row["metadata_json"] or "{}"),
            )

    def save_result(self, result: VerificationResultEntity) -> None:
        run = VerificationRunEntity(
            id=result.id,
            subject_type=result.subject_type,
            subject_id=result.subject_id,
            verification_type=result.verification_type,
            policy_id=result.policy_name,
            policy_version=result.policy_version,
            status=result.status,
            confidence=result.confidence,
            started_at=result.verified_at,
            completed_at=result.verified_at,
            valid_until=result.valid_until,
            metadata_json=result.metadata_json,
        )
        self.save_run(run)

        for chk in result.checks:
            chk.verification_run_id = result.id
            self.save_check(chk)

        state = VerificationStateEntity(
            subject_type=result.subject_type,
            subject_id=result.subject_id,
            verification_type=result.verification_type,
            latest_run_id=result.id,
            status=result.status,
            confidence=result.confidence,
            last_verified_at=result.verified_at,
            valid_until=result.valid_until,
            updated_at=utc_iso_now(),
            metadata_json=result.details_json,
        )
        self.save_state(state)
