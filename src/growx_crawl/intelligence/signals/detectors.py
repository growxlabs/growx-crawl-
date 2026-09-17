"""
GrowX Buying Signal Detectors.
Detects signal candidates from timeline events and company data.
"""

from typing import Any, Dict, List
from growx_crawl.intelligence.signals.models import (
    SignalCandidateEntity,
    SignalEntity,
    SignalType,
)
from growx_crawl.intelligence.history.models import TimelineEventEntity
from growx_crawl.shared.ids import generate_id
from growx_crawl.shared.time import utc_iso_now


def detect_signals_from_company(company_id: str, company_data: Dict[str, Any]) -> List[SignalEntity]:
    """Legacy: scans company attributes and returns high-confidence buying signals."""
    signals: List[SignalEntity] = []

    # 1. Check for funding indicator
    funding = company_data.get("funding_stage") or company_data.get("total_funding")
    if funding:
        signals.append(SignalEntity(
            id=generate_id("sig_"),
            entity_id=company_id,
            signal_type="funding_raised",
            title="Capital Infusion / Funding",
            description=f"Company reported active funding stage or capital: {funding}",
            confidence=0.90,
        ))

    # 2. Check for technology modernization
    techs = company_data.get("technologies_used") or []
    if isinstance(techs, list) and len(techs) >= 3:
        signals.append(SignalEntity(
            id=generate_id("sig_"),
            entity_id=company_id,
            signal_type="tech_stack_active",
            title="Modern Tech Stack Observed",
            description=f"Active technologies identified: {', '.join(str(t) for t in techs[:5])}",
            confidence=0.85,
        ))

    return signals


# Event type to signal type mapping
_EVENT_TO_SIGNAL: Dict[str, str] = {
    "fact_changed": "",  # depends on predicate
    "technology_added": SignalType.TECHNOLOGY_ADOPTION.value,
    "technology_removed": SignalType.TECHNOLOGY_REMOVAL.value,
    "location_added": SignalType.LOCATION_EXPANSION.value,
    "employment_started": SignalType.LEADERSHIP_CHANGE.value,
    "employment_ended": SignalType.LEADERSHIP_CHANGE.value,
    "product_added": SignalType.PRODUCT_LAUNCH.value,
}

# Predicate-based signal mapping for fact_changed events
_PREDICATE_TO_SIGNAL: Dict[str, str] = {
    "company.employee_count": SignalType.HIRING_GROWTH.value,
    "company.employee_range": SignalType.HIRING_GROWTH.value,
    "company.headquarters": SignalType.LOCATION_EXPANSION.value,
}


class SignalCandidateDetector:
    """Detects signal candidates from timeline events."""

    def detect_from_timeline_events(
        self,
        entity_id: str,
        events: List[TimelineEventEntity],
        entity_type: str = "company",
    ) -> List[SignalCandidateEntity]:
        """
        Map timeline events to signal candidates.
        Every signal traces back to timeline events -> facts -> observations -> evidence.
        """
        candidates: List[SignalCandidateEntity] = []

        for event in events:
            signal_type = self._resolve_signal_type(event)
            if not signal_type:
                continue

            # Skip low-significance events for signal candidacy
            if event.significance == "low":
                continue

            candidate = SignalCandidateEntity(
                id=generate_id("sigc_"),
                entity_type=entity_type,
                entity_id=entity_id,
                signal_type=signal_type,
                trigger_event_ids=[event.id],
                detected_at=utc_iso_now(),
                occurred_at=event.occurred_at,
                confidence=event.confidence,
                significance=event.significance,
                status="candidate",
            )
            candidates.append(candidate)

        return candidates

    def _resolve_signal_type(self, event: TimelineEventEntity) -> str:
        """Determine signal type from event type and predicate."""
        # Direct event-type mapping
        signal = _EVENT_TO_SIGNAL.get(event.event_type, "")
        if signal:
            return signal

        # Predicate-based mapping for generic fact changes
        if event.event_type == "fact_changed" and event.predicate:
            return _PREDICATE_TO_SIGNAL.get(event.predicate, "")

        return ""
