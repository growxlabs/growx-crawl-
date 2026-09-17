"""
GrowX Prospect Ranking Repository.
Persistence layer for prospects, ranking profiles, scores, historical snapshots, and explanations.
"""

import json
import logging
import sqlite3
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from growx_crawl.scoring.models import (
    ProspectEntity,
    ProspectScoreEntity,
    ProspectScoreHistoryEntity,
    RankingExplanationEntity,
    RankingProfileEntity,
)
from growx_crawl.storage.db import get_db
from growx_crawl.storage.sqlite.canonical import init_sqlite_canonical_tables

logger = logging.getLogger("growx_crawl.scoring.repository")


class BaseRankingRepository(ABC):
    @abstractmethod
    def save_prospect(self, prospect: ProspectEntity) -> ProspectEntity: ...

    @abstractmethod
    def get_prospect(self, prospect_id: str) -> Optional[ProspectEntity]: ...

    @abstractmethod
    def get_prospect_by_entity(
        self, project_id: str, company_id: str, person_id: Optional[str] = None
    ) -> Optional[ProspectEntity]: ...

    @abstractmethod
    def list_prospects(
        self, project_id: Optional[str] = None, status: Optional[str] = None, limit: int = 50
    ) -> List[ProspectEntity]: ...

    @abstractmethod
    def save_profile(self, profile: RankingProfileEntity) -> RankingProfileEntity: ...

    @abstractmethod
    def get_profile(self, profile_id: str) -> Optional[RankingProfileEntity]: ...

    @abstractmethod
    def list_profiles(self, limit: int = 50) -> List[RankingProfileEntity]: ...

    @abstractmethod
    def save_score(self, score: ProspectScoreEntity) -> ProspectScoreEntity: ...

    @abstractmethod
    def get_score(self, score_id: str) -> Optional[ProspectScoreEntity]: ...

    @abstractmethod
    def get_latest_prospect_score(
        self, prospect_id: str, ranking_profile_id: Optional[str] = None
    ) -> Optional[ProspectScoreEntity]: ...

    @abstractmethod
    def list_scores(
        self,
        ranking_profile_id: Optional[str] = None,
        status: Optional[str] = None,
        min_score: float = 0.0,
        limit: int = 50,
    ) -> List[ProspectScoreEntity]: ...

    @abstractmethod
    def save_score_history(self, history: ProspectScoreHistoryEntity) -> ProspectScoreHistoryEntity: ...

    @abstractmethod
    def list_score_history(self, prospect_id: str) -> List[ProspectScoreHistoryEntity]: ...

    @abstractmethod
    def save_explanations(self, explanations: List[RankingExplanationEntity]) -> None: ...

    @abstractmethod
    def list_explanations(self, score_id: str) -> List[RankingExplanationEntity]: ...


