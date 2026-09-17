"""
GrowX Confidence Adjustment.
Calculates confidence factors and applies downward calibration for unverified or stale prospect data.
"""

from growx_crawl.scoring.policies import normalize_score


class ConfidenceAdjuster:
    """Combines verification, data quality, and freshness into a confidence multiplier."""

    @staticmethod
    def calculate_confidence_factor(
        verification_confidence: float = 1.0,
        data_quality_score: float = 1.0,
        freshness_score: float = 1.0,
    ) -> float:
        """
        Calculates composite confidence factor (0.20 to 1.0).
        Weak data quality or unverified records temper raw ranking score.
        """
        v = normalize_score(verification_confidence)
        q = normalize_score(data_quality_score)
        f = normalize_score(freshness_score)

        # 45% verification + 35% data quality + 20% freshness
        factor = (0.45 * v) + (0.35 * q) + (0.20 * f)
        return normalize_score(max(0.20, factor))

    @staticmethod
    def adjust_score(raw_score: float, confidence_factor: float) -> float:
        """Applies confidence multiplier to raw score."""
        adjusted = float(raw_score) * float(confidence_factor)
        return normalize_score(adjusted)
