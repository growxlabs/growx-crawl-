from abc import ABC, abstractmethod
from datetime import datetime, timezone
import json
import logging
import sqlite3
from typing import Any, Dict, List, Optional

from growx_crawl.intelligence.facts.models import (
    FactConflictEntity,
    FactEntity,
    FactEventEntity,
    FactEvidenceEntity,
    FactValueEntity,
)
from growx_crawl.storage.db import get_db
from growx_crawl.storage.sqlite.canonical import init_sqlite_canonical_tables

logger = logging.getLogger("growx_crawl.intelligence.facts.repository")


class BaseFactRepository(ABC):
    # Facts
    @abstractmethod
    def get(self, fact_id: str) -> Optional[FactEntity]: ...

    @abstractmethod
    def find_current(
        self,
        subject_type: str,
        subject_id: str,
        predicate: str,
        scope_type: str = "global",
        scope_id: str = "global",
    ) -> Optional[FactEntity]: ...

    @abstractmethod
    def list_current(
        self,
        subject_type: str,
        subject_id: str,
        scope_type: str = "global",
        scope_id: str = "global",
    ) -> List[FactEntity]: ...

    @abstractmethod
    def create(self, fact: FactEntity) -> FactEntity: ...

    @abstractmethod
    def update(self, fact: FactEntity) -> FactEntity: ...

    @abstractmethod
    def count(self) -> int: ...

    # Fact Values (History)
    @abstractmethod
    def add_value(self, val: FactValueEntity) -> FactValueEntity: ...

    @abstractmethod
    def update_value(self, val: FactValueEntity) -> FactValueEntity: ...

    @abstractmethod
    def list_history(self, fact_id: str) -> List[FactValueEntity]: ...

    # Fact Evidence
    @abstractmethod
    def link_evidence(self, link: FactEvidenceEntity) -> FactEvidenceEntity: ...

    @abstractmethod
    def list_evidence(self, fact_id: str) -> List[FactEvidenceEntity]: ...

    # Conflicts
    @abstractmethod
    def create_conflict(self, conflict: FactConflictEntity) -> FactConflictEntity: ...

    @abstractmethod
    def get_conflict(self, conflict_id: str) -> Optional[FactConflictEntity]: ...

    @abstractmethod
    def list_conflicts(
        self,
        subject_type: Optional[str] = None,
        subject_id: Optional[str] = None,
        status: str = "open",
    ) -> List[FactConflictEntity]: ...

    @abstractmethod
    def resolve_conflict(
        self,
        conflict_id: str,
        resolution_method: str,
        selected_fact_value_id: Optional[str] = None,
    ) -> Optional[FactConflictEntity]: ...

    # Fact Events
    @abstractmethod
    def record_event(self, event: FactEventEntity) -> FactEventEntity: ...

    @abstractmethod
    def list_events(self, fact_id: str, limit: int = 50) -> List[FactEventEntity]: ...


