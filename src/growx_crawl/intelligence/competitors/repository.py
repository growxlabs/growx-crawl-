"""
GrowX Competitor Graph Repository.
Persistence layer for competitive relationships, evidence, rejection memory, and summaries.
"""

import json
import logging
import sqlite3
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from growx_crawl.intelligence.competitors.models import (
    CompanyCompetitorSummary,
    CompetitorEvidenceEntity,
    CompetitorRejectionEntity,
    CompetitorRelationshipEntity,
)
from growx_crawl.intelligence.competitors.policies import canonical_pair
from growx_crawl.storage.db import get_db
from growx_crawl.storage.sqlite.canonical import init_sqlite_canonical_tables

logger = logging.getLogger("growx_crawl.intelligence.competitors.repository")


class BaseCompetitorRepository(ABC):
    @abstractmethod
    def save_relationship(self, rel: CompetitorRelationshipEntity) -> CompetitorRelationshipEntity: ...

    @abstractmethod
    def get_relationship(self, relationship_id: str) -> Optional[CompetitorRelationshipEntity]: ...

    @abstractmethod
    def get_relationship_by_pair(
        self, canonical_pair: str, relationship_type: Optional[str] = None
    ) -> Optional[CompetitorRelationshipEntity]: ...

    @abstractmethod
    def list_relationships(
        self,
        company_id: str,
        status: Optional[str] = None,
        relationship_type: Optional[str] = None,
        min_strength: float = 0.0,
        limit: int = 50,
    ) -> List[CompetitorRelationshipEntity]: ...

    @abstractmethod
    def save_evidence(self, evidence: CompetitorEvidenceEntity) -> CompetitorEvidenceEntity: ...

    @abstractmethod
    def list_evidence(self, relationship_id: str) -> List[CompetitorEvidenceEntity]: ...

    @abstractmethod
    def save_rejection(self, rejection: CompetitorRejectionEntity) -> None: ...

    @abstractmethod
    def is_rejected(self, canonical_pair: str) -> bool: ...

    @abstractmethod
    def save_summary(self, summary: CompanyCompetitorSummary) -> None: ...

    @abstractmethod
    def get_summary(self, company_id: str) -> Optional[CompanyCompetitorSummary]: ...

    @abstractmethod
    def get_corporate_relationship(self, company_a: str, company_b: str) -> Optional[str]: ...


