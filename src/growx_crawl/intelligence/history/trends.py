"""
GrowX Trend Calculators and Engine.
Computes derived temporal metrics from fact value history.
"""

from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Any, Dict, List, Optional

from growx_crawl.intelligence.history.models import TrendEntity, TrendType, TrendWindow
from growx_crawl.shared.ids import generate_id
from growx_crawl.shared.time import parse_iso, utc_iso_now, utc_now, format_iso


class TrendCalculator(ABC):
    """Base class for trend calculators."""

    @abstractmethod
    def trend_type(self) -> str: ...

    @abstractmethod
    def calculate(
        self,
        entity_type: str,
        entity_id: str,
        fact_values: List[Dict[str, Any]],
        window_days: int,
    ) -> Optional[TrendEntity]: ...


class EmployeeGrowthCalculator(TrendCalculator):
    """Calculates employee count growth over a time window."""

    def trend_type(self) -> str:
        return TrendType.EMPLOYEE_GROWTH.value

    def calculate(
        self,
        entity_type: str,
        entity_id: str,
        fact_values: List[Dict[str, Any]],
        window_days: int,
    ) -> Optional[TrendEntity]:
        now = utc_now()
        window_start = now - timedelta(days=window_days)

        # Filter to employee_count values within window
        relevant = []
        for fv in fact_values:
            vf = parse_iso(fv.get("valid_from"))
            if vf and vf >= window_start:
                val = _extract_number(fv.get("value_json", {}))
                if val is not None:
                    relevant.append((vf, val))

        # Also include the most recent value before the window (baseline)
        baseline_val = None
        for fv in fact_values:
            vf = parse_iso(fv.get("valid_from"))
            if vf and vf < window_start:
                val = _extract_number(fv.get("value_json", {}))
                if val is not None:
                    baseline_val = val
                    break

        if not relevant:
            return None

        # Sort by time ascending
        relevant.sort(key=lambda x: x[0])

        earliest_val = baseline_val if baseline_val is not None else relevant[0][1]
        latest_val = relevant[-1][1]

        if earliest_val == 0:
            growth_pct = 0.0
        else:
            growth_pct = round(((latest_val - earliest_val) / earliest_val) * 100.0, 2)

        # Confidence based on number of observations
        confidence = min(0.5 + len(relevant) * 0.1, 0.99)

        return TrendEntity(
            id=generate_id("trd_"),
            entity_type=entity_type,
            entity_id=entity_id,
            trend_type=self.trend_type(),
            window_start=format_iso(window_start) or "",
            window_end=format_iso(now) or "",
            value_json={
                "earliest_value": earliest_val,
                "latest_value": latest_val,
                "absolute_delta": latest_val - earliest_val,
                "growth_percentage": growth_pct,
                "observation_count": len(relevant),
            },
            confidence=confidence,
            source_fact_ids=[fv.get("fact_id", "") for fv in fact_values[:5]],
        )


class LeadershipChangeCalculator(TrendCalculator):
    """Calculates leadership change rate from employment events."""

    def trend_type(self) -> str:
        return TrendType.LEADERSHIP_CHANGE_RATE.value

    def calculate(
        self,
        entity_type: str,
        entity_id: str,
        fact_values: List[Dict[str, Any]],
        window_days: int,
    ) -> Optional[TrendEntity]:
        now = utc_now()
        window_start = now - timedelta(days=window_days)

        # Count leadership changes (employment_started/ended events for this entity)
        change_count = 0
        for fv in fact_values:
            detected = parse_iso(fv.get("detected_at") or fv.get("valid_from"))
            if detected and detected >= window_start:
                change_count += 1

        if change_count == 0:
            return None

        return TrendEntity(
            id=generate_id("trd_"),
            entity_type=entity_type,
            entity_id=entity_id,
            trend_type=self.trend_type(),
            window_start=format_iso(window_start) or "",
            window_end=format_iso(now) or "",
            value_json={
                "change_count": change_count,
                "window_days": window_days,
            },
            confidence=0.8,
        )


