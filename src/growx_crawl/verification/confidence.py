"""
GrowX Verification Confidence.
Calculates multi-signal verification confidence scores.
"""

from typing import List


def calculate_verification_confidence(check_scores: List[float]) -> float:
    """Combines individual check confidences into a single bounded score [0.0, 1.0]."""
    if not check_scores:
        return 0.0
    # Minimum failing check caps confidence, but average provides fidelity
    min_score = min(check_scores)
    avg_score = sum(check_scores) / len(check_scores)
    return round(min_score * 0.4 + avg_score * 0.6, 3)
