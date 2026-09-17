"""
GrowX Match Explainability.
Generates human-readable summaries and signal breakdowns for match confidence.
"""

from typing import List
from growx_crawl.entity_resolution.decisions import evaluate_decision
from growx_crawl.entity_resolution.models import MatchExplanation, MatchSignal


def build_explanation(signals: List[MatchSignal]) -> MatchExplanation:
    """Combines individual match signals into an explanation model with recommended decision."""
    if not signals:
        return MatchExplanation(
            summary="No matching features detected.",
            signals=[],
            confidence=0.0,
            recommended_decision=evaluate_decision(0.0),
        )

    # Max single signal or weighted composition
    top_score = max(s.score for s in signals)
    desc_list = [f"{s.name} ({s.score:.2f}): {s.description}" for s in signals]
    summary = "; ".join(desc_list)

    return MatchExplanation(
        summary=summary,
        signals=signals,
        confidence=top_score,
        recommended_decision=evaluate_decision(top_score),
    )
