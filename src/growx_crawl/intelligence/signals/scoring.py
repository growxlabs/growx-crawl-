"""
GrowX Signal Scoring.
Computes confidence, significance, and freshness for signal candidates.
"""

from datetime import timedelta
from typing import Optional

from growx_crawl.intelligence.signals.models import SignalCandidateEntity
from growx_crawl.shared.time import parse_iso, utc_now


def compute_signal_freshness(candidate: SignalCandidateEntity) -> float:
    """
    Compute freshness score (0.0–1.0) based on time since detection.
    Newer signals are fresher. Signals decay linearly over their expiry window.
    """
    now = utc_now()
    detected = parse_iso(candidate.detected_at)
    if detected is None:
        return 0.5

    age = now - detected
    age_days = age.total_seconds() / 86400.0

    # Default expiry windows by signal type
    max_days = _get_expiry_days(candidate.signal_type)

    if age_days <= 0:
        return 1.0
    if age_days >= max_days:
        return 0.0

    return round(1.0 - (age_days / max_days), 3)


def compute_signal_score(candidate: SignalCandidateEntity) -> dict:
    """
    Compute composite signal score with confidence, significance, and freshness.
    Does NOT include ICP fit — that comes later.
    """
    freshness = compute_signal_freshness(candidate)

    return {
        "confidence": candidate.confidence,
        "significance": candidate.significance,
        "freshness": freshness,
        "composite": round(candidate.confidence * freshness, 3),
    }


def _get_expiry_days(signal_type: str) -> float:
    """Get default expiry window in days for a signal type."""
    expiry_map = {
        "leadership_change": 135,    # 90-180 days, use midpoint
        "hiring_growth": 60,         # 30-90 days
        "location_expansion": 270,   # longer
        "technology_adoption": 365,  # technology signals last longer
        "technology_removal": 180,
        "product_launch": 180,
        "market_expansion": 270,
        "operational_expansion": 270,
        "funding_raised": 180,
    }
    return expiry_map.get(signal_type, 180)
