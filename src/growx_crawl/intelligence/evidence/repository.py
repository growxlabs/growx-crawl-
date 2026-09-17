from abc import ABC, abstractmethod
import json
import logging
import sqlite3
from typing import Any, Dict, List, Optional

from growx_crawl.intelligence.evidence.models import EvidenceEntity
from growx_crawl.storage.db import get_db
from growx_crawl.storage.sqlite.canonical import init_sqlite_canonical_tables

logger = logging.getLogger("growx_crawl.intelligence.evidence.repository")


class BaseEvidenceRepository(ABC):
    @abstractmethod
    def get(self, evidence_id: str) -> Optional[EvidenceEntity]: ...

    @abstractmethod
    def create(self, evidence: EvidenceEntity) -> EvidenceEntity: ...

    @abstractmethod
    def list_by_observation(self, observation_id: str) -> List[EvidenceEntity]: ...

    @abstractmethod
    def count(self) -> int: ...


class SqliteEvidenceRepository(BaseEvidenceRepository):
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def _ensure_schema(self, conn: sqlite3.Connection):
        init_sqlite_canonical_tables(conn)

    def get(self, evidence_id: str) -> Optional[EvidenceEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute("SELECT * FROM canonical_evidence WHERE id = ?", (evidence_id,)).fetchone()
            return self._row_to_entity(row) if row else None

    def create(self, evidence: EvidenceEntity) -> EvidenceEntity:
        sql = """
            INSERT INTO canonical_evidence (
                id, observation_id, source_id, object_ref_id, evidence_type, source_url,
                selector, text_start, text_end, page_number, quoted_text, content_hash,
                captured_at, created_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO NOTHING;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    evidence.id,
                    evidence.observation_id,
                    evidence.source_id,
                    evidence.object_ref_id,
                    evidence.evidence_type,
                    evidence.source_url,
                    evidence.selector,
                    evidence.text_start,
                    evidence.text_end,
                    evidence.page_number,
                    evidence.quoted_text,
                    evidence.content_hash,
                    evidence.captured_at,
                    evidence.created_at,
                    json.dumps(evidence.metadata_json),
                ),
            )
        return evidence

    def list_by_observation(self, observation_id: str) -> List[EvidenceEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(
                "SELECT * FROM canonical_evidence WHERE observation_id = ? ORDER BY created_at DESC",
                (observation_id,),
            ).fetchall()
            return [self._row_to_entity(r) for r in rows]

    def count(self) -> int:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            return conn.execute("SELECT COUNT(*) FROM canonical_evidence;").fetchone()[0]

    def _row_to_entity(self, r) -> EvidenceEntity:
        meta = r["metadata_json"]
        if isinstance(meta, str):
            meta = json.loads(meta)
        return EvidenceEntity(
            id=r["id"],
            observation_id=r["observation_id"],
            source_id=r["source_id"],
            object_ref_id=r["object_ref_id"],
            evidence_type=r["evidence_type"],
            source_url=r["source_url"],
            selector=r["selector"],
            text_start=r["text_start"],
            text_end=r["text_end"],
            page_number=r["page_number"],
            quoted_text=r["quoted_text"],
            content_hash=r["content_hash"],
            captured_at=r["captured_at"],
            created_at=r["created_at"],
            metadata_json=meta or {},
        )
