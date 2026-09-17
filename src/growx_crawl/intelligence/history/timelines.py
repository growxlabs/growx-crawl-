"""
GrowX Timeline Builder.
Constructs timeline views and reconstructs historical entity state.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from growx_crawl.intelligence.history.models import TimelineEventEntity
from growx_crawl.shared.time import parse_iso


class TimelineBuilder:
    """Constructs timeline views from raw timeline events."""

    def build_entity_timeline(
        self,
        events: List[TimelineEventEntity],
        include_derived: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Build a sorted, deduplicated, annotated timeline from raw events.
        Returns list of timeline entry dicts suitable for API response.
        """
        # Deduplicate by fingerprint
        seen_fingerprints: set = set()
        unique_events: List[TimelineEventEntity] = []
        for e in events:
            if e.fingerprint not in seen_fingerprints:
                seen_fingerprints.add(e.fingerprint)
                unique_events.append(e)

        # Filter derived events if not wanted
        if not include_derived:
            unique_events = [
                e for e in unique_events
                if e.event_type != "interpretation_revised"
            ]

        # Sort chronologically
        unique_events.sort(key=lambda e: e.occurred_at)

        return [
            {
                "id": e.id,
                "event_type": e.event_type,
                "occurred_at": e.occurred_at,
                "predicate": e.predicate,
                "previous_value": e.previous_value_json,
                "new_value": e.new_value_json,
                "confidence": e.confidence,
                "significance": e.significance,
                "verification_state": e.verification_state,
                "fact_id": e.fact_id,
                "metadata": e.metadata_json,
            }
            for e in unique_events
        ]

    def reconstruct_state_at(
        self,
        facts: List[Dict[str, Any]],
        values: List[Dict[str, Any]],
        target_time: str,
    ) -> Dict[str, Any]:
        """
        Reconstruct what we believed about an entity at a given point in time.
        Uses fact values' valid_from/valid_to to find the active value at target_time.
        """
        target_dt = parse_iso(target_time)
        if target_dt is None:
            return {}

        state: Dict[str, Any] = {}

        for fact in facts:
            predicate = fact.get("predicate", "")
            fact_id = fact.get("id", "")

            # Find the value that was active at target_time for this fact
            fact_values = [v for v in values if v.get("fact_id") == fact_id]

            active_value = None
            for fv in fact_values:
                vf = parse_iso(fv.get("valid_from"))
                vt = parse_iso(fv.get("valid_to"))

                if vf is None:
                    continue

                # Value was valid at target_time if valid_from <= target <= valid_to (or no valid_to)
                if vf <= target_dt:
                    if vt is None or vt >= target_dt:
                        active_value = fv
                        break  # values should be ordered newest-first

            if active_value:
                value_json = active_value.get("value_json", {})
                if isinstance(value_json, str):
                    import json
                    value_json = json.loads(value_json)
                state[predicate] = {
                    "value": value_json,
                    "confidence": active_value.get("confidence", 1.0),
                    "valid_from": active_value.get("valid_from"),
                    "valid_to": active_value.get("valid_to"),
                    "status": active_value.get("status"),
                }

        return state
