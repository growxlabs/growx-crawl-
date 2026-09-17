"""
GrowX Signal Candidate Repository.
Persistence layer for signal candidates.
"""

import json
import logging
import sqlite3
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from growx_crawl.intelligence.signals.models import SignalCandidateEntity
from growx_crawl.storage.db import get_db
from growx_crawl.storage.sqlite.canonical import init_sqlite_canonical_tables

logger = logging.getLogger("growx_crawl.intelligence.signals.repository")


class BaseSignalRepository(ABC):
    @abstractmethod
    def create_candidate(self, candidate: SignalCandidateEntity) -> SignalCandidateEntity: ...

    @abstractmethod
    def update_candidate(self, candidate: SignalCandidateEntity) -> SignalCandidateEntity: ...

    @abstractmethod
    def list_candidates(
        self,
        entity_id: str,
        status: Optional[str] = None,
        signal_type: Optional[str] = None,
    ) -> List[SignalCandidateEntity]: ...

    @abstractmethod
    def expire_candidates(self, before_date: str) -> int: ...


class SqliteSignalRepository(BaseSignalRepository):
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def _ensure_schema(self, conn: sqlite3.Connection):
        init_sqlite_canonical_tables(conn)

    def create_candidate(self, candidate: SignalCandidateEntity) -> SignalCandidateEntity:
        sql = """
            INSERT INTO signal_candidates (
                id, entity_type, entity_id, signal_type, trigger_event_ids,
                detected_at, occurred_at, expires_at, confidence, significance,
                status, policy_version, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO NOTHING;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(sql, (
                candidate.id, candidate.entity_type, candidate.entity_id,
                candidate.signal_type, json.dumps(candidate.trigger_event_ids),
                candidate.detected_at, candidate.occurred_at, candidate.expires_at,
                candidate.confidence, candidate.significance, candidate.status,
                candidate.policy_version, json.dumps(candidate.metadata_json),
            ))
        return candidate

    def update_candidate(self, candidate: SignalCandidateEntity) -> SignalCandidateEntity:
        sql = """
            UPDATE signal_candidates SET
                status = ?, confidence = ?, significance = ?,
                expires_at = ?, metadata_json = ?
            WHERE id = ?;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(sql, (
                candidate.status, candidate.confidence, candidate.significance,
                candidate.expires_at, json.dumps(candidate.metadata_json),
                candidate.id,
            ))
        return candidate

    def list_candidates(
        self,
        entity_id: str,
        status: Optional[str] = None,
        signal_type: Optional[str] = None,
    ) -> List[SignalCandidateEntity]:
        conditions = ["entity_id = ?"]
        params: list = [entity_id]

        if status:
            conditions.append("status = ?")
            params.append(status)
        if signal_type:
            conditions.append("signal_type = ?")
            params.append(signal_type)

        where = " AND ".join(conditions)
        sql = f"SELECT * FROM signal_candidates WHERE {where} ORDER BY detected_at DESC"

        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(sql, params).fetchall()
            return [self._row_to_candidate(r) for r in rows]

    def expire_candidates(self, before_date: str) -> int:
        sql = """
            UPDATE signal_candidates SET status = 'expired'
            WHERE status IN ('candidate', 'supported')
              AND expires_at IS NOT NULL AND expires_at < ?;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            cursor = conn.execute(sql, (before_date,))
            return cursor.rowcount

    def _row_to_candidate(self, r) -> SignalCandidateEntity:
        events = r["trigger_event_ids"]
        if isinstance(events, str):
            events = json.loads(events)
        meta = r["metadata_json"]
        if isinstance(meta, str):
            meta = json.loads(meta)
        return SignalCandidateEntity(
            id=r["id"],
            entity_type=r["entity_type"],
            entity_id=r["entity_id"],
            signal_type=r["signal_type"],
            trigger_event_ids=events or [],
            detected_at=r["detected_at"],
            occurred_at=r["occurred_at"],
            expires_at=r["expires_at"],
            confidence=float(r["confidence"]),
            significance=r["significance"],
            status=r["status"],
            policy_version=r["policy_version"],
            metadata_json=meta or {},
        )