class LocationExpansionCalculator(TrendCalculator):
    """Calculates location expansion over a time window."""

    def trend_type(self) -> str:
        return TrendType.LOCATION_EXPANSION.value

    def calculate(
        self,
        entity_type: str,
        entity_id: str,
        fact_values: List[Dict[str, Any]],
        window_days: int,
    ) -> Optional[TrendEntity]:
        now = utc_now()
        window_start = now - timedelta(days=window_days)

        new_locations = 0
        for fv in fact_values:
            first_seen = parse_iso(fv.get("first_seen_at") or fv.get("valid_from"))
            if first_seen and first_seen >= window_start:
                new_locations += 1

        if new_locations == 0:
            return None

        return TrendEntity(
            id=generate_id("trd_"),
            entity_type=entity_type,
            entity_id=entity_id,
            trend_type=self.trend_type(),
            window_start=format_iso(window_start) or "",
            window_end=format_iso(now) or "",
            value_json={
                "new_locations": new_locations,
                "window_days": window_days,
            },
            confidence=0.85,
        )


class TechnologyAdoptionCalculator(TrendCalculator):
    """Tracks technology adoption/removal rates."""

    def trend_type(self) -> str:
        return TrendType.TECHNOLOGY_CHANGE_RATE.value

    def calculate(
        self,
        entity_type: str,
        entity_id: str,
        fact_values: List[Dict[str, Any]],
        window_days: int,
    ) -> Optional[TrendEntity]:
        now = utc_now()
        window_start = now - timedelta(days=window_days)

        added = 0
        removed = 0
        for fv in fact_values:
            first_seen = parse_iso(fv.get("first_seen_at") or fv.get("valid_from"))
            status = fv.get("status", "accepted")
            if first_seen and first_seen >= window_start:
                if status == "accepted":
                    added += 1
                elif status == "superseded":
                    removed += 1

        if added == 0 and removed == 0:
            return None

        return TrendEntity(
            id=generate_id("trd_"),
            entity_type=entity_type,
            entity_id=entity_id,
            trend_type=self.trend_type(),
            window_start=format_iso(window_start) or "",
            window_end=format_iso(now) or "",
            value_json={
                "technologies_added": added,
                "technologies_removed": removed,
                "net_change": added - removed,
                "window_days": window_days,
            },
            confidence=0.8,
        )


class TrendEngine:
    """Orchestrates trend calculators across multiple windows."""

    WINDOW_DAYS = {
        TrendWindow.D30.value: 30,
        TrendWindow.D90.value: 90,
        TrendWindow.D180.value: 180,
        TrendWindow.D365.value: 365,
    }

    def __init__(self):
        self.calculators: List[TrendCalculator] = [
            EmployeeGrowthCalculator(),
            LeadershipChangeCalculator(),
            LocationExpansionCalculator(),
            TechnologyAdoptionCalculator(),
        ]

    def calculate_trends(
        self,
        entity_type: str,
        entity_id: str,
        fact_values_by_type: Dict[str, List[Dict[str, Any]]],
        windows: Optional[List[str]] = None,
    ) -> List[TrendEntity]:
        """Calculate all applicable trends for an entity."""
        results: List[TrendEntity] = []
        target_windows = windows or [TrendWindow.D90.value, TrendWindow.D365.value]

        for calc in self.calculators:
            # Map calculator to appropriate fact values
            trend_type = calc.trend_type()
            values = fact_values_by_type.get(trend_type, [])

            for window_key in target_windows:
                days = self.WINDOW_DAYS.get(window_key, 90)
                trend = calc.calculate(entity_type, entity_id, values, days)
                if trend:
                    results.append(trend)

        return results


def _extract_number(value_json: Any) -> Optional[float]:
    """Extract numeric value from a value_json dict."""
    if isinstance(value_json, (int, float)):
        return float(value_json)
    if isinstance(value_json, dict):
        val = value_json.get("value")
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            try:
                return float(val.replace(",", ""))
            except ValueError:
                return None
    return None
