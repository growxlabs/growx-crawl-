"""
GrowX Verification Freshness Engine.
Evaluates time-decay freshness states, valid_until deadlines, and refresh scheduling.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple
from growx_crawl.shared.time import parse_iso, utc_now
from growx_crawl.verification.models import FreshnessState


def calculate_valid_until(verified_at: Optional[datetime], ttl_hours: int) -> datetime:
    """Calculates expiration timestamp given verification time and TTL in hours."""
    base = verified_at or utc_now()
    return base + timedelta(hours=ttl_hours)


def evaluate_freshness(
    verified_at_iso: str,
    valid_until_iso: Optional[str] = None,
    ttl_hours: int = 168,
) -> Tuple[FreshnessState, float]:
    """
    Evaluates freshness of a verified record.
    Returns (FreshnessState, freshness_ratio) where freshness_ratio in [0.0, 1.0].
    """
    v_at = parse_iso(verified_at_iso)
    if not v_at:
        return FreshnessState.EXPIRED, 0.0

    now = utc_now()
    age_seconds = (now - v_at).total_seconds()
    ttl_seconds = ttl_hours * 3600

    if age_seconds < 0:
        return FreshnessState.FRESH, 1.0

    ratio = max(1.0 - (age_seconds / ttl_seconds), 0.0)

    if age_seconds <= ttl_seconds * 0.5:
        return FreshnessState.FRESH, round(ratio, 2)
    elif age_seconds <= ttl_seconds:
        return FreshnessState.AGING, round(ratio, 2)
    elif age_seconds <= ttl_seconds * 1.5:
        return FreshnessState.STALE, round(ratio, 2)
    else:
        return FreshnessState.EXPIRED, 0.0


def recommend_refresh(
    subject_type: str,
    freshness_state: FreshnessState,
    priority: str = "normal",
) -> Dict[str, Any]:
    """Determines whether a verification refresh is recommended and assigns queue priority."""
    needs_refresh = freshness_state in (FreshnessState.STALE, FreshnessState.EXPIRED)
    if priority in ("campaign_active", "outreach_imminent") and freshness_state == FreshnessState.AGING:
        needs_refresh = True

    return {
        "subject_type": subject_type,
        "needs_refresh": needs_refresh,
        "freshness_state": freshness_state.value,
        "priority_level": 1 if priority == "outreach_imminent" else (2 if priority == "campaign_active" else 5),
    }
