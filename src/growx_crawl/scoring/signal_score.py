"""
GrowX Signal Score Calculator.
Evaluates the intrinsic strength and relevance of detected company events with diminishing returns combination.
"""

from typing import Any, Dict, List, Optional
from growx_crawl.scoring.models import RankingReasonCode, SignalScoreResult
from growx_crawl.scoring.policies import SIGNAL_TYPE_WEIGHTS, normalize_score


class SignalScoreCalculator:
    """Calculates signal strength score from detected historical events."""

    def calculate(
        self,
        signals: Optional[List[Any]] = None,
        custom_weights: Optional[Dict[str, float]] = None,
    ) -> SignalScoreResult:
        if not signals:
            return SignalScoreResult(
                score=0.0,
                active_signals_count=0,
                signals_evaluated=[],
                reason_codes=[],
                contributions={},
            )

        weights = custom_weights or SIGNAL_TYPE_WEIGHTS
        reasons: List[str] = []
        evaluated: List[Dict[str, Any]] = []
        raw_signal_points = 0.0
        contributions: Dict[str, float] = {}

        has_expansion = False
        has_contraction = False

        for sig in signals:
            s_type = getattr(sig, "signal_type", None) or (
                sig.get("signal_type") if isinstance(sig, dict) else str(sig)
            )
            s_type_clean = str(s_type).lower()
            confidence = float(getattr(sig, "confidence", 1.0) if hasattr(sig, "confidence") else sig.get("confidence", 1.0) if isinstance(sig, dict) else 1.0)

            base_w = weights.get(s_type_clean, 0.5)
            effective_contrib = round(base_w * confidence, 3)
            raw_signal_points += effective_contrib

            evaluated.append({"type": s_type_clean, "confidence": confidence, "contribution": effective_contrib})
            contributions[s_type_clean] = effective_contrib

            # Tag specific reason codes
            if "expansion" in s_type_clean:
                has_expansion = True
                if RankingReasonCode.RECENT_EXPANSION.value not in reasons:
                    reasons.append(RankingReasonCode.RECENT_EXPANSION.value)
            elif "leadership" in s_type_clean or "executive" in s_type_clean:
                if RankingReasonCode.RECENT_LEADERSHIP_CHANGE.value not in reasons:
                    reasons.append(RankingReasonCode.RECENT_LEADERSHIP_CHANGE.value)
            elif "funding" in s_type_clean:
                if RankingReasonCode.FUNDING_RAISED.value not in reasons:
                    reasons.append(RankingReasonCode.FUNDING_RAISED.value)
            elif "tech" in s_type_clean:
                if RankingReasonCode.TECH_ADOPTION.value not in reasons:
                    reasons.append(RankingReasonCode.TECH_ADOPTION.value)
            elif "contraction" in s_type_clean or "layoff" in s_type_clean:
                has_contraction = True

        # Signal conflict penalty (Section 50)
        conflict_penalty = 0.0
        if has_expansion and has_contraction:
            conflict_penalty = 0.25
            raw_signal_points = max(0.0, raw_signal_points - conflict_penalty)

        # Capped diminishing returns curve: 1 - exp(-points) or asymptotic formula
        # 1 signal (0.85 pts) -> ~0.70; 2 signals (1.7 pts) -> ~0.90; 3+ signals -> ~0.98
        score = 1.0 - (1.0 / (1.0 + raw_signal_points * 1.5))
        if conflict_penalty > 0:
            score = max(0.0, score - conflict_penalty)

        score = normalize_score(score)
        if score >= 0.70 and RankingReasonCode.HIGH_INTENT_SIGNAL.value not in reasons:
            reasons.append(RankingReasonCode.HIGH_INTENT_SIGNAL.value)

        return SignalScoreResult(
            score=score,
            active_signals_count=len(evaluated),
            signals_evaluated=evaluated,
            reason_codes=reasons,
            contributions=contributions,
        )
