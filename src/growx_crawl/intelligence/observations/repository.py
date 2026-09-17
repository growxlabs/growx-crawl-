from abc import ABC, abstractmethod
import json
import logging
import sqlite3
from typing import Any, Dict, List, Optional

from growx_crawl.intelligence.observations.models import ObservationEntity, ObservationRejectionEntity
from growx_crawl.storage.db import get_db
from growx_crawl.storage.sqlite.canonical import init_sqlite_canonical_tables

logger = logging.getLogger("growx_crawl.intelligence.observations.repository")


class BaseObservationRepository(ABC):
    @abstractmethod
    def get(self, observation_id: str) -> Optional[ObservationEntity]: ...

    @abstractmethod
    def create(self, observation: ObservationEntity) -> ObservationEntity: ...

    @abstractmethod
    def create_batch(self, observations: List[ObservationEntity]) -> int: ...

    @abstractmethod
    def list_by_subject(self, subject_type: str, subject_id: str, limit: int = 100) -> List[ObservationEntity]: ...

    @abstractmethod
    def quarantine(self, rejection: ObservationRejectionEntity) -> ObservationRejectionEntity: ...

    @abstractmethod
    def list_rejections(self, limit: int = 50) -> List[ObservationRejectionEntity]: ...

    @abstractmethod
    def count(self) -> int: ...

    @abstractmethod
    def count_rejections(self) -> int: ...


class SqliteObservationRepository(BaseObservationRepository):
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def _ensure_schema(self, conn: sqlite3.Connection):
        init_sqlite_canonical_tables(conn)

    def get(self, observation_id: str) -> Optional[ObservationEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute("SELECT * FROM canonical_observations WHERE id = ?", (observation_id,)).fetchone()
            return self._row_to_entity(row) if row else None

    def create(self, observation: ObservationEntity) -> ObservationEntity:
        sql = """
            INSERT INTO canonical_observations (
                id, subject_type, subject_id, predicate, raw_value, normalized_value_json,
                value_type, source_id, object_ref_id, observed_at, extractor_name,
                extractor_version, model_run_id, confidence, created_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO NOTHING;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    observation.id,
                    observation.subject_type,
                    observation.subject_id,
                    observation.predicate,
                    observation.raw_value,
                    json.dumps(observation.normalized_value_json),
                    observation.value_type,
                    observation.source_id,
                    observation.object_ref_id,
                    observation.observed_at,
                    observation.extractor_name,
                    observation.extractor_version,
                    observation.model_run_id,
                    observation.confidence,
                    observation.created_at,
                    json.dumps(observation.metadata_json),
                ),
            )
        return observation

    def create_batch(self, observations: List[ObservationEntity]) -> int:
        if not observations:
            return 0
        sql = """
            INSERT INTO canonical_observations (
                id, subject_type, subject_id, predicate, raw_value, normalized_value_json,
                value_type, source_id, object_ref_id, observed_at, extractor_name,
                extractor_version, model_run_id, confidence, created_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO NOTHING;
        """
        params = [
            (
                obs.id,
                obs.subject_type,
                obs.subject_id,
                obs.predicate,
                obs.raw_value,
                json.dumps(obs.normalized_value_json),
                obs.value_type,
                obs.source_id,
                obs.object_ref_id,
                obs.observed_at,
                obs.extractor_name,
                obs.extractor_version,
                obs.model_run_id,
                obs.confidence,
                obs.created_at,
                json.dumps(obs.metadata_json),
            )
            for obs in observations
        ]
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            cur = conn.executemany(sql, params)
            return cur.rowcount

    def list_by_subject(self, subject_type: str, subject_id: str, limit: int = 100) -> List[ObservationEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(
                "SELECT * FROM canonical_observations WHERE subject_type = ? AND subject_id = ? ORDER BY observed_at DESC LIMIT ?",
                (subject_type, subject_id, limit),
            ).fetchall()
            return [self._row_to_entity(r) for r in rows]

    def quarantine(self, rejection: ObservationRejectionEntity) -> ObservationRejectionEntity:
        sql = """
            INSERT INTO canonical_observation_rejections (id, payload_json, reason_code, source_id, created_at, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?);
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    rejection.id,
                    json.dumps(rejection.payload_json),
                    rejection.reason_code,
                    rejection.source_id,
                    rejection.created_at,
                    json.dumps(rejection.metadata_json),
                ),
            )
        return rejection

    def list_rejections(self, limit: int = 50) -> List[ObservationRejectionEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(
                "SELECT * FROM canonical_observation_rejections ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [
                ObservationRejectionEntity(
                    id=r["id"],
                    payload_json=json.loads(r["payload_json"]) if isinstance(r["payload_json"], str) else (r["payload_json"] or {}),
                    reason_code=r["reason_code"],
                    source_id=r["source_id"],
                    created_at=r["created_at"],
                    metadata_json=json.loads(r["metadata_json"]) if isinstance(r["metadata_json"], str) else (r["metadata_json"] or {}),
                )
                for r in rows
            ]

    def count(self) -> int:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            return conn.execute("SELECT COUNT(*) FROM canonical_observations;").fetchone()[0]

    def count_rejections(self) -> int:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            return conn.execute("SELECT COUNT(*) FROM canonical_observation_rejections;").fetchone()[0]

    def _row_to_entity(self, r) -> ObservationEntity:
        norm = r["normalized_value_json"]
        if isinstance(norm, str):
            norm = json.loads(norm)
        meta = r["metadata_json"]
        if isinstance(meta, str):
            meta = json.loads(meta)
        return ObservationEntity(
            id=r["id"],
            subject_type=r["subject_type"],
            subject_id=r["subject_id"],
            predicate=r["predicate"],
            raw_value=r["raw_value"],
            normalized_value_json=norm or {},
            value_type=r["value_type"],
            source_id=r["source_id"],
            object_ref_id=r["object_ref_id"],
            observed_at=r["observed_at"],
            extractor_name=r["extractor_name"],
            extractor_version=r["extractor_version"],
            model_run_id=r["model_run_id"],
            confidence=float(r["confidence"]),
            created_at=r["created_at"],
            metadata_json=meta or {},
        )