class SqliteFactRepository(BaseFactRepository):
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def _ensure_schema(self, conn: sqlite3.Connection):
        init_sqlite_canonical_tables(conn)

    # Facts
    def get(self, fact_id: str) -> Optional[FactEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute("SELECT * FROM canonical_facts WHERE id = ?", (fact_id,)).fetchone()
            return self._row_to_fact(row) if row else None

    def find_current(
        self,
        subject_type: str,
        subject_id: str,
        predicate: str,
        scope_type: str = "global",
        scope_id: str = "global",
    ) -> Optional[FactEntity]:
        sql = """
            SELECT * FROM canonical_facts
            WHERE subject_type = ? AND subject_id = ? AND predicate = ?
              AND scope_type = ? AND scope_id = ?
              AND status != 'deleted'
            ORDER BY updated_at DESC LIMIT 1;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute(sql, (subject_type, subject_id, predicate, scope_type, scope_id)).fetchone()
            return self._row_to_fact(row) if row else None

    def list_current(
        self,
        subject_type: str,
        subject_id: str,
        scope_type: str = "global",
        scope_id: str = "global",
    ) -> List[FactEntity]:
        sql = """
            SELECT * FROM canonical_facts
            WHERE subject_type = ? AND subject_id = ?
              AND scope_type = ? AND scope_id = ?
              AND status != 'deleted'
            ORDER BY predicate ASC;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(sql, (subject_type, subject_id, scope_type, scope_id)).fetchall()
            return [self._row_to_fact(r) for r in rows]

    def create(self, fact: FactEntity) -> FactEntity:
        sql = """
            INSERT INTO canonical_facts (
                id, subject_type, subject_id, predicate, value_type, current_value_json,
                status, confidence, verification_state, first_seen_at, last_seen_at,
                last_verified_at, valid_from, valid_to, scope_type, scope_id,
                created_at, updated_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO NOTHING;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    fact.id,
                    fact.subject_type,
                    fact.subject_id,
                    fact.predicate,
                    fact.value_type,
                    json.dumps(fact.current_value_json),
                    fact.status,
                    fact.confidence,
                    fact.verification_state,
                    fact.first_seen_at,
                    fact.last_seen_at,
                    fact.last_verified_at,
                    fact.valid_from,
                    fact.valid_to,
                    fact.scope_type,
                    fact.scope_id,
                    fact.created_at,
                    fact.updated_at,
                    json.dumps(fact.metadata_json),
                ),
            )
        return fact

    def update(self, fact: FactEntity) -> FactEntity:
        sql = """
            UPDATE canonical_facts SET
                current_value_json = ?,
                status = ?,
                confidence = ?,
                verification_state = ?,
                last_seen_at = ?,
                last_verified_at = coalesce(?, last_verified_at),
                valid_from = ?,
                valid_to = ?,
                updated_at = ?,
                metadata_json = ?
            WHERE id = ?;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    json.dumps(fact.current_value_json),
                    fact.status,
                    fact.confidence,
                    fact.verification_state,
                    fact.last_seen_at,
                    fact.last_verified_at,
                    fact.valid_from,
                    fact.valid_to,
                    fact.updated_at,
                    json.dumps(fact.metadata_json),
                    fact.id,
                ),
            )
        return fact

    def count(self) -> int:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            return conn.execute("SELECT COUNT(*) FROM canonical_facts;").fetchone()[0]

    # Fact Values (History)
    def add_value(self, val: FactValueEntity) -> FactValueEntity:
        sql = """
            INSERT INTO canonical_fact_values (
                id, fact_id, value_json, value_type, confidence, status,
                valid_from, valid_to, first_seen_at, last_seen_at, last_verified_at,
                created_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO NOTHING;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    val.id,
                    val.fact_id,
                    json.dumps(val.value_json),
                    val.value_type,
                    val.confidence,
                    val.status,
                    val.valid_from,
                    val.valid_to,
                    val.first_seen_at,
                    val.last_seen_at,
                    val.last_verified_at,
                    val.created_at,
                    json.dumps(val.metadata_json),
                ),
            )
        return val

    def update_value(self, val: FactValueEntity) -> FactValueEntity:
        sql = """
            UPDATE canonical_fact_values SET
                status = ?,
                valid_to = ?,
                last_seen_at = ?,
                last_verified_at = coalesce(?, last_verified_at),
                metadata_json = ?
            WHERE id = ?;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    val.status,
                    val.valid_to,
                    val.last_seen_at,
                    val.last_verified_at,
                    json.dumps(val.metadata_json),
                    val.id,
                ),
            )
        return val

    def list_history(self, fact_id: str) -> List[FactValueEntity]:
        sql = "SELECT * FROM canonical_fact_values WHERE fact_id = ? ORDER BY valid_from DESC;"
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(sql, (fact_id,)).fetchall()
            return [self._row_to_fact_value(r) for r in rows]

    # Fact Evidence
    def link_evidence(self, link: FactEvidenceEntity) -> FactEvidenceEntity:
        sql = """
            INSERT INTO canonical_fact_evidence (fact_id, observation_id, support_type, weight, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (fact_id, observation_id) DO UPDATE SET
                support_type = excluded.support_type,
                weight = excluded.weight;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(sql, (link.fact_id, link.observation_id, link.support_type, link.weight, link.created_at))
        return link

    def list_evidence(self, fact_id: str) -> List[FactEvidenceEntity]:
        sql = "SELECT * FROM canonical_fact_evidence WHERE fact_id = ? ORDER BY created_at DESC;"
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(sql, (fact_id,)).fetchall()
            return [
                FactEvidenceEntity(
                    fact_id=r["fact_id"],
                    observation_id=r["observation_id"],
                    support_type=r["support_type"],
                    weight=float(r["weight"]),
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    # Conflicts
    def create_conflict(self, conflict: FactConflictEntity) -> FactConflictEntity:
        sql = """
            INSERT INTO canonical_fact_conflicts (
                id, subject_type, subject_id, predicate, status, created_at,
                resolved_at, resolution_method, selected_fact_value_id, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO NOTHING;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    conflict.id,
                    conflict.subject_type,
                    conflict.subject_id,
                    conflict.predicate,
                    conflict.status,
                    conflict.created_at,
                    conflict.resolved_at,
                    conflict.resolution_method,
                    conflict.selected_fact_value_id,
                    json.dumps(conflict.metadata_json),
                ),
            )
        return conflict

    def get_conflict(self, conflict_id: str) -> Optional[FactConflictEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute("SELECT * FROM canonical_fact_conflicts WHERE id = ?", (conflict_id,)).fetchone()
            return self._row_to_conflict(row) if row else None

    def list_conflicts(
        self,
        subject_type: Optional[str] = None,
        subject_id: Optional[str] = None,
        status: str = "open",
    ) -> List[FactConflictEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            if subject_type and subject_id:
                sql = "SELECT * FROM canonical_fact_conflicts WHERE subject_type = ? AND subject_id = ? AND status = ? ORDER BY created_at DESC;"
                rows = conn.execute(sql, (subject_type, subject_id, status)).fetchall()
            else:
                sql = "SELECT * FROM canonical_fact_conflicts WHERE status = ? ORDER BY created_at DESC;"
                rows = conn.execute(sql, (status,)).fetchall()
            return [self._row_to_conflict(r) for r in rows]

    def resolve_conflict(
        self,
        conflict_id: str,
        resolution_method: str,
        selected_fact_value_id: Optional[str] = None,
    ) -> Optional[FactConflictEntity]:
        now_iso = datetime.now(timezone.utc).isoformat()
        sql = """
            UPDATE canonical_fact_conflicts SET
                status = 'auto_resolved' if ? = 'auto' else 'human_resolved',
                resolved_at = ?,
                resolution_method = ?,
                selected_fact_value_id = ?
            WHERE id = ?;
        """
        status_val = "auto_resolved" if "auto" in resolution_method else "human_resolved"
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                """UPDATE canonical_fact_conflicts SET status = ?, resolved_at = ?, resolution_method = ?, selected_fact_value_id = ? WHERE id = ?""",
                (status_val, now_iso, resolution_method, selected_fact_value_id, conflict_id),
            )
        return self.get_conflict(conflict_id)

    # Fact Events
    def record_event(self, event: FactEventEntity) -> FactEventEntity:
        sql = """
            INSERT INTO canonical_fact_events (id, fact_id, event_type, payload_json, actor_type, actor_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO NOTHING;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    event.id,
                    event.fact_id,
                    event.event_type,
                    json.dumps(event.payload_json),
                    event.actor_type,
                    event.actor_id,
                    event.created_at,
                ),
            )
        return event

    def list_events(self, fact_id: str, limit: int = 50) -> List[FactEventEntity]:
        sql = "SELECT * FROM canonical_fact_events WHERE fact_id = ? ORDER BY created_at DESC LIMIT ?;"
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(sql, (fact_id, limit)).fetchall()
            return [
                FactEventEntity(
                    id=r["id"],
                    fact_id=r["fact_id"],
                    event_type=r["event_type"],
                    payload_json=json.loads(r["payload_json"]) if isinstance(r["payload_json"], str) else (r["payload_json"] or {}),
                    actor_type=r["actor_type"],
                    actor_id=r["actor_id"],
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    # Row Helpers
    def _row_to_fact(self, r) -> FactEntity:
        curr = r["current_value_json"]
        if isinstance(curr, str):
            curr = json.loads(curr)
        meta = r["metadata_json"]
        if isinstance(meta, str):
            meta = json.loads(meta)
        return FactEntity(
            id=r["id"],
            subject_type=r["subject_type"],
            subject_id=r["subject_id"],
            predicate=r["predicate"],
            value_type=r["value_type"],
            current_value_json=curr or {},
            status=r["status"],
            confidence=float(r["confidence"]),
            verification_state=r["verification_state"],
            first_seen_at=r["first_seen_at"],
            last_seen_at=r["last_seen_at"],
            last_verified_at=r["last_verified_at"],
            valid_from=r["valid_from"],
            valid_to=r["valid_to"],
            scope_type=r["scope_type"],
            scope_id=r["scope_id"],
            created_at=r["created_at"],
            updated_at=r["updated_at"],
            metadata_json=meta or {},
        )

    def _row_to_fact_value(self, r) -> FactValueEntity:
        val = r["value_json"]
        if isinstance(val, str):
            val = json.loads(val)
        meta = r["metadata_json"]
        if isinstance(meta, str):
            meta = json.loads(meta)
        return FactValueEntity(
            id=r["id"],
            fact_id=r["fact_id"],
            value_json=val or {},
            value_type=r["value_type"],
            confidence=float(r["confidence"]),
            status=r["status"],
            valid_from=r["valid_from"],
            valid_to=r["valid_to"],
            first_seen_at=r["first_seen_at"],
            last_seen_at=r["last_seen_at"],
            last_verified_at=r["last_verified_at"],
            created_at=r["created_at"],
            metadata_json=meta or {},
        )

    def _row_to_conflict(self, r) -> FactConflictEntity:
        meta = r["metadata_json"]
        if isinstance(meta, str):
            meta = json.loads(meta)
        return FactConflictEntity(
            id=r["id"],
            subject_type=r["subject_type"],
            subject_id=r["subject_id"],
            predicate=r["predicate"],
            status=r["status"],
            created_at=r["created_at"],
            resolved_at=r["resolved_at"],
            resolution_method=r["resolution_method"],
            selected_fact_value_id=r["selected_fact_value_id"],
            metadata_json=meta or {},
        )