class SqliteRankingRepository(BaseRankingRepository):
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

    # --- Prospects ---

    def save_prospect(self, prospect: ProspectEntity) -> ProspectEntity:
        sql = """
            INSERT INTO prospects (
                id, project_id, company_id, person_id, icp_version_id,
                status, created_at, updated_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                status = excluded.status,
                icp_version_id = excluded.icp_version_id,
                updated_at = excluded.updated_at,
                metadata_json = excluded.metadata_json;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    prospect.id,
                    prospect.project_id,
                    prospect.company_id,
                    prospect.person_id,
                    prospect.icp_version_id,
                    prospect.status,
                    prospect.created_at,
                    prospect.updated_at,
                    json.dumps(prospect.metadata_json),
                ),
            )
        return prospect

    def get_prospect(self, prospect_id: str) -> Optional[ProspectEntity]:
        sql = "SELECT * FROM prospects WHERE id = ?"
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute(sql, (prospect_id,)).fetchone()
            if not row:
                return None
            return ProspectEntity(
                id=row["id"],
                project_id=row["project_id"],
                company_id=row["company_id"],
                person_id=row["person_id"],
                icp_version_id=row["icp_version_id"],
                status=row["status"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                metadata_json=self._parse_json(row["metadata_json"]),
            )

    def get_prospect_by_entity(
        self, project_id: str, company_id: str, person_id: Optional[str] = None
    ) -> Optional[ProspectEntity]:
        if person_id:
            sql = "SELECT * FROM prospects WHERE project_id = ? AND company_id = ? AND person_id = ?"
            params = (project_id, company_id, person_id)
        else:
            sql = "SELECT * FROM prospects WHERE project_id = ? AND company_id = ? AND (person_id IS NULL OR person_id = '')"
            params = (project_id, company_id)

        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute(sql, params).fetchone()
            if not row:
                return None
            return ProspectEntity(
                id=row["id"],
                project_id=row["project_id"],
                company_id=row["company_id"],
                person_id=row["person_id"],
                icp_version_id=row["icp_version_id"],
                status=row["status"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                metadata_json=self._parse_json(row["metadata_json"]),
            )

    def list_prospects(
        self, project_id: Optional[str] = None, status: Optional[str] = None, limit: int = 50
    ) -> List[ProspectEntity]:
        conditions = []
        params: List[Any] = []
        if project_id:
            conditions.append("project_id = ?")
            params.append(project_id)
        if status:
            conditions.append("status = ?")
            params.append(status)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"SELECT * FROM prospects {where} ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(sql, params).fetchall()
            return [
                ProspectEntity(
                    id=r["id"],
                    project_id=r["project_id"],
                    company_id=r["company_id"],
                    person_id=r["person_id"],
                    icp_version_id=r["icp_version_id"],
                    status=r["status"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                    metadata_json=self._parse_json(r["metadata_json"]),
                )
                for r in rows
            ]

    # --- Ranking Profiles ---

    def save_profile(self, profile: RankingProfileEntity) -> RankingProfileEntity:
        sql = """
            INSERT INTO ranking_profiles (
                id, name, version, config_json, enabled, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                config_json = excluded.config_json,
                enabled = excluded.enabled,
                updated_at = excluded.updated_at;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    profile.id,
                    profile.name,
                    profile.version,
                    json.dumps(profile.config_json),
                    1 if profile.enabled else 0,
                    profile.created_at,
                    profile.updated_at,
                ),
            )
        return profile

    def get_profile(self, profile_id: str) -> Optional[RankingProfileEntity]:
        sql = "SELECT * FROM ranking_profiles WHERE id = ? OR name = ?"
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute(sql, (profile_id, profile_id)).fetchone()
            if not row:
                return None
            return RankingProfileEntity(
                id=row["id"],
                name=row["name"],
                version=row["version"],
                config_json=self._parse_json(row["config_json"]),
                enabled=bool(row["enabled"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    def list_profiles(self, limit: int = 50) -> List[RankingProfileEntity]:
        sql = "SELECT * FROM ranking_profiles ORDER BY created_at DESC LIMIT ?"
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(sql, (limit,)).fetchall()
            return [
                RankingProfileEntity(
                    id=r["id"],
                    name=r["name"],
                    version=r["version"],
                    config_json=self._parse_json(r["config_json"]),
                    enabled=bool(r["enabled"]),
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
                for r in rows
            ]

    # --- Prospect Scores ---

    def save_score(self, score: ProspectScoreEntity) -> ProspectScoreEntity:
        sql = """
            INSERT INTO prospect_scores (
                id, prospect_id, company_id, person_id, icp_version_id, ranking_profile_id,
                account_score, person_score, signal_score, timing_score, quality_score,
                verification_score, contactability_score, penalty_score, raw_score,
                confidence_factor, final_score, status, rank_position, calculated_at,
                valid_until, fingerprint, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(prospect_id, ranking_profile_id) DO UPDATE SET
                id = excluded.id,
                account_score = excluded.account_score,
                person_score = excluded.person_score,
                signal_score = excluded.signal_score,
                timing_score = excluded.timing_score,
                quality_score = excluded.quality_score,
                verification_score = excluded.verification_score,
                contactability_score = excluded.contactability_score,
                penalty_score = excluded.penalty_score,
                raw_score = excluded.raw_score,
                confidence_factor = excluded.confidence_factor,
                final_score = excluded.final_score,
                status = excluded.status,
                rank_position = excluded.rank_position,
                calculated_at = excluded.calculated_at,
                valid_until = excluded.valid_until,
                fingerprint = excluded.fingerprint,
                metadata_json = excluded.metadata_json;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    score.id,
                    score.prospect_id,
                    score.company_id,
                    score.person_id,
                    score.icp_version_id,
                    score.ranking_profile_id,
                    score.account_score,
                    score.person_score,
                    score.signal_score,
                    score.timing_score,
                    score.quality_score,
                    score.verification_score,
                    score.contactability_score,
                    score.penalty_score,
                    score.raw_score,
                    score.confidence_factor,
                    score.final_score,
                    score.status,
                    score.rank_position,
                    score.calculated_at,
                    score.valid_until,
                    score.fingerprint,
                    json.dumps(score.metadata_json),
                ),
            )
        return score

    def get_score(self, score_id: str) -> Optional[ProspectScoreEntity]:
        sql = "SELECT * FROM prospect_scores WHERE id = ?"
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute(sql, (score_id,)).fetchone()
            if not row:
                return None
            return ProspectScoreEntity(
                id=row["id"],
                prospect_id=row["prospect_id"],
                company_id=row["company_id"],
                person_id=row["person_id"],
                icp_version_id=row["icp_version_id"],
                ranking_profile_id=row["ranking_profile_id"],
                account_score=row["account_score"],
                person_score=row["person_score"],
                signal_score=row["signal_score"],
                timing_score=row["timing_score"],
                quality_score=row["quality_score"],
                verification_score=row["verification_score"],
                contactability_score=row["contactability_score"],
                penalty_score=row["penalty_score"],
                raw_score=row["raw_score"],
                confidence_factor=row["confidence_factor"],
                final_score=row["final_score"],
                status=row["status"],
                rank_position=row["rank_position"],
                calculated_at=row["calculated_at"],
                valid_until=row["valid_until"],
                fingerprint=row["fingerprint"],
                metadata_json=self._parse_json(row["metadata_json"]),
            )

    def get_latest_prospect_score(
        self, prospect_id: str, ranking_profile_id: Optional[str] = None
    ) -> Optional[ProspectScoreEntity]:
        if ranking_profile_id:
            sql = "SELECT * FROM prospect_scores WHERE prospect_id = ? AND ranking_profile_id = ?"
            params = (prospect_id, ranking_profile_id)
        else:
            sql = "SELECT * FROM prospect_scores WHERE prospect_id = ? ORDER BY calculated_at DESC LIMIT 1"
            params = (prospect_id,)

        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute(sql, params).fetchone()
            if not row:
                return None
            return ProspectScoreEntity(
                id=row["id"],
                prospect_id=row["prospect_id"],
                company_id=row["company_id"],
                person_id=row["person_id"],
                icp_version_id=row["icp_version_id"],
                ranking_profile_id=row["ranking_profile_id"],
                account_score=row["account_score"],
                person_score=row["person_score"],
                signal_score=row["signal_score"],
                timing_score=row["timing_score"],
                quality_score=row["quality_score"],
                verification_score=row["verification_score"],
                contactability_score=row["contactability_score"],
                penalty_score=row["penalty_score"],
                raw_score=row["raw_score"],
                confidence_factor=row["confidence_factor"],
                final_score=row["final_score"],
                status=row["status"],
                rank_position=row["rank_position"],
                calculated_at=row["calculated_at"],
                valid_until=row["valid_until"],
                fingerprint=row["fingerprint"],
                metadata_json=self._parse_json(row["metadata_json"]),
            )

    def list_scores(
        self,
        ranking_profile_id: Optional[str] = None,
        status: Optional[str] = None,
        min_score: float = 0.0,
        limit: int = 50,
    ) -> List[ProspectScoreEntity]:
        conditions = ["final_score >= ?"]
        params: List[Any] = [min_score]
        if ranking_profile_id:
            conditions.append("ranking_profile_id = ?")
            params.append(ranking_profile_id)
        if status:
            conditions.append("status = ?")
            params.append(status)

        sql = f"""
            SELECT * FROM prospect_scores
            WHERE {' AND '.join(conditions)}
            ORDER BY final_score DESC, raw_score DESC
            LIMIT ?
        """
        params.append(limit)

        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(sql, params).fetchall()
            return [
                ProspectScoreEntity(
                    id=r["id"],
                    prospect_id=r["prospect_id"],
                    company_id=r["company_id"],
                    person_id=r["person_id"],
                    icp_version_id=r["icp_version_id"],
                    ranking_profile_id=r["ranking_profile_id"],
                    account_score=r["account_score"],
                    person_score=r["person_score"],
                    signal_score=r["signal_score"],
                    timing_score=r["timing_score"],
                    quality_score=r["quality_score"],
                    verification_score=r["verification_score"],
                    contactability_score=r["contactability_score"],
                    penalty_score=r["penalty_score"],
                    raw_score=r["raw_score"],
                    confidence_factor=r["confidence_factor"],
                    final_score=r["final_score"],
                    status=r["status"],
                    rank_position=r["rank_position"],
                    calculated_at=r["calculated_at"],
                    valid_until=r["valid_until"],
                    fingerprint=r["fingerprint"],
                    metadata_json=self._parse_json(r["metadata_json"]),
                )
                for r in rows
            ]

    # --- Score History ---

    def save_score_history(self, history: ProspectScoreHistoryEntity) -> ProspectScoreHistoryEntity:
        sql = """
            INSERT INTO prospect_score_history (
                id, prospect_id, score_id, ranking_profile_id, rank_position,
                final_score, status, calculated_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    history.id,
                    history.prospect_id,
                    history.score_id,
                    history.ranking_profile_id,
                    history.rank_position,
                    history.final_score,
                    history.status,
                    history.calculated_at,
                    json.dumps(history.metadata_json),
                ),
            )
        return history

    def list_score_history(self, prospect_id: str) -> List[ProspectScoreHistoryEntity]:
        sql = "SELECT * FROM prospect_score_history WHERE prospect_id = ? ORDER BY calculated_at DESC"
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(sql, (prospect_id,)).fetchall()
            return [
                ProspectScoreHistoryEntity(
                    id=r["id"],
                    prospect_id=r["prospect_id"],
                    score_id=r["score_id"],
                    ranking_profile_id=r["ranking_profile_id"],
                    rank_position=r["rank_position"],
                    final_score=r["final_score"],
                    status=r["status"],
                    calculated_at=r["calculated_at"],
                    metadata_json=self._parse_json(r["metadata_json"]),
                )
                for r in rows
            ]

    # --- Explanations ---

    def save_explanations(self, explanations: List[RankingExplanationEntity]) -> None:
        if not explanations:
            return
        sql = """
            INSERT INTO ranking_explanations (
                id, score_id, reason_code, component, contribution,
                direction, evidence_refs, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = [
            (
                e.id,
                e.score_id,
                e.reason_code,
                e.component,
                e.contribution,
                e.direction,
                json.dumps(e.evidence_refs),
                json.dumps(e.metadata_json),
            )
            for e in explanations
        ]
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.executemany(sql, params)

    def list_explanations(self, score_id: str) -> List[RankingExplanationEntity]:
        sql = "SELECT * FROM ranking_explanations WHERE score_id = ?"
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(sql, (score_id,)).fetchall()
            return [
                RankingExplanationEntity(
                    id=r["id"],
                    score_id=r["score_id"],
                    reason_code=r["reason_code"],
                    component=r["component"],
                    contribution=r["contribution"],
                    direction=r["direction"],
                    evidence_refs=self._parse_json(r["evidence_refs"]),
                    metadata_json=self._parse_json(r["metadata_json"]),
                )
                for r in rows
            ]
