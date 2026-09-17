"""
GrowX Change Significance Engine.
Evaluates whether a detected change is low, medium, high, or critical significance.
"""

from typing import Any, Dict, Optional
from growx_crawl.intelligence.history.models import Significance


# Predicate-level default significance
_PREDICATE_SIGNIFICANCE: Dict[str, str] = {
    # High significance predicates
    "company.headquarters": Significance.HIGH.value,
    "company.legal_name": Significance.HIGH.value,
    "company.employee_count": Significance.HIGH.value,
    "company.employee_range": Significance.HIGH.value,
    "company.funding_stage": Significance.HIGH.value,
    "company.revenue_range": Significance.HIGH.value,
    # Medium significance predicates
    "company.industry": Significance.MEDIUM.value,
    "company.technology": Significance.MEDIUM.value,
    "company.description": Significance.LOW.value,
    "company.email": Significance.LOW.value,
    "company.phone": Significance.LOW.value,
    "person.title": Significance.MEDIUM.value,
    "person.email": Significance.LOW.value,
}

# Event type significance overrides
_EVENT_SIGNIFICANCE: Dict[str, str] = {
    "employment_started": Significance.MEDIUM.value,
    "employment_ended": Significance.MEDIUM.value,
    "location_added": Significance.HIGH.value,
    "location_removed": Significance.MEDIUM.value,
    "technology_added": Significance.MEDIUM.value,
    "technology_removed": Significance.MEDIUM.value,
    "domain_changed": Significance.HIGH.value,
    "interpretation_revised": Significance.LOW.value,
}


class SignificanceEngine:
    """Evaluates the significance of a change event."""

    def evaluate(
        self,
        event_type: str,
        predicate: Optional[str] = None,
        magnitude: Optional[float] = None,
        verification_confidence: float = 1.0,
        source_strength: float = 1.0,
    ) -> str:
        """
        Returns significance level based on predicate importance, event type,
        magnitude, and verification confidence.
        """
        # Start with event-type-based significance
        base = _EVENT_SIGNIFICANCE.get(event_type)

        # Override with predicate-specific significance if available
        if predicate and predicate in _PREDICATE_SIGNIFICANCE:
            base = _PREDICATE_SIGNIFICANCE[predicate]

        if not base:
            base = Significance.MEDIUM.value

        # Boost for large magnitude changes
        if magnitude is not None and abs(magnitude) > 50:
            base = _boost_significance(base)

        # Downgrade if verification confidence is low
        if verification_confidence < 0.5:
            base = _downgrade_significance(base)

        return base


def _boost_significance(current: str) -> str:
    """Boost significance by one level."""
    order = [Significance.LOW.value, Significance.MEDIUM.value, Significance.HIGH.value, Significance.CRITICAL.value]
    idx = order.index(current) if current in order else 1
    return order[min(idx + 1, len(order) - 1)]


def _downgrade_significance(current: str) -> str:
    """Downgrade significance by one level."""
    order = [Significance.LOW.value, Significance.MEDIUM.value, Significance.HIGH.value, Significance.CRITICAL.value]
    idx = order.index(current) if current in order else 1
    return order[max(idx - 1, 0)]
