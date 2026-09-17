"""
GrowX Fact History Change Detector.
Identifies significant semantic changes between past and new fact values.
Suppresses formatting-only changes and extractor version artifacts.
"""

import hashlib
import json
import re
from typing import Any, Dict, List, Optional, Tuple

from growx_crawl.intelligence.history.models import ChangeEventType, TimelineEventEntity
from growx_crawl.shared.ids import generate_id
from growx_crawl.shared.time import utc_iso_now


# Characters stripped during normalization comparison
_NOISE_CHARS = re.compile(r"[~\s\u00a0,]+")
_EMPLOYEE_APPROX = re.compile(r"^[~\u2248]?\s*(\d[\d,]*)\s*(employees?|staff|people)?$", re.I)


def _normalize_for_comparison(value: Any) -> str:
    """Normalize a value for comparison, stripping formatting noise."""
    if value is None:
        return ""
    s = str(value).strip().lower()
    s = _NOISE_CHARS.sub("", s)
    return s


def _extract_numeric(value: Any) -> Optional[float]:
    """Extract numeric value from various representations."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        # Handle "~250 employees", "250", etc.
        m = _EMPLOYEE_APPROX.match(value.strip())
        if m:
            return float(m.group(1).replace(",", ""))
        cleaned = value.strip().replace(",", "")
        try:
            return float(cleaned)
        except ValueError:
            return None
    if isinstance(value, dict):
        v = value.get("value")
        if v is not None:
            return _extract_numeric(v)
    return None


def _extract_value(value_json: Dict[str, Any]) -> Any:
    """Extract the core value from a value_json wrapper."""
    if not value_json:
        return None
    return value_json.get("value", value_json)


class ChangeDetector:
    """
    Detects meaningful changes between fact values.
    Suppresses false changes from formatting, normalization, and extractor version differences.
    """

    def detect_fact_change(
        self,
        entity_type: str,
        entity_id: str,
        fact_id: str,
        predicate: str,
        old_value_json: Dict[str, Any],
        new_value_json: Dict[str, Any],
        occurred_at: str,
        confidence: float = 1.0,
        verification_state: str = "unverified",
        old_extractor_version: Optional[str] = None,
        new_extractor_version: Optional[str] = None,
        source_id: Optional[str] = None,
        observation_id: Optional[str] = None,
        evidence_ids: Optional[List[str]] = None,
    ) -> Optional[TimelineEventEntity]:
        """
        Compare old and new fact values. Returns a TimelineEventEntity if a
        meaningful change is detected, None otherwise.
        """
        old_val = _extract_value(old_value_json)
        new_val = _extract_value(new_value_json)

        # Check for formatting-only change
        if self._is_formatting_only_change(old_val, new_val, predicate):
            return None

        # Check for extractor version artifact
        if self._is_extractor_change(old_extractor_version, new_extractor_version):
            # Create interpretation_revised event instead of real-world change
            fingerprint = self.compute_fingerprint(
                entity_type, entity_id, predicate,
                old_value_json, new_value_json, occurred_at,
            )
            return TimelineEventEntity(
                id=generate_id("evt_"),
                entity_type=entity_type,
                entity_id=entity_id,
                event_type=ChangeEventType.INTERPRETATION_REVISED.value,
                occurred_at=occurred_at,
                detected_at=utc_iso_now(),
                source_id=source_id,
                fact_id=fact_id,
                observation_id=observation_id,
                evidence_ids=evidence_ids or [],
                predicate=predicate,
                previous_value_json=old_value_json,
                new_value_json=new_value_json,
                confidence=confidence * 0.5,  # lower confidence for interpretation changes
                verification_state=verification_state,
                significance="low",
                fingerprint=fingerprint,
                extractor_version=new_extractor_version,
                metadata_json={"reason": "extractor_version_change"},
            )

        # Determine change type
        event_type = ChangeEventType.FACT_CHANGED.value

        # Compute deltas for numeric predicates
        metadata: Dict[str, Any] = {}
        deltas = self.compute_numeric_delta(old_val, new_val)
        if deltas:
            metadata["absolute_delta"] = deltas[0]
            metadata["percentage_delta"] = deltas[1]

        # Range transition
        range_info = self.compute_range_transition(old_val, new_val)
        if range_info:
            metadata["range_transition"] = range_info

        fingerprint = self.compute_fingerprint(
            entity_type, entity_id, predicate,
            old_value_json, new_value_json, occurred_at,
        )

        return TimelineEventEntity(
            id=generate_id("evt_"),
            entity_type=entity_type,
            entity_id=entity_id,
            event_type=event_type,
            occurred_at=occurred_at,
            detected_at=utc_iso_now(),
            source_id=source_id,
            fact_id=fact_id,
            observation_id=observation_id,
            evidence_ids=evidence_ids or [],
            predicate=predicate,
            previous_value_json=old_value_json,
            new_value_json=new_value_json,
            confidence=confidence,
            verification_state=verification_state,
            fingerprint=fingerprint,
            extractor_version=new_extractor_version,
            metadata_json=metadata,
        )

    def detect_multivalue_changes(
        self,
        entity_type: str,
        entity_id: str,
        fact_id: str,
        predicate: str,
        old_values: List[Any],
        new_values: List[Any],
        occurred_at: str,
        confidence: float = 1.0,
        verification_state: str = "unverified",
    ) -> List[TimelineEventEntity]:
        """Detect add/remove/reappear events for multi-value predicates."""
        events: List[TimelineEventEntity] = []

        old_set = {_normalize_for_comparison(v) for v in old_values if v}
        new_set = {_normalize_for_comparison(v) for v in new_values if v}

        # Map normalized back to original for display
        old_map = {_normalize_for_comparison(v): v for v in old_values if v}
        new_map = {_normalize_for_comparison(v): v for v in new_values if v}

        # Determine event type prefix based on predicate
        event_prefix = _predicate_to_event_prefix(predicate)

        # Added values
        for norm_val in new_set - old_set:
            original = new_map.get(norm_val, norm_val)
            event_type = f"{event_prefix}_added" if event_prefix else ChangeEventType.FACT_CREATED.value
            fp = self.compute_fingerprint(
                entity_type, entity_id, predicate,
                {}, {"value": original}, occurred_at,
            )
            events.append(TimelineEventEntity(
                id=generate_id("evt_"),
                entity_type=entity_type,
                entity_id=entity_id,
                event_type=event_type,
                occurred_at=occurred_at,
                fact_id=fact_id,
                predicate=predicate,
                previous_value_json={},
                new_value_json={"value": original},
                confidence=confidence,
                verification_state=verification_state,
                fingerprint=fp,
            ))

        # Removed values
        for norm_val in old_set - new_set:
            original = old_map.get(norm_val, norm_val)
            event_type = f"{event_prefix}_removed" if event_prefix else ChangeEventType.FACT_REMOVED.value
            fp = self.compute_fingerprint(
                entity_type, entity_id, predicate,
                {"value": original}, {}, occurred_at,
            )
            events.append(TimelineEventEntity(
                id=generate_id("evt_"),
                entity_type=entity_type,
                entity_id=entity_id,
                event_type=event_type,
                occurred_at=occurred_at,
                fact_id=fact_id,
                predicate=predicate,
                previous_value_json={"value": original},
                new_value_json={},
                confidence=confidence,
                verification_state=verification_state,
                fingerprint=fp,
            ))

        return events

    def _is_formatting_only_change(self, old_val: Any, new_val: Any, predicate: str) -> bool:
        """Returns True if the difference is only formatting/normalization noise."""
        if old_val is None and new_val is None:
            return True
        if old_val is None or new_val is None:
            return False

        old_norm = _normalize_for_comparison(old_val)
        new_norm = _normalize_for_comparison(new_val)

        if old_norm == new_norm:
            return True

        # Numeric equivalence: "250 employees" vs "~250 employees" vs 250
        old_num = _extract_numeric(old_val)
        new_num = _extract_numeric(new_val)
        if old_num is not None and new_num is not None and old_num == new_num:
            return True

        return False

    def _is_extractor_change(
        self,
        old_version: Optional[str],
        new_version: Optional[str],
    ) -> bool:
        """Returns True if versions differ, indicating a potential interpretation change."""
        if old_version is None or new_version is None:
            return False
        return old_version != new_version

    def compute_numeric_delta(
        self, old_val: Any, new_val: Any
    ) -> Optional[Tuple[float, float]]:
        """Returns (absolute_delta, percentage_delta) for numeric values."""
        old_num = _extract_numeric(old_val)
        new_num = _extract_numeric(new_val)
        if old_num is None or new_num is None:
            return None
        if old_num == 0:
            return (new_num - old_num, 0.0)
        absolute = new_num - old_num
        percentage = (absolute / old_num) * 100.0
        return (absolute, round(percentage, 2))

    def compute_range_transition(
        self, old_val: Any, new_val: Any
    ) -> Optional[Dict[str, Any]]:
        """Detects range transitions like '51-200' -> '201-500'."""
        old_range = _parse_range(old_val)
        new_range = _parse_range(new_val)
        if old_range and new_range and old_range != new_range:
            return {
                "old_range": old_range,
                "new_range": new_range,
            }
        return None

    @staticmethod
    def compute_fingerprint(
        entity_type: str,
        entity_id: str,
        predicate: str,
        old_value_json: Dict[str, Any],
        new_value_json: Dict[str, Any],
        effective_time: str,
    ) -> str:
        """Compute a stable hash for idempotent event deduplication."""
        parts = [
            entity_type, entity_id, predicate,
            json.dumps(old_value_json, sort_keys=True),
            json.dumps(new_value_json, sort_keys=True),
            effective_time,
        ]
        raw = "|".join(parts)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def _predicate_to_event_prefix(predicate: str) -> str:
    """Map predicate name to event type prefix for multi-value changes."""
    mapping = {
        "company.technology": "technology",
        "company.product": "product",
        "company.service": "product",
        "company.location": "location",
    }
    return mapping.get(predicate, "")


def _parse_range(value: Any) -> Optional[Tuple[int, int]]:
    """Parse range strings like '51-200' or '201-500'."""
    if value is None:
        return None
    s = str(value).strip()
    # Handle dict wrapper
    if isinstance(value, dict):
        if "min" in value and "max" in value:
            try:
                return (int(value["min"]), int(value["max"]))
            except (ValueError, TypeError):
                return None
        s = str(value.get("value", "")).strip()

    # Parse "51-200" or "51 - 200"
    match = re.match(r"(\d+)\s*[-\u2013]\s*(\d+)", s)
    if match:
        return (int(match.group(1)), int(match.group(2)))
    return None


# Backward compatibility
def detect_value_change(old_value: Any, new_value: Any, predicate: str) -> Optional[Dict[str, Any]]:
    """Legacy function preserved for backward compatibility."""
    detector = ChangeDetector()
    if detector._is_formatting_only_change(old_value, new_value, predicate):
        return None

    change_type = "updated"
    if predicate == "company.employee_count":
        old_num = _extract_numeric(old_value)
        new_num = _extract_numeric(new_value)
        if old_num is not None and new_num is not None:
            if new_num > old_num:
                change_type = "headcount_growth"
            elif new_num < old_num:
                change_type = "headcount_contraction"

    return {
        "predicate": predicate,
        "old_value": old_value,
        "new_value": new_value,
        "change_type": change_type,
    }
