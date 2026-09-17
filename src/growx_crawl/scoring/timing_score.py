"""
GrowX Timing Score Calculator.
Evaluates how actionable and timely detected signals are based on recency decay curves.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from growx_crawl.scoring.models import TimingScoreResult
from growx_crawl.scoring.policies import (
    EXPIRED_SIGNAL_DAYS,
    FRESH_SIGNAL_DAYS,
    MEDIUM_SIGNAL_DAYS,
    normalize_score,
)


class TimingScoreCalculator:
    """Calculates actionable timing score reflecting signal recency and change momentum."""

    def calculate(
        self,
        signals: Optional[List[Any]] = None,
        decay_halflife_days: int = 45,
    ) -> TimingScoreResult:
        if not signals:
            return TimingScoreResult(
                score=0.25,  # Baseline timing without positive/negative trigger
                recency_factor=0.25,
                decay_details={"signals_count": 0},
                reason_codes=[],
                contributions={"baseline": 0.25},
            )

        now = datetime.now(timezone.utc)
        min_age_days: Optional[int] = None
        reasons: List[str] = []
        decay_details: Dict[str, Any] = {}

        decayed_scores = []

        for idx, sig in enumerate(signals):
            occurred_at_str = getattr(sig, "occurred_at", None) or getattr(sig, "detected_at", None) or (
                sig.get("occurred_at") or sig.get("detected_at") if isinstance(sig, dict) else None
            )
            age_days = 15  # Default assumption: 15 days if timestamp omitted

            if occurred_at_str:
                try:
                    iso_str = str(occurred_at_str).replace("Z", "+00:00")
                    dt = datetime.fromisoformat(iso_str)
                    age_days = max(0, (now - dt).days)
                except Exception:
                    pass

            if min_age_days is None or age_days < min_age_days:
                min_age_days = age_days

            # Recency curve
            if age_days <= FRESH_SIGNAL_DAYS:
                recency_multiplier = 1.0
            elif age_days <= MEDIUM_SIGNAL_DAYS:
                recency_multiplier = 0.70
            elif age_days <= EXPIRED_SIGNAL_DAYS:
                recency_multiplier = 0.35
            else:
                recency_multiplier = 0.0

            decayed_scores.append(recency_multiplier)
            decay_details[f"sig_{idx}"] = {"age_days": age_days, "recency": recency_multiplier}

        if min_age_days is not None and min_age_days <= FRESH_SIGNAL_DAYS:
            reasons.append("RECENT_SIGNAL_TIMING")

        # Combine timing: primary fresh signal + boost for multiple recent transitions
        if decayed_scores:
            primary_recency = max(decayed_scores)
            extra_boost = min(0.20, (len([s for s in decayed_scores if s >= 0.7]) - 1) * 0.10) if len(decayed_scores) > 1 else 0.0
            timing_score = min(1.0, primary_recency + extra_boost)
        else:
            timing_score = 0.25

        timing_score = normalize_score(timing_score)

        return TimingScoreResult(
            score=timing_score,
            recency_factor=primary_recency if decayed_scores else 0.25,
            decay_details=decay_details,
            reason_codes=reasons,
            contributions={"recency": timing_score},
        )
