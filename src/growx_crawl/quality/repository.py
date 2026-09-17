"""
GrowX Quality Repository.
Provides dual-mode persistence (SQLite / In-Memory) for quality evaluations,
rule results, state caching, quarantine, and prospect quality snapshots.
"""

import json
import sqlite3
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from growx_crawl.quality.models import (
    GateType,
    ProspectQualitySnapshot,
    QualityDecision,
    QualityResultEntity,
    QualityRuleResult,
    QualityStateEntity,
    QualityStatus,
    QuarantineEntity,
)
from growx_crawl.shared.ids import generate_id
from growx_crawl.shared.time import utc_iso_now


class QualityRepository(ABC):
    """Abstract interface for Quality persistence."""

    @abstractmethod
    def save_result(self, result: QualityResultEntity, rule_results: Optional[List[QualityRuleResult]] = None) -> None:
        pass

    @abstractmethod
    def get_result(self, result_id: str) -> Optional[QualityResultEntity]:
        pass

    @abstractmethod
    def save_state(self, state: QualityStateEntity) -> None:
        pass

    @abstractmethod
    def get_state(self, subject_type: str, subject_id: str, gate_type: GateType) -> Optional[QualityStateEntity]:
        pass

    @abstractmethod
    def save_quarantine(self, entity: QuarantineEntity) -> None:
        pass

    @abstractmethod
    def list_quarantine(self, status: Optional[str] = None) -> List[QuarantineEntity]:
        pass

    @abstractmethod
    def save_prospect_snapshot(self, snapshot: ProspectQualitySnapshot) -> None:
        pass

    @abstractmethod
    def get_prospect_snapshot(self, prospect_id: str) -> Optional[ProspectQualitySnapshot]:
        pass


class InMemoryQualityRepository(QualityRepository):
    """Fast in-memory implementation for test isolation and ephemeral execution."""

    def __init__(self):
        self._results: Dict[str, QualityResultEntity] = {}
        self._states: Dict[str, QualityStateEntity] = {}
        self._quarantine: Dict[str, QuarantineEntity] = {}
        self._snapshots: Dict[str, ProspectQualitySnapshot] = {}

    def save_result(self, result: QualityResultEntity, rule_results: Optional[List[QualityRuleResult]] = None) -> None:
        self._results[result.id] = result

    def get_result(self, result_id: str) -> Optional[QualityResultEntity]:
        return self._results.get(result_id)

    def save_state(self, state: QualityStateEntity) -> None:
        key = f"{state.subject_type}:{state.subject_id}:{state.gate_type.value}"
        self._states[key] = state

    def get_state(self, subject_type: str, subject_id: str, gate_type: GateType) -> Optional[QualityStateEntity]:
        key = f"{subject_type}:{subject_id}:{gate_type.value}"
        return self._states.get(key)

    def save_quarantine(self, entity: QuarantineEntity) -> None:
        self._quarantine[entity.id] = entity

    def list_quarantine(self, status: Optional[str] = None) -> List[QuarantineEntity]:
        items = list(self._quarantine.values())
        if status:
            items = [q for q in items if q.status == status]
        return items

    def save_prospect_snapshot(self, snapshot: ProspectQualitySnapshot) -> None:
        self._snapshots[snapshot.prospect_id] = snapshot

    def get_prospect_snapshot(self, prospect_id: str) -> Optional[ProspectQualitySnapshot]:
        return self._snapshots.get(prospect_id)


