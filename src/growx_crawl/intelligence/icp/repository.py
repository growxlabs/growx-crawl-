"""
GrowX ICP Repository.
Persistence layer for ICP profiles, versions, seller snapshots, criteria, exclusions, personas, scores, and evidence.
"""

import json
import logging
import sqlite3
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from growx_crawl.intelligence.icp.models import (
    ICPEntity,
    ICPVersionEntity,
    SellerSnapshotEntity,
    ICPCriterionEntity,
    ICPExclusionEntity,
    ICPPersonaEntity,
    ICPCompanyScoreEntity,
    ICPPersonScoreEntity,
    ICPEvidenceEntity,
)
from growx_crawl.storage.db import get_db
from growx_crawl.storage.sqlite.canonical import init_sqlite_canonical_tables

logger = logging.getLogger("growx_crawl.intelligence.icp.repository")


class BaseICPRepository(ABC):
    @abstractmethod
    def save_icp(self, icp: ICPEntity) -> ICPEntity: ...

    @abstractmethod
    def get_icp(self, icp_id: str) -> Optional[ICPEntity]: ...

    @abstractmethod
    def list_icps(
        self,
        seller_company_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[ICPEntity]: ...

    @abstractmethod
    def update_icp_status(
        self, icp_id: str, status: str, current_version_id: Optional[str] = None
    ) -> None: ...

    @abstractmethod
    def save_version(self, version: ICPVersionEntity) -> ICPVersionEntity: ...

    @abstractmethod
    def get_version(self, version_id: str) -> Optional[ICPVersionEntity]: ...

    @abstractmethod
    def get_version_by_number(self, icp_id: str, version: int) -> Optional[ICPVersionEntity]: ...

    @abstractmethod
    def list_versions(self, icp_id: str) -> List[ICPVersionEntity]: ...

    @abstractmethod
    def update_version_status(self, version_id: str, status: str) -> None: ...

    @abstractmethod
    def save_snapshot(self, snapshot: SellerSnapshotEntity) -> SellerSnapshotEntity: ...

    @abstractmethod
    def get_snapshot(self, snapshot_id: str) -> Optional[SellerSnapshotEntity]: ...

    @abstractmethod
    def save_criterion(self, criterion: ICPCriterionEntity) -> ICPCriterionEntity: ...

    @abstractmethod
    def save_criteria(self, criteria: List[ICPCriterionEntity]) -> None: ...

    @abstractmethod
    def list_criteria(
        self, icp_version_id: str, category: Optional[str] = None
    ) -> List[ICPCriterionEntity]: ...

    @abstractmethod
    def save_exclusion(self, exclusion: ICPExclusionEntity) -> ICPExclusionEntity: ...

    @abstractmethod
    def save_exclusions(self, exclusions: List[ICPExclusionEntity]) -> None: ...

    @abstractmethod
    def list_exclusions(self, icp_version_id: str) -> List[ICPExclusionEntity]: ...

    @abstractmethod
    def save_persona(self, persona: ICPPersonaEntity) -> ICPPersonaEntity: ...

    @abstractmethod
    def save_personas(self, personas: List[ICPPersonaEntity]) -> None: ...

    @abstractmethod
    def list_personas(self, icp_version_id: str) -> List[ICPPersonaEntity]: ...

    @abstractmethod
    def save_company_score(self, score: ICPCompanyScoreEntity) -> ICPCompanyScoreEntity: ...

    @abstractmethod
    def get_company_score(
        self, icp_version_id: str, company_id: str
    ) -> Optional[ICPCompanyScoreEntity]: ...

    @abstractmethod
    def list_company_scores(
        self,
        icp_version_id: str,
        min_fit: float = 0.0,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[ICPCompanyScoreEntity]: ...

    @abstractmethod
    def save_person_score(self, score: ICPPersonScoreEntity) -> ICPPersonScoreEntity: ...

    @abstractmethod
    def get_person_score(
        self, icp_version_id: str, person_id: str
    ) -> Optional[ICPPersonScoreEntity]: ...

    @abstractmethod
    def list_person_scores(
        self, icp_version_id: str, company_id: Optional[str] = None, limit: int = 50
    ) -> List[ICPPersonScoreEntity]: ...

    @abstractmethod
    def save_evidence(self, evidence: ICPEvidenceEntity) -> ICPEvidenceEntity: ...

    @abstractmethod
    def save_evidence_batch(self, evidence_list: List[ICPEvidenceEntity]) -> None: ...

    @abstractmethod
    def list_evidence(
        self, icp_version_id: str, criterion_id: Optional[str] = None
    ) -> List[ICPEvidenceEntity]: ...


class SqliteICPRepository(BaseICPRepository):
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def _ensure_schema(self, conn: sqlite3.Connection):
        init_sqlite_canonical_tables(conn)

    def _parse_json(self, val: Any) -> Any:
        if val is None:
            return {}
        if isinstance(val, (dict, list)):
            return val
        try:
            return json.loads(val)
        except Exception:
            return {}

    # --- ICP ---

    def save_icp(self, icp: ICPEntity) -> ICPEntity:
        sql = """
            INSERT INTO icps (
                id, seller_company_id, name, description, status, source_type,
                current_version_id, created_at, updated_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                seller_company_id = excluded.seller_company_id,
                name = excluded.name,
                description = excluded.description,
                status = excluded.status,
                source_type = excluded.source_type,
                current_version_id = excluded.current_version_id,
                updated_at = excluded.updated_at,
                metadata_json = excluded.metadata_json;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    icp.id,
                    icp.seller_company_id,
                    icp.name,
                    icp.description,
                    icp.status,
                    icp.source_type,
                    icp.current_version_id,
                    icp.created_at,
                    icp.updated_at,
                    json.dumps(icp.metadata_json),
                ),
            )
        return icp

    def get_icp(self, icp_id: str) -> Optional[ICPEntity]:
        sql = "SELECT * FROM icps WHERE id = ?"
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute(sql, (icp_id,)).fetchone()
            if not row:
                return None
            return ICPEntity(
                id=row["id"],
                seller_company_id=row["seller_company_id"],
                name=row["name"],
                description=row["description"],
                status=row["status"],
                source_type=row["source_type"],
                current_version_id=row["current_version_id"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                metadata_json=self._parse_json(row["metadata_json"]),
            )

    def list_icps(
        self,
        seller_company_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[ICPEntity]:
        conditions = []
        params: List[Any] = []
        if seller_company_id:
            conditions.append("seller_company_id = ?")
            params.append(seller_company_id)
        if status:
            conditions.append("status = ?")
            params.append(status)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"SELECT * FROM icps {where_clause} ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(sql, params).fetchall()
            return [
                ICPEntity(
                    id=r["id"],
                    seller_company_id=r["seller_company_id"],
                    name=r["name"],
                    description=r["description"],
                    status=r["status"],
                    source_type=r["source_type"],
                    current_version_id=r["current_version_id"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                    metadata_json=self._parse_json(r["metadata_json"]),
                )
                for r in rows
            ]

    def update_icp_status(
        self, icp_id: str, status: str, current_version_id: Optional[str] = None
    ) -> None:
        if current_version_id:
            sql = "UPDATE icps SET status = ?, current_version_id = ? WHERE id = ?"
            params = (status, current_version_id, icp_id)
        else:
            sql = "UPDATE icps SET status = ? WHERE id = ?"
            params = (status, icp_id)
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(sql, params)

    # --- Versions ---

    def save_version(self, version: ICPVersionEntity) -> ICPVersionEntity:
        sql = """
            INSERT INTO icp_versions (
                id, icp_id, version, status, created_at, created_by,
                seller_snapshot_id, policy_version, model_run_id, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                status = excluded.status,
                seller_snapshot_id = excluded.seller_snapshot_id,
                policy_version = excluded.policy_version,
                model_run_id = excluded.model_run_id,
                metadata_json = excluded.metadata_json;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    version.id,
                    version.icp_id,
                    version.version,
                    version.status,
                    version.created_at,
                    version.created_by,
                    version.seller_snapshot_id,
                    version.policy_version,
                    version.model_run_id,
                    json.dumps(version.metadata_json),
                ),
            )
        return version

    def get_version(self, version_id: str) -> Optional[ICPVersionEntity]:
        sql = "SELECT * FROM icp_versions WHERE id = ?"
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute(sql, (version_id,)).fetchone()
            if not row:
                return None
            return ICPVersionEntity(
                id=row["id"],
                icp_id=row["icp_id"],
                version=row["version"],
                status=row["status"],
                created_at=row["created_at"],
                created_by=row["created_by"],
                seller_snapshot_id=row["seller_snapshot_id"],
                policy_version=row["policy_version"],
                model_run_id=row["model_run_id"],
                metadata_json=self._parse_json(row["metadata_json"]),
            )

    def get_version_by_number(self, icp_id: str, version: int) -> Optional[ICPVersionEntity]:
        sql = "SELECT * FROM icp_versions WHERE icp_id = ? AND version = ?"
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute(sql, (icp_id, version)).fetchone()
            if not row:
                return None
            return ICPVersionEntity(
                id=row["id"],
                icp_id=row["icp_id"],
                version=row["version"],
                status=row["status"],
                created_at=row["created_at"],
                created_by=row["created_by"],
                seller_snapshot_id=row["seller_snapshot_id"],
                policy_version=row["policy_version"],
                model_run_id=row["model_run_id"],
                metadata_json=self._parse_json(row["metadata_json"]),
            )

    def list_versions(self, icp_id: str) -> List[ICPVersionEntity]:
        sql = "SELECT * FROM icp_versions WHERE icp_id = ? ORDER BY version ASC"
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(sql, (icp_id,)).fetchall()
            return [
                ICPVersionEntity(
                    id=r["id"],
                    icp_id=r["icp_id"],
                    version=r["version"],
                    status=r["status"],
                    created_at=r["created_at"],
                    created_by=r["created_by"],
                    seller_snapshot_id=r["seller_snapshot_id"],
                    policy_version=r["policy_version"],
                    model_run_id=r["model_run_id"],
                    metadata_json=self._parse_json(r["metadata_json"]),
                )
                for r in rows
            ]

    def update_version_status(self, version_id: str, status: str) -> None:
        sql = "UPDATE icp_versions SET status = ? WHERE id = ?"
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(sql, (status, version_id))

    # --- Snapshots ---

    def save_snapshot(self, snapshot: SellerSnapshotEntity) -> SellerSnapshotEntity:
        sql = """
            INSERT INTO seller_snapshots (
                id, seller_company_id, fact_snapshot_json, verified_at, created_at
            ) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                fact_snapshot_json = excluded.fact_snapshot_json,
                verified_at = excluded.verified_at;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    snapshot.id,
                    snapshot.seller_company_id,
                    json.dumps(snapshot.fact_snapshot_json),
                    snapshot.verified_at,
                    snapshot.created_at,
                ),
            )
        return snapshot

    def get_snapshot(self, snapshot_id: str) -> Optional[SellerSnapshotEntity]:
        sql = "SELECT * FROM seller_snapshots WHERE id = ?"
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute(sql, (snapshot_id,)).fetchone()
            if not row:
                return None
            return SellerSnapshotEntity(
                id=row["id"],
                seller_company_id=row["seller_company_id"],
                fact_snapshot_json=self._parse_json(row["fact_snapshot_json"]),
                verified_at=row["verified_at"],
                created_at=row["created_at"],
            )

    # --- Criteria ---

    def save_criterion(self, criterion: ICPCriterionEntity) -> ICPCriterionEntity:
        sql = """
            INSERT INTO icp_criteria (
                id, icp_version_id, category, field, operator, value_json,
                weight, requirement_type, source, confidence, created_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                category = excluded.category,
                field = excluded.field,
                operator = excluded.operator,
                value_json = excluded.value_json,
                weight = excluded.weight,
                requirement_type = excluded.requirement_type,
                source = excluded.source,
                confidence = excluded.confidence,
                metadata_json = excluded.metadata_json;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    criterion.id,
                    criterion.icp_version_id,
                    criterion.category,
                    criterion.field,
                    criterion.operator,
                    json.dumps(criterion.value_json),
                    criterion.weight,
                    criterion.requirement_type,
                    criterion.source,
                    criterion.confidence,
                    criterion.created_at,
                    json.dumps(criterion.metadata_json),
                ),
            )
        return criterion

    def save_criteria(self, criteria: List[ICPCriterionEntity]) -> None:
        if not criteria:
            return
        sql = """
            INSERT INTO icp_criteria (
                id, icp_version_id, category, field, operator, value_json,
                weight, requirement_type, source, confidence, created_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                category = excluded.category,
                field = excluded.field,
                operator = excluded.operator,
                value_json = excluded.value_json,
                weight = excluded.weight,
                requirement_type = excluded.requirement_type,
                source = excluded.source,
                confidence = excluded.confidence,
                metadata_json = excluded.metadata_json;
        """
        params = [
            (
                c.id,
                c.icp_version_id,
                c.category,
                c.field,
                c.operator,
                json.dumps(c.value_json),
                c.weight,
                c.requirement_type,
                c.source,
                c.confidence,
                c.created_at,
                json.dumps(c.metadata_json),
            )
            for c in criteria
        ]
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.executemany(sql, params)

    def list_criteria(
        self, icp_version_id: str, category: Optional[str] = None
    ) -> List[ICPCriterionEntity]:
        sql = "SELECT * FROM icp_criteria WHERE icp_version_id = ?"
        params: List[Any] = [icp_version_id]
        if category:
            sql += " AND category = ?"
            params.append(category)

        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(sql, params).fetchall()
            return [
                ICPCriterionEntity(
                    id=r["id"],
                    icp_version_id=r["icp_version_id"],
                    category=r["category"],
                    field=r["field"],
                    operator=r["operator"],
                    value_json=self._parse_json(r["value_json"]),
                    weight=r["weight"],
                    requirement_type=r["requirement_type"],
                    source=r["source"],
                    confidence=r["confidence"],
                    created_at=r["created_at"],
                    metadata_json=self._parse_json(r["metadata_json"]),
                )
                for r in rows
            ]

    # --- Exclusions ---

    def save_exclusion(self, exclusion: ICPExclusionEntity) -> ICPExclusionEntity:
        sql = """
            INSERT INTO icp_exclusions (
                id, icp_version_id, rule_type, field, operator, value_json, reason, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                rule_type = excluded.rule_type,
                field = excluded.field,
                operator = excluded.operator,
                value_json = excluded.value_json,
                reason = excluded.reason;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    exclusion.id,
                    exclusion.icp_version_id,
                    exclusion.rule_type,
                    exclusion.field,
                    exclusion.operator,
                    json.dumps(exclusion.value_json),
                    exclusion.reason,
                    exclusion.created_at,
                ),
            )
        return exclusion

    def save_exclusions(self, exclusions: List[ICPExclusionEntity]) -> None:
        if not exclusions:
            return
        sql = """
            INSERT INTO icp_exclusions (
                id, icp_version_id, rule_type, field, operator, value_json, reason, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                rule_type = excluded.rule_type,
                field = excluded.field,
                operator = excluded.operator,
                value_json = excluded.value_json,
                reason = excluded.reason;
        """
        params = [
            (
                e.id,
                e.icp_version_id,
                e.rule_type,
                e.field,
                e.operator,
                json.dumps(e.value_json),
                e.reason,
                e.created_at,
            )
            for e in exclusions
        ]
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.executemany(sql, params)

    def list_exclusions(self, icp_version_id: str) -> List[ICPExclusionEntity]:
        sql = "SELECT * FROM icp_exclusions WHERE icp_version_id = ?"
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(sql, (icp_version_id,)).fetchall()
            return [
                ICPExclusionEntity(
                    id=r["id"],
                    icp_version_id=r["icp_version_id"],
                    rule_type=r["rule_type"],
                    field=r["field"],
                    operator=r["operator"],
                    value_json=self._parse_json(r["value_json"]),
                    reason=r["reason"],
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    # --- Personas ---

    def save_persona(self, persona: ICPPersonaEntity) -> ICPPersonaEntity:
        sql = """
            INSERT INTO icp_personas (
                id, icp_version_id, name, department, seniority,
                title_patterns, responsibilities, persona_category,
                priority, confidence, created_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                department = excluded.department,
                seniority = excluded.seniority,
                title_patterns = excluded.title_patterns,
                responsibilities = excluded.responsibilities,
                persona_category = excluded.persona_category,
                priority = excluded.priority,
                confidence = excluded.confidence,
                metadata_json = excluded.metadata_json;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    persona.id,
                    persona.icp_version_id,
                    persona.name,
                    persona.department,
                    persona.seniority,
                    json.dumps(persona.title_patterns),
                    json.dumps(persona.responsibilities),
                    persona.persona_category,
                    persona.priority,
                    persona.confidence,
                    persona.created_at,
                    json.dumps(persona.metadata_json),
                ),
            )
        return persona

    def save_personas(self, personas: List[ICPPersonaEntity]) -> None:
        if not personas:
            return
        sql = """
            INSERT INTO icp_personas (
                id, icp_version_id, name, department, seniority,
                title_patterns, responsibilities, persona_category,
                priority, confidence, created_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                department = excluded.department,
                seniority = excluded.seniority,
                title_patterns = excluded.title_patterns,
                responsibilities = excluded.responsibilities,
                persona_category = excluded.persona_category,
                priority = excluded.priority,
                confidence = excluded.confidence,
                metadata_json = excluded.metadata_json;
        """
        params = [
            (
                p.id,
                p.icp_version_id,
                p.name,
                p.department,
                p.seniority,
                json.dumps(p.title_patterns),
                json.dumps(p.responsibilities),
                p.persona_category,
                p.priority,
                p.confidence,
                p.created_at,
                json.dumps(p.metadata_json),
            )
            for p in personas
        ]
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.executemany(sql, params)

    def list_personas(self, icp_version_id: str) -> List[ICPPersonaEntity]:
        sql = "SELECT * FROM icp_personas WHERE icp_version_id = ? ORDER BY priority ASC"
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(sql, (icp_version_id,)).fetchall()
            return [
                ICPPersonaEntity(
                    id=r["id"],
                    icp_version_id=r["icp_version_id"],
                    name=r["name"],
                    department=r["department"],
                    seniority=r["seniority"],
                    title_patterns=self._parse_json(r["title_patterns"]),
                    responsibilities=self._parse_json(r["responsibilities"]),
                    persona_category=r["persona_category"],
                    priority=r["priority"],
                    confidence=r["confidence"],
                    created_at=r["created_at"],
                    metadata_json=self._parse_json(r["metadata_json"]),
                )
                for r in rows
            ]

    # --- Company Scores ---

    def save_company_score(self, score: ICPCompanyScoreEntity) -> ICPCompanyScoreEntity:
        sql = """
            INSERT INTO icp_company_scores (
                id, icp_version_id, company_id, fit_score, data_confidence,
                status, evaluated_at, valid_until, fingerprint, explanation_json, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(icp_version_id, company_id) DO UPDATE SET
                fit_score = excluded.fit_score,
                data_confidence = excluded.data_confidence,
                status = excluded.status,
                evaluated_at = excluded.evaluated_at,
                valid_until = excluded.valid_until,
                fingerprint = excluded.fingerprint,
                explanation_json = excluded.explanation_json,
                metadata_json = excluded.metadata_json;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    score.id,
                    score.icp_version_id,
                    score.company_id,
                    score.fit_score,
                    score.data_confidence,
                    score.status,
                    score.evaluated_at,
                    score.valid_until,
                    score.fingerprint,
                    json.dumps(score.explanation_json),
                    json.dumps(score.metadata_json),
                ),
            )
        return score

    def get_company_score(
        self, icp_version_id: str, company_id: str
    ) -> Optional[ICPCompanyScoreEntity]:
        sql = "SELECT * FROM icp_company_scores WHERE icp_version_id = ? AND company_id = ?"
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute(sql, (icp_version_id, company_id)).fetchone()
            if not row:
                return None
            return ICPCompanyScoreEntity(
                id=row["id"],
                icp_version_id=row["icp_version_id"],
                company_id=row["company_id"],
                fit_score=row["fit_score"],
                data_confidence=row["data_confidence"],
                status=row["status"],
                evaluated_at=row["evaluated_at"],
                valid_until=row["valid_until"],
                fingerprint=row["fingerprint"],
                explanation_json=self._parse_json(row["explanation_json"]),
                metadata_json=self._parse_json(row["metadata_json"]),
            )

    def list_company_scores(
        self,
        icp_version_id: str,
        min_fit: float = 0.0,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[ICPCompanyScoreEntity]:
        conditions = ["icp_version_id = ?", "fit_score >= ?"]
        params: List[Any] = [icp_version_id, min_fit]
        if status:
            conditions.append("status = ?")
            params.append(status)

        sql = f"""
            SELECT * FROM icp_company_scores
            WHERE {' AND '.join(conditions)}
            ORDER BY fit_score DESC, data_confidence DESC
            LIMIT ?
        """
        params.append(limit)

        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(sql, params).fetchall()
            return [
                ICPCompanyScoreEntity(
                    id=r["id"],
                    icp_version_id=r["icp_version_id"],
                    company_id=r["company_id"],
                    fit_score=r["fit_score"],
                    data_confidence=r["data_confidence"],
                    status=r["status"],
                    evaluated_at=r["evaluated_at"],
                    valid_until=r["valid_until"],
                    fingerprint=r["fingerprint"],
                    explanation_json=self._parse_json(r["explanation_json"]),
                    metadata_json=self._parse_json(r["metadata_json"]),
                )
                for r in rows
            ]

    # --- Person Scores ---

    def save_person_score(self, score: ICPPersonScoreEntity) -> ICPPersonScoreEntity:
        sql = """
            INSERT INTO icp_person_scores (
                id, icp_version_id, person_id, company_id, persona_id,
                fit_score, employment_confidence, role_matched, evaluated_at,
                explanation_json, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(icp_version_id, person_id) DO UPDATE SET
                company_id = excluded.company_id,
                persona_id = excluded.persona_id,
                fit_score = excluded.fit_score,
                employment_confidence = excluded.employment_confidence,
                role_matched = excluded.role_matched,
                evaluated_at = excluded.evaluated_at,
                explanation_json = excluded.explanation_json,
                metadata_json = excluded.metadata_json;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    score.id,
                    score.icp_version_id,
                    score.person_id,
                    score.company_id,
                    score.persona_id,
                    score.fit_score,
                    score.employment_confidence,
                    score.role_matched,
                    score.evaluated_at,
                    json.dumps(score.explanation_json),
                    json.dumps(score.metadata_json),
                ),
            )
        return score

    def get_person_score(
        self, icp_version_id: str, person_id: str
    ) -> Optional[ICPPersonScoreEntity]:
        sql = "SELECT * FROM icp_person_scores WHERE icp_version_id = ? AND person_id = ?"
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute(sql, (icp_version_id, person_id)).fetchone()
            if not row:
                return None
            return ICPPersonScoreEntity(
                id=row["id"],
                icp_version_id=row["icp_version_id"],
                person_id=row["person_id"],
                company_id=row["company_id"],
                persona_id=row["persona_id"],
                fit_score=row["fit_score"],
                employment_confidence=row["employment_confidence"],
                role_matched=row["role_matched"],
                evaluated_at=row["evaluated_at"],
                explanation_json=self._parse_json(row["explanation_json"]),
                metadata_json=self._parse_json(row["metadata_json"]),
            )

    def list_person_scores(
        self, icp_version_id: str, company_id: Optional[str] = None, limit: int = 50
    ) -> List[ICPPersonScoreEntity]:
        conditions = ["icp_version_id = ?"]
        params: List[Any] = [icp_version_id]
        if company_id:
            conditions.append("company_id = ?")
            params.append(company_id)

        sql = f"""
            SELECT * FROM icp_person_scores
            WHERE {' AND '.join(conditions)}
            ORDER BY fit_score DESC, employment_confidence DESC
            LIMIT ?
        """
        params.append(limit)

        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(sql, params).fetchall()
            return [
                ICPPersonScoreEntity(
                    id=r["id"],
                    icp_version_id=r["icp_version_id"],
                    person_id=r["person_id"],
                    company_id=r["company_id"],
                    persona_id=r["persona_id"],
                    fit_score=r["fit_score"],
                    employment_confidence=r["employment_confidence"],
                    role_matched=r["role_matched"],
                    evaluated_at=r["evaluated_at"],
                    explanation_json=self._parse_json(r["explanation_json"]),
                    metadata_json=self._parse_json(r["metadata_json"]),
                )
                for r in rows
            ]

    # --- Evidence ---

    def save_evidence(self, evidence: ICPEvidenceEntity) -> ICPEvidenceEntity:
        sql = """
            INSERT INTO icp_evidence (
                id, icp_version_id, criterion_id, source_type, source_id,
                fact_id, evidence_id, confidence, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                criterion_id = excluded.criterion_id,
                source_type = excluded.source_type,
                source_id = excluded.source_id,
                fact_id = excluded.fact_id,
                evidence_id = excluded.evidence_id,
                confidence = excluded.confidence;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    evidence.id,
                    evidence.icp_version_id,
                    evidence.criterion_id,
                    evidence.source_type,
                    evidence.source_id,
                    evidence.fact_id,
                    evidence.evidence_id,
                    evidence.confidence,
                    evidence.created_at,
                ),
            )
        return evidence

    def save_evidence_batch(self, evidence_list: List[ICPEvidenceEntity]) -> None:
        if not evidence_list:
            return
        sql = """
            INSERT INTO icp_evidence (
                id, icp_version_id, criterion_id, source_type, source_id,
                fact_id, evidence_id, confidence, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                criterion_id = excluded.criterion_id,
                source_type = excluded.source_type,
                source_id = excluded.source_id,
                fact_id = excluded.fact_id,
                evidence_id = excluded.evidence_id,
                confidence = excluded.confidence;
        """
        params = [
            (
                ev.id,
                ev.icp_version_id,
                ev.criterion_id,
                ev.source_type,
                ev.source_id,
                ev.fact_id,
                ev.evidence_id,
                ev.confidence,
                ev.created_at,
            )
            for ev in evidence_list
        ]
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.executemany(sql, params)

    def list_evidence(
        self, icp_version_id: str, criterion_id: Optional[str] = None
    ) -> List[ICPEvidenceEntity]:
        sql = "SELECT * FROM icp_evidence WHERE icp_version_id = ?"
        params: List[Any] = [icp_version_id]
        if criterion_id:
            sql += " AND criterion_id = ?"
            params.append(criterion_id)

        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(sql, params).fetchall()
            return [
                ICPEvidenceEntity(
                    id=r["id"],
                    icp_version_id=r["icp_version_id"],
                    criterion_id=r["criterion_id"],
                    source_type=r["source_type"],
                    source_id=r["source_id"],
                    fact_id=r["fact_id"],
                    evidence_id=r["evidence_id"],
                    confidence=r["confidence"],
                    created_at=r["created_at"],
                )
                for r in rows
            ]
