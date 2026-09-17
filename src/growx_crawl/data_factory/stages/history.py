"""
GrowX Data Factory Stage 8: History & Change Tracking.
Detects attribute evolution, computes trends, and generates signal candidates
using the Historical Intelligence service.
"""

import logging
from typing import Any, Dict, List, Optional
from growx_crawl.data_factory.metrics import DataFactoryMetrics
from growx_crawl.shared.time import utc_iso_now

logger = logging.getLogger("growx_crawl.data_factory.stages.history")


class HistoryStage:
    """Tracks state mutations and preserves historical intelligence."""

    def execute(
        self,
        quality_items: List[Dict[str, Any]],
        metrics: DataFactoryMetrics,
    ) -> List[Dict[str, Any]]:
        history_output: List[Dict[str, Any]] = []

        # Lazy import to avoid circular dependency at module level
        try:
            from growx_crawl.intelligence.history.service import HistoricalIntelligenceService
            from growx_crawl.intelligence.signals.service import SignalService
            history_svc = HistoricalIntelligenceService()
            signal_svc = SignalService()
        except Exception as e:
            logger.warning("Could not initialize history services: %s", e)
            # Fall through to basic processing
            for item in quality_items:
                item["changes"] = []
                history_output.append(item)
            return history_output

        for item in quality_items:
            changes: List[Dict[str, Any]] = []
            entity_id = item.get("company_id") or item.get("entity_id", "")
            entity_type = item.get("entity_type", "company")

            # Build fact change records from item data
            fact_changes: List[Dict[str, Any]] = []

            obs = item.get("observation", {})
            prior_name = item.get("prior_company_name")

            # Check if company name changed
            if prior_name and prior_name != item.get("company_name"):
                fact_changes.append({
                    "fact_id": item.get("fact_id", ""),
                    "predicate": "company.legal_name",
                    "old_value_json": {"value": prior_name},
                    "new_value_json": {"value": item.get("company_name")},
                    "occurred_at": utc_iso_now(),
                    "confidence": item.get("confidence", 0.8),
                    "verification_state": item.get("verification_state", "unverified"),
                })

            # Detect changes via Historical Intelligence service
            if fact_changes and entity_id:
                try:
                    events = history_svc.detect_changes(
                        entity_type=entity_type,
                        entity_id=entity_id,
                        fact_changes=fact_changes,
                    )
                    for ev in events:
                        changes.append({
                            "change_type": ev.event_type,
                            "predicate": ev.predicate,
                            "old_value": ev.previous_value_json,
                            "new_value": ev.new_value_json,
                            "significance": ev.significance,
                            "detected_at": ev.detected_at,
                        })
                        metrics.facts_changed += 1

                    # Generate signal candidates from new events
                    if events:
                        signal_svc.detect_signal_candidates(
                            entity_id=entity_id,
                            timeline_events=events,
                            entity_type=entity_type,
                        )
                except Exception as e:
                    logger.warning("Change detection error for %s: %s", entity_id, e)

            # Check for new contact signals (backward compat)
            emails = obs.get("emails", [])
            if len(emails) > 1:
                changes.append({
                    "change_type": "contacts_expanded",
                    "new_contacts_count": len(emails),
                    "detected_at": utc_iso_now(),
                })

            item["changes"] = changes
            history_output.append(item)

        return history_output
