"""
GrowX Buying Signal Scorer.
Evaluates observed intent, hiring velocity, tech stack adoption, and capital events.
Score range: 0.0 - 100.0
"""

from typing import Any, Dict, List, Tuple


def calculate_buying_signal(signals: List[Dict[str, Any]]) -> Tuple[float, List[str]]:
    """Evaluates real-time buying and urgency signals."""
    score = 0.0
    reasons = []

    for sig in signals:
        sig_type = sig.get("signal_type", "")
        if sig_type == "funding_raised":
            score += 40.0
            reasons.append("Recent funding signal detected (+40)")
        elif sig_type == "hiring_growth":
            score += 35.0
            reasons.append("Hiring growth velocity detected (+35)")
        elif sig_type == "tech_stack_active":
            score += 25.0
            reasons.append("Active modern tech stack observed (+25)")

    return min(score, 100.0), reasons
