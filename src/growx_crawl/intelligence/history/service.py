"""
GrowX Historical Intelligence Service.
Primary service boundary for change detection, timelines, state reconstruction,
trends, and historical backfill.
"""

import logging
from typing import Any, Dict, List, Optional

from growx_crawl.intelligence.history.change_detector import ChangeDetector
from growx_crawl.intelligence.history.models import (
    BackfillRunEntity,
    ChangeEventType,
    CompanyTemporalSummary,
    CompanyTrendSummary,
    TimelineEventEntity,
    TrendEntity,
)
from growx_crawl.intelligence.history.policies import PolicyRegistry
from growx_crawl.intelligence.history.repository import (
    BaseHistoricalRepository,
    SqliteHistoricalRepository,
)
from growx_crawl.intelligence.history.significance import SignificanceEngine
from growx_crawl.intelligence.history.timelines import TimelineBuilder
from growx_crawl.intelligence.history.trends import TrendEngine
from growx_crawl.shared.ids import generate_id
from growx_crawl.shared.time import utc_iso_now

logger = logging.getLogger("growx_crawl.intelligence.history.service")


class HistoricalIntelligenceService:
    """
    Service boundary for retrieving fact history, detecting changes,
    building timelines, computing trends, and historical state reconstruction.
    """

    def __init__(
        self,
        repository: Optional[BaseHistoricalRepository] = None,
        change_detector: Optional[ChangeDetector] = None,
        significance_engine: Optional[SignificanceEngine] = None,
        policy_registry: Optional[PolicyRegistry] = None,
        timeline_builder: Optional[TimelineBuilder] = None,
        trend_engine: Optional[TrendEngine] = None,
    ):
        self.repository = repository or SqliteHistoricalRepository()
        self.change_detector = change_detector or ChangeDetector()
        self.significance_engine = significance_engine or SignificanceEngine()
        self.policy_registry = policy_registry or PolicyRegistry()
        self.timeline_builder = timeline_builder or TimelineBuilder()
        self.trend_engine = trend_engine or TrendEngine()

    def detect_changes(
        self,
        entity_type: str,
        entity_id: str,
        fact_changes: List[Dict[str, Any]],
    ) -> List[TimelineEventEntity]:
        """
        Process a batch of fact changes and create timeline events.
        Each fact_change dict should contain:
            fact_id, predicate, old_value_json, new_value_json, occurred_at,
            confidence, verification_state, old_extractor_version, new_extractor_version,
            source_id, observation_id, evidence_ids, cardinality
        """
        events: List[TimelineEventEntity] = []

        for change in fact_changes:
            cardinality = change.get("cardinality", "one")

            if cardinality == "many":
                # Multi-value change detection
                old_values = change.get("old_values", [])
                new_values = change.get("new_values", [])
                mv_events = self.change_detector.detect_multivalue_changes(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    fact_id=change.get("fact_id", ""),
                    predicate=change.get("predicate", ""),
                    old_values=old_values,
                    new_values=new_values,
                    occurred_at=change.get("occurred_at", utc_iso_now()),
                    confidence=change.get("confidence", 1.0),
                    verification_state=change.get("verification_state", "unverified"),
                )
                for ev in mv_events:
                    ev.significance = self.significance_engine.evaluate(
                        event_type=ev.event_type,
                        predicate=ev.predicate,
                    )
                    events.append(ev)
            else:
                # Single-value change detection
                event = self.change_detector.detect_fact_change(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    fact_id=change.get("fact_id", ""),
                    predicate=change.get("predicate", ""),
                    old_value_json=change.get("old_value_json", {}),
                    new_value_json=change.get("new_value_json", {}),
                    occurred_at=change.get("occurred_at", utc_iso_now()),
                    confidence=change.get("confidence", 1.0),
                    verification_state=change.get("verification_state", "unverified"),
                    old_extractor_version=change.get("old_extractor_version"),
                    new_extractor_version=change.get("new_extractor_version"),
                    source_id=change.get("source_id"),
                    observation_id=change.get("observation_id"),
                    evidence_ids=change.get("evidence_ids"),
                )
                if event:
                    # Evaluate significance
                    magnitude = event.metadata_json.get("percentage_delta")
                    event.significance = self.significance_engine.evaluate(
                        event_type=event.event_type,
                        predicate=event.predicate,
                        magnitude=magnitude,
                        verification_confidence=event.confidence,
                    )
                    events.append(event)

        # Persist events (idempotent via fingerprint)
        persisted: List[TimelineEventEntity] = []
        for ev in events:
            if not self.repository.event_exists_by_fingerprint(ev.fingerprint):
                self.repository.create_event(ev)
                persisted.append(ev)
            else:
                logger.debug("Skipping duplicate event with fingerprint %s", ev.fingerprint)

        return persisted

    def process_employment_change(
        self,
        person_id: str,
        company_id: str,
        event_type: str,
        title: Optional[str] = None,
        occurred_at: Optional[str] = None,
    ) -> Optional[TimelineEventEntity]:
        """Create timeline event for employment changes (join/leave/title change)."""
        now = occurred_at or utc_iso_now()

        fingerprint = ChangeDetector.compute_fingerprint(
            "person", person_id, "employment",
            {"company_id": company_id, "type": event_type},
            {"title": title or ""},
            now,
        )

        if self.repository.event_exists_by_fingerprint(fingerprint):
            return None

        event = TimelineEventEntity(
            id=generate_id("evt_"),
            entity_type="person",
            entity_id=person_id,
            event_type=event_type,
            occurred_at=now,
            predicate="employment",
            new_value_json={"company_id": company_id, "title": title},
            fingerprint=fingerprint,
            significance=self.significance_engine.evaluate(event_type),
        )
        self.repository.create_event(event)
        return event

    def get_timeline(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 100,
        offset: int = 0,
        event_types: Optional[List[str]] = None,
        since: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get the timeline for an entity as annotated list."""
        events = self.repository.list_events(
            entity_type=entity_type,
            entity_id=entity_id,
            event_types=event_types,
            since=since,
            limit=limit,
            offset=offset,
        )
        return self.timeline_builder.build_entity_timeline(events)

    def get_state_at(
        self,
        entity_type: str,
        entity_id: str,
        at_time: str,
        facts: List[Dict[str, Any]],
        values: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Reconstruct historical state of an entity at a given time."""
        return self.timeline_builder.reconstruct_state_at(facts, values, at_time)

    def get_trends(
        self,
        entity_type: str,
        entity_id: str,
        trend_types: Optional[List[str]] = None,
    ) -> List[TrendEntity]:
        """Get computed trends for an entity."""
        return self.repository.list_trends(
            entity_type=entity_type,
            entity_id=entity_id,
            trend_types=trend_types,
        )

    def compute_and_store_trends(
        self,
        entity_type: str,
        entity_id: str,
        fact_values_by_type: Dict[str, List[Dict[str, Any]]],
    ) -> List[TrendEntity]:
        """Compute trends from fact values and persist them."""
        trends = self.trend_engine.calculate_trends(
            entity_type=entity_type,
            entity_id=entity_id,
            fact_values_by_type=fact_values_by_type,
        )
        for trend in trends:
            self.repository.save_trend(trend)
        return trends

    def update_temporal_summary(
        self,
        company_id: str,
        latest_signal_type: Optional[str] = None,
        latest_signal_at: Optional[str] = None,
    ) -> None:
        """Update the denormalized temporal summary for a company."""
        from datetime import timedelta
        from growx_crawl.shared.time import utc_now, format_iso

        now = utc_now()
        count_30d = self.repository.count_events(
            "company", company_id,
            since=format_iso(now - timedelta(days=30)),
        )
        count_90d = self.repository.count_events(
            "company", company_id,
            since=format_iso(now - timedelta(days=90)),
        )

        # Get the most recent event's occurred_at
        recent = self.repository.list_events("company", company_id, limit=1)
        # list_events returns ASC, so recent[-1] is latest if populated
        last_change = None
        if recent:
            last_change = recent[-1].occurred_at

        summary = CompanyTemporalSummary(
            company_id=company_id,
            last_change_at=last_change,
            change_count_30d=count_30d,
            change_count_90d=count_90d,
            latest_signal_type=latest_signal_type,
            latest_signal_at=latest_signal_at,
        )
        self.repository.save_temporal_summary(summary)

    def backfill(
        self,
        entity_type: str,
        fact_history: List[Dict[str, Any]],
        batch_size: int = 100,
    ) -> BackfillRunEntity:
        """
        Process historical fact records into timeline events.
        fact_history items should be ordered oldest-to-newest with:
            entity_id, fact_id, predicate, old_value_json, new_value_json,
            occurred_at, confidence
        """
        run = BackfillRunEntity(
            id=generate_id("bkf_"),
            entity_type=entity_type,
        )
        self.repository.save_backfill_run(run)

        processed = 0
        errors = 0

        for i in range(0, len(fact_history), batch_size):
            batch = fact_history[i:i + batch_size]
            for record in batch:
                try:
                    entity_id = record.get("entity_id", "")
                    events = self.detect_changes(
                        entity_type=entity_type,
                        entity_id=entity_id,
                        fact_changes=[record],
                    )
                    processed += 1
                except Exception as e:
                    logger.warning("Backfill error for record %s: %s", record.get("fact_id"), e)
                    errors += 1

            run.processed_count = processed
            run.error_count = errors
            run.last_cursor = str(i + len(batch))
            self.repository.update_backfill_run(run)

        run.status = "completed"
        run.completed_at = utc_iso_now()
        run.processed_count = processed
        run.error_count = errors
        self.repository.update_backfill_run(run)

        return run

    # Backward compatibility
    def diff_fact_values(self, old_value, new_value, predicate):
        """Legacy method preserved for backward compatibility."""
        from growx_crawl.intelligence.history.change_detector import detect_value_change
        return detect_value_change(old_value, new_value, predicate)


# Module-level singleton (backward compatible)
history_service = HistoricalIntelligenceService()