class SqliteQualityRepository(QualityRepository):
    """Durable SQLite repository implementation."""

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

    def save_result(self, result: QualityResultEntity, rule_results: Optional[List[QualityRuleResult]] = None) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO quality_results (
                    id, subject_type, subject_id, gate_type, profile, status, score,
                    policy_id, policy_version, reasons, required_actions, evaluated_at,
                    valid_until, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.id,
                    result.subject_type,
                    result.subject_id,
                    result.gate_type.value,
                    result.profile,
                    result.status.value,
                    result.score,
                    result.policy_id,
                    result.policy_version,
                    json.dumps(result.reasons),
                    json.dumps(result.required_actions),
                    result.evaluated_at,
                    result.valid_until,
                    json.dumps(result.metadata_json),
                ),
            )
            if rule_results:
                for r in rule_results:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO quality_rule_results (
                            id, quality_result_id, rule_name, rule_type, status,
                            score_delta, reason_code, details_json, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            generate_id("qrr_"),
                            result.id,
                            r.rule_name,
                            r.rule_type.value,
                            r.status,
                            r.score_delta,
                            r.reason_code,
                            json.dumps(r.details),
                            utc_iso_now(),
                        ),
                    )
            conn.commit()

    def get_result(self, result_id: str) -> Optional[QualityResultEntity]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM quality_results WHERE id = ?", (result_id,)).fetchone()
            if not row:
                return None
            return QualityResultEntity(
                id=row["id"],
                subject_type=row["subject_type"],
                subject_id=row["subject_id"],
                gate_type=GateType(row["gate_type"]),
                profile=row["profile"],
                status=QualityStatus(row["status"]),
                score=row["score"],
                policy_id=row["policy_id"],
                policy_version=row["policy_version"],
                evaluated_at=row["evaluated_at"],
                valid_until=row["valid_until"],
                reasons=json.loads(row["reasons"] or "[]"),
                required_actions=json.loads(row["required_actions"] or "[]"),
                metadata_json=json.loads(row["metadata_json"] or "{}"),
            )

    def save_state(self, state: QualityStateEntity) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO quality_state (
                    subject_type, subject_id, gate_type, latest_result_id, status, score, valid_until, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    state.subject_type,
                    state.subject_id,
                    state.gate_type.value,
                    state.latest_result_id,
                    state.status.value,
                    state.score,
                    state.valid_until,
                    state.updated_at,
                ),
            )
            conn.commit()

    def get_state(self, subject_type: str, subject_id: str, gate_type: GateType) -> Optional[QualityStateEntity]:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM quality_state WHERE subject_type = ? AND subject_id = ? AND gate_type = ?",
                (subject_type, subject_id, gate_type.value),
            ).fetchone()
            if not row:
                return None
            return QualityStateEntity(
                subject_type=row["subject_type"],
                subject_id=row["subject_id"],
                gate_type=GateType(row["gate_type"]),
                latest_result_id=row["latest_result_id"],
                status=QualityStatus(row["status"]),
                score=row["score"],
                valid_until=row["valid_until"],
                updated_at=row["updated_at"],
            )

    def save_quarantine(self, entity: QuarantineEntity) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO quality_quarantine (
                    id, subject_type, candidate_payload_json, reason_codes, source_id, status, created_at, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entity.id,
                    entity.subject_type,
                    json.dumps(entity.candidate_payload_json),
                    json.dumps(entity.reason_codes),
                    entity.source_id,
                    entity.status,
                    entity.created_at,
                    json.dumps(entity.metadata_json),
                ),
            )
            conn.commit()

    def list_quarantine(self, status: Optional[str] = None) -> List[QuarantineEntity]:
        with self._get_conn() as conn:
            if status:
                rows = conn.execute("SELECT * FROM quality_quarantine WHERE status = ? ORDER BY created_at DESC", (status,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM quality_quarantine ORDER BY created_at DESC").fetchall()
            return [
                QuarantineEntity(
                    id=r["id"],
                    subject_type=r["subject_type"],
                    candidate_payload_json=json.loads(r["candidate_payload_json"] or "{}"),
                    reason_codes=json.loads(r["reason_codes"] or "[]"),
                    source_id=r["source_id"],
                    status=r["status"],
                    created_at=r["created_at"],
                    metadata_json=json.loads(r["metadata_json"] or "{}"),
                )
                for r in rows
            ]

    def save_prospect_snapshot(self, snapshot: ProspectQualitySnapshot) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO prospect_quality_snapshots (
                    prospect_id, company_score, person_score, employment_score, email_score,
                    personalization_score, outreach_score, overall_status, reasons, required_actions, evaluated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot.prospect_id,
                    snapshot.company_score,
                    snapshot.person_score,
                    snapshot.employment_score,
                    snapshot.email_score,
                    snapshot.personalization_score,
                    snapshot.outreach_score,
                    snapshot.overall_status.value,
                    json.dumps(snapshot.reasons),
                    json.dumps(snapshot.required_actions),
                    snapshot.evaluated_at,
                ),
            )
            conn.commit()

    def get_prospect_snapshot(self, prospect_id: str) -> Optional[ProspectQualitySnapshot]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM prospect_quality_snapshots WHERE prospect_id = ?", (prospect_id,)).fetchone()
            if not row:
                return None
            return ProspectQualitySnapshot(
                prospect_id=row["prospect_id"],
                company_score=row["company_score"],
                person_score=row["person_score"],
                employment_score=row["employment_score"],
                email_score=row["email_score"],
                personalization_score=row["personalization_score"],
                outreach_score=row["outreach_score"],
                overall_status=QualityStatus(row["overall_status"]),
                reasons=json.loads(row["reasons"] or "[]"),
                required_actions=json.loads(row["required_actions"] or "[]"),
                evaluated_at=row["evaluated_at"],
            )


quality_repository = InMemoryQualityRepository()
