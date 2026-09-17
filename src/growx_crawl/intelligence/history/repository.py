"""
GrowX Historical Intelligence Repository.
Persistence layer for timeline events, trends, temporal summaries, and backfill runs.
"""

import json
import logging
import sqlite3
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from growx_crawl.intelligence.history.models import (
    BackfillRunEntity,
    CompanyTemporalSummary,
    CompanyTrendSummary,
    TimelineEventEntity,
    TrendEntity,
)
from growx_crawl.storage.db import get_db
from growx_crawl.storage.sqlite.canonical import init_sqlite_canonical_tables

logger = logging.getLogger("growx_crawl.intelligence.history.repository")


class BaseHistoricalRepository(ABC):
    @abstractmethod
    def create_event(self, event: TimelineEventEntity) -> TimelineEventEntity: ...

    @abstractmethod
    def get_event(self, event_id: str) -> Optional[TimelineEventEntity]: ...

    @abstractmethod
    def list_events(
        self,
        entity_type: str,
        entity_id: str,
        event_types: Optional[List[str]] = None,
        since: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[TimelineEventEntity]: ...

    @abstractmethod
    def event_exists_by_fingerprint(self, fingerprint: str) -> bool: ...

    @abstractmethod
    def save_trend(self, trend: TrendEntity) -> TrendEntity: ...

    @abstractmethod
    def list_trends(
        self,
        entity_type: str,
        entity_id: str,
        trend_types: Optional[List[str]] = None,
    ) -> List[TrendEntity]: ...

    @abstractmethod
    def save_temporal_summary(self, summary: CompanyTemporalSummary) -> None: ...

    @abstractmethod
    def get_temporal_summary(self, company_id: str) -> Optional[CompanyTemporalSummary]: ...

    @abstractmethod
    def save_trend_summary(self, summary: CompanyTrendSummary) -> None: ...

    @abstractmethod
    def save_backfill_run(self, run: BackfillRunEntity) -> BackfillRunEntity: ...

    @abstractmethod
    def update_backfill_run(self, run: BackfillRunEntity) -> BackfillRunEntity: ...


class SqliteHistoricalRepository(BaseHistoricalRepository):
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def _ensure_schema(self, conn: sqlite3.Connection):
        init_sqlite_canonical_tables(conn)

    def create_event(self, event: TimelineEventEntity) -> TimelineEventEntity:
        sql = """
            INSERT INTO entity_timeline_events (
                id, entity_type, entity_id, event_type, occurred_at, detected_at,
                source_id, fact_id, observation_id, evidence_ids, predicate,
                previous_value_json, new_value_json, confidence, verification_state,
                significance, fingerprint, extractor_version, policy_version, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (fingerprint) DO NOTHING;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(sql, (
                event.id, event.entity_type, event.entity_id, event.event_type,
                event.occurred_at, event.detected_at, event.source_id, event.fact_id,
                event.observation_id, json.dumps(event.evidence_ids), event.predicate,
                json.dumps(event.previous_value_json), json.dumps(event.new_value_json),
                event.confidence, event.verification_state, event.significance,
                event.fingerprint, event.extractor_version, event.policy_version,
                json.dumps(event.metadata_json),
            ))
        return event

    def get_event(self, event_id: str) -> Optional[TimelineEventEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute(
                "SELECT * FROM entity_timeline_events WHERE id = ?", (event_id,)
            ).fetchone()
            return self._row_to_event(row) if row else None

    def list_events(
        self,
        entity_type: str,
        entity_id: str,
        event_types: Optional[List[str]] = None,
        since: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[TimelineEventEntity]:
        conditions = ["entity_type = ?", "entity_id = ?"]
        params: list = [entity_type, entity_id]

        if event_types:
            placeholders = ",".join("?" for _ in event_types)
            conditions.append(f"event_type IN ({placeholders})")
            params.extend(event_types)

        if since:
            conditions.append("occurred_at >= ?")
            params.append(since)

        where = " AND ".join(conditions)
        sql = f"SELECT * FROM entity_timeline_events WHERE {where} ORDER BY occurred_at ASC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(sql, params).fetchall()
            return [self._row_to_event(r) for r in rows]

    def event_exists_by_fingerprint(self, fingerprint: str) -> bool:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute(
                "SELECT 1 FROM entity_timeline_events WHERE fingerprint = ?", (fingerprint,)
            ).fetchone()
            return row is not None

    def save_trend(self, trend: TrendEntity) -> TrendEntity:
        sql = """
            INSERT INTO entity_trends (
                id, entity_type, entity_id, trend_type, window_start, window_end,
                value_json, confidence, calculation_version, source_fact_ids,
                derived, created_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET
                value_json = excluded.value_json,
                confidence = excluded.confidence,
                calculation_version = excluded.calculation_version,
                source_fact_ids = excluded.source_fact_ids;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(sql, (
                trend.id, trend.entity_type, trend.entity_id, trend.trend_type,
                trend.window_start, trend.window_end, json.dumps(trend.value_json),
                trend.confidence, trend.calculation_version,
                json.dumps(trend.source_fact_ids),
                1 if trend.derived else 0, trend.created_at,
                json.dumps(trend.metadata_json),
            ))
        return trend

    def list_trends(
        self,
        entity_type: str,
        entity_id: str,
        trend_types: Optional[List[str]] = None,
    ) -> List[TrendEntity]:
        conditions = ["entity_type = ?", "entity_id = ?"]
        params: list = [entity_type, entity_id]

        if trend_types:
            placeholders = ",".join("?" for _ in trend_types)
            conditions.append(f"trend_type IN ({placeholders})")
            params.extend(trend_types)

        where = " AND ".join(conditions)
        sql = f"SELECT * FROM entity_trends WHERE {where} ORDER BY created_at DESC"

        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(sql, params).fetchall()
            return [self._row_to_trend(r) for r in rows]

    def save_temporal_summary(self, summary: CompanyTemporalSummary) -> None:
        sql = """
            INSERT INTO company_temporal_summaries (
                company_id, last_change_at, change_count_30d, change_count_90d,
                latest_signal_type, latest_signal_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (company_id) DO UPDATE SET
                last_change_at = excluded.last_change_at,
                change_count_30d = excluded.change_count_30d,
                change_count_90d = excluded.change_count_90d,
                latest_signal_type = excluded.latest_signal_type,
                latest_signal_at = excluded.latest_signal_at,
                updated_at = excluded.updated_at;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(sql, (
                summary.company_id, summary.last_change_at,
                summary.change_count_30d, summary.change_count_90d,
                summary.latest_signal_type, summary.latest_signal_at,
                summary.updated_at,
            ))

    def get_temporal_summary(self, company_id: str) -> Optional[CompanyTemporalSummary]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute(
                "SELECT * FROM company_temporal_summaries WHERE company_id = ?", (company_id,)
            ).fetchone()
            if not row:
                return None
            return CompanyTemporalSummary(
                company_id=row["company_id"],
                last_change_at=row["last_change_at"],
                change_count_30d=row["change_count_30d"],
                change_count_90d=row["change_count_90d"],
                latest_signal_type=row["latest_signal_type"],
                latest_signal_at=row["latest_signal_at"],
                updated_at=row["updated_at"],
            )

    def save_trend_summary(self, summary: CompanyTrendSummary) -> None:
        sql = """
            INSERT INTO company_trend_summaries (
                company_id, employee_growth_90d, employee_growth_365d,
                leadership_changes_180d, location_growth_365d,
                technology_changes_180d, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (company_id) DO UPDATE SET
                employee_growth_90d = excluded.employee_growth_90d,
                employee_growth_365d = excluded.employee_growth_365d,
                leadership_changes_180d = excluded.leadership_changes_180d,
                location_growth_365d = excluded.location_growth_365d,
                technology_changes_180d = excluded.technology_changes_180d,
                updated_at = excluded.updated_at;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(sql, (
                summary.company_id, summary.employee_growth_90d,
                summary.employee_growth_365d, summary.leadership_changes_180d,
                summary.location_growth_365d, summary.technology_changes_180d,
                summary.updated_at,
            ))

    def save_backfill_run(self, run: BackfillRunEntity) -> BackfillRunEntity:
        sql = """
            INSERT INTO history_backfill_runs (
                id, entity_type, start_time, end_time, status,
                processed_count, error_count, last_cursor, created_at, completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO NOTHING;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(sql, (
                run.id, run.entity_type, run.start_time, run.end_time,
                run.status, run.processed_count, run.error_count,
                run.last_cursor, run.created_at, run.completed_at,
            ))
        return run

    def update_backfill_run(self, run: BackfillRunEntity) -> BackfillRunEntity:
        sql = """
            UPDATE history_backfill_runs SET
                status = ?, processed_count = ?, error_count = ?,
                last_cursor = ?, completed_at = ?
            WHERE id = ?;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(sql, (
                run.status, run.processed_count, run.error_count,
                run.last_cursor, run.completed_at, run.id,
            ))
        return run

    def count_events(self, entity_type: str, entity_id: str, since: Optional[str] = None) -> int:
        conditions = ["entity_type = ?", "entity_id = ?"]
        params: list = [entity_type, entity_id]
        if since:
            conditions.append("occurred_at >= ?")
            params.append(since)
        where = " AND ".join(conditions)
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute(
                f"SELECT COUNT(*) FROM entity_timeline_events WHERE {where}", params
            ).fetchone()
            return row[0] if row else 0

    # Row helpers
    def _row_to_event(self, r) -> TimelineEventEntity:
        evidence = r["evidence_ids"]
        if isinstance(evidence, str):
            evidence = json.loads(evidence)
        prev = r["previous_value_json"]
        if isinstance(prev, str):
            prev = json.loads(prev)
        new_v = r["new_value_json"]
        if isinstance(new_v, str):
            new_v = json.loads(new_v)
        meta = r["metadata_json"]
        if isinstance(meta, str):
            meta = json.loads(meta)
        return TimelineEventEntity(
            id=r["id"],
            entity_type=r["entity_type"],
            entity_id=r["entity_id"],
            event_type=r["event_type"],
            occurred_at=r["occurred_at"],
            detected_at=r["detected_at"],
            source_id=r["source_id"],
            fact_id=r["fact_id"],
            observation_id=r["observation_id"],
            evidence_ids=evidence or [],
            predicate=r["predicate"],
            previous_value_json=prev or {},
            new_value_json=new_v or {},
            confidence=float(r["confidence"]),
            verification_state=r["verification_state"],
            significance=r["significance"],
            fingerprint=r["fingerprint"],
            extractor_version=r["extractor_version"],
            policy_version=r["policy_version"],
            metadata_json=meta or {},
        )

    def _row_to_trend(self, r) -> TrendEntity:
        val = r["value_json"]
        if isinstance(val, str):
            val = json.loads(val)
        facts = r["source_fact_ids"]
        if isinstance(facts, str):
            facts = json.loads(facts)
        meta = r["metadata_json"]
        if isinstance(meta, str):
            meta = json.loads(meta)
        return TrendEntity(
            id=r["id"],
            entity_type=r["entity_type"],
            entity_id=r["entity_id"],
            trend_type=r["trend_type"],
            window_start=r["window_start"],
            window_end=r["window_end"],
            value_json=val or {},
            confidence=float(r["confidence"]),
            calculation_version=r["calculation_version"],
            source_fact_ids=facts or [],
            derived=bool(r["derived"]),
            created_at=r["created_at"],
            metadata_json=meta or {},
        )