class SqliteCompetitorRepository(BaseCompetitorRepository):
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def _ensure_schema(self, conn: sqlite3.Connection):
        init_sqlite_canonical_tables(conn)

    def save_relationship(self, rel: CompetitorRelationshipEntity) -> CompetitorRelationshipEntity:
        sql = """
            INSERT INTO competitor_relationships (
                id, company_id, competitor_company_id, canonical_pair, relationship_type,
                status, confidence, strength, market_overlap, offering_overlap,
                customer_overlap, geography_overlap, evidence_count, first_seen_at,
                last_seen_at, last_verified_at, valid_until, scoring_version,
                policy_version, reasons, created_at, updated_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (canonical_pair, relationship_type) DO UPDATE SET
                status = excluded.status,
                confidence = excluded.confidence,
                strength = excluded.strength,
                market_overlap = excluded.market_overlap,
                offering_overlap = excluded.offering_overlap,
                customer_overlap = excluded.customer_overlap,
                geography_overlap = excluded.geography_overlap,
                evidence_count = excluded.evidence_count,
                last_seen_at = excluded.last_seen_at,
                last_verified_at = excluded.last_verified_at,
                valid_until = excluded.valid_until,
                scoring_version = excluded.scoring_version,
                policy_version = excluded.policy_version,
                reasons = excluded.reasons,
                updated_at = excluded.updated_at,
                metadata_json = excluded.metadata_json;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    rel.id,
                    rel.company_id,
                    rel.competitor_company_id,
                    rel.canonical_pair,
                    rel.relationship_type,
                    rel.status,
                    rel.confidence,
                    rel.strength,
                    rel.market_overlap,
                    rel.offering_overlap,
                    rel.customer_overlap,
                    rel.geography_overlap,
                    rel.evidence_count,
                    rel.first_seen_at,
                    rel.last_seen_at,
                    rel.last_verified_at,
                    rel.valid_until,
                    rel.scoring_version,
                    rel.policy_version,
                    json.dumps(rel.reasons),
                    rel.created_at,
                    rel.updated_at,
                    json.dumps(rel.metadata_json),
                ),
            )
        return rel

    def get_relationship(self, relationship_id: str) -> Optional[CompetitorRelationshipEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute(
                "SELECT * FROM competitor_relationships WHERE id = ?",
                (relationship_id,),
            ).fetchone()
            return self._row_to_relationship(row) if row else None

    def get_relationship_by_pair(
        self, canonical_pair: str, relationship_type: Optional[str] = None
    ) -> Optional[CompetitorRelationshipEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            if relationship_type:
                row = conn.execute(
                    "SELECT * FROM competitor_relationships WHERE canonical_pair = ? AND relationship_type = ?",
                    (canonical_pair, relationship_type),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT * FROM competitor_relationships WHERE canonical_pair = ? ORDER BY strength DESC LIMIT 1",
                    (canonical_pair,),
                ).fetchone()
            return self._row_to_relationship(row) if row else None

    def list_relationships(
        self,
        company_id: str,
        status: Optional[str] = None,
        relationship_type: Optional[str] = None,
        min_strength: float = 0.0,
        limit: int = 50,
    ) -> List[CompetitorRelationshipEntity]:
        conditions = ["(company_id = ? OR competitor_company_id = ?)", "strength >= ?"]
        params: list = [company_id, company_id, min_strength]

        if status:
            conditions.append("status = ?")
            params.append(status)
        if relationship_type:
            conditions.append("relationship_type = ?")
            params.append(relationship_type)

        where = " AND ".join(conditions)
        sql = f"SELECT * FROM competitor_relationships WHERE {where} ORDER BY strength DESC LIMIT ?"
        params.append(limit)

        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(sql, params).fetchall()
            return [self._row_to_relationship(r) for r in rows]

    def save_evidence(self, evidence: CompetitorEvidenceEntity) -> CompetitorEvidenceEntity:
        sql = """
            INSERT INTO competitor_evidence (
                id, relationship_id, source_id, fact_id, observation_id,
                object_ref_id, evidence_type, support_type, captured_at,
                confidence, created_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO NOTHING;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    evidence.id,
                    evidence.relationship_id,
                    evidence.source_id,
                    evidence.fact_id,
                    evidence.observation_id,
                    evidence.object_ref_id,
                    evidence.evidence_type,
                    evidence.support_type,
                    evidence.captured_at,
                    evidence.confidence,
                    evidence.created_at,
                    json.dumps(evidence.metadata_json),
                ),
            )
        return evidence

    def list_evidence(self, relationship_id: str) -> List[CompetitorEvidenceEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(
                "SELECT * FROM competitor_evidence WHERE relationship_id = ? ORDER BY captured_at DESC",
                (relationship_id,),
            ).fetchall()
            return [self._row_to_evidence(r) for r in rows]

    def save_rejection(self, rejection: CompetitorRejectionEntity) -> None:
        sql = """
            INSERT INTO competitor_rejections (
                canonical_pair, company_a, company_b, reason_code,
                rejected_at, policy_version, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (canonical_pair) DO UPDATE SET
                reason_code = excluded.reason_code,
                rejected_at = excluded.rejected_at,
                metadata_json = excluded.metadata_json;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    rejection.canonical_pair,
                    rejection.company_a,
                    rejection.company_b,
                    rejection.reason_code,
                    rejection.rejected_at,
                    rejection.policy_version,
                    json.dumps(rejection.metadata_json),
                ),
            )

    def is_rejected(self, pair_key: str) -> bool:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute(
                "SELECT 1 FROM competitor_rejections WHERE canonical_pair = ?",
                (pair_key,),
            ).fetchone()
            return row is not None

    def save_summary(self, summary: CompanyCompetitorSummary) -> None:
        sql = """
            INSERT INTO company_competitor_summaries (
                company_id, top_competitor_ids, competitor_count,
                verified_competitor_count, last_refreshed_at, updated_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (company_id) DO UPDATE SET
                top_competitor_ids = excluded.top_competitor_ids,
                competitor_count = excluded.competitor_count,
                verified_competitor_count = excluded.verified_competitor_count,
                last_refreshed_at = excluded.last_refreshed_at,
                updated_at = excluded.updated_at,
                metadata_json = excluded.metadata_json;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    summary.company_id,
                    json.dumps(summary.top_competitor_ids),
                    summary.competitor_count,
                    summary.verified_competitor_count,
                    summary.last_refreshed_at,
                    summary.updated_at,
                    json.dumps(summary.metadata_json),
                ),
            )

    def get_summary(self, company_id: str) -> Optional[CompanyCompetitorSummary]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute(
                "SELECT * FROM company_competitor_summaries WHERE company_id = ?",
                (company_id,),
            ).fetchone()
            if not row:
                return None
            top_ids = row["top_competitor_ids"]
            if isinstance(top_ids, str):
                top_ids = json.loads(top_ids)
            meta = row["metadata_json"]
            if isinstance(meta, str):
                meta = json.loads(meta)
            return CompanyCompetitorSummary(
                company_id=row["company_id"],
                top_competitor_ids=top_ids or [],
                competitor_count=row["competitor_count"],
                verified_competitor_count=row["verified_competitor_count"],
                last_refreshed_at=row["last_refreshed_at"],
                updated_at=row["updated_at"],
                metadata_json=meta or {},
            )

    def get_corporate_relationship(self, company_a: str, company_b: str) -> Optional[str]:
        """Queries canonical_company_relationships or company_relationships for structural bindings."""
        for tbl in ("canonical_company_relationships", "company_relationships"):
            sql = f"""
                SELECT relationship_type FROM {tbl}
                WHERE (from_company_id = ? AND to_company_id = ?)
                   OR (from_company_id = ? AND to_company_id = ?)
                LIMIT 1
            """
            try:
                with get_db(self.db_path) as conn:
                    row = conn.execute(sql, (company_a, company_b, company_b, company_a)).fetchone()
                    if row:
                        return row["relationship_type"]
            except Exception:
                continue
        return None

    def _row_to_relationship(self, r) -> CompetitorRelationshipEntity:
        reasons = r["reasons"]
        if isinstance(reasons, str):
            reasons = json.loads(reasons)
        meta = r["metadata_json"]
        if isinstance(meta, str):
            meta = json.loads(meta)
        return CompetitorRelationshipEntity(
            id=r["id"],
            company_id=r["company_id"],
            competitor_company_id=r["competitor_company_id"],
            canonical_pair=r["canonical_pair"],
            relationship_type=r["relationship_type"],
            status=r["status"],
            confidence=float(r["confidence"]),
            strength=float(r["strength"]),
            market_overlap=float(r["market_overlap"]),
            offering_overlap=float(r["offering_overlap"]),
            customer_overlap=float(r["customer_overlap"]),
            geography_overlap=float(r["geography_overlap"]),
            evidence_count=int(r["evidence_count"]),
            first_seen_at=r["first_seen_at"],
            last_seen_at=r["last_seen_at"],
            last_verified_at=r["last_verified_at"],
            valid_until=r["valid_until"],
            scoring_version=r["scoring_version"],
            policy_version=r["policy_version"],
            reasons=reasons or [],
            created_at=r["created_at"],
            updated_at=r["updated_at"],
            metadata_json=meta or {},
        )

    def _row_to_evidence(self, r) -> CompetitorEvidenceEntity:
        meta = r["metadata_json"]
        if isinstance(meta, str):
            meta = json.loads(meta)
        return CompetitorEvidenceEntity(
            id=r["id"],
            relationship_id=r["relationship_id"],
            source_id=r["source_id"],
            fact_id=r["fact_id"],
            observation_id=r["observation_id"],
            object_ref_id=r["object_ref_id"],
            evidence_type=r["evidence_type"],
            support_type=r["support_type"],
            captured_at=r["captured_at"],
            confidence=float(r["confidence"]),
            created_at=r["created_at"],
            metadata_json=meta or {},
        )
