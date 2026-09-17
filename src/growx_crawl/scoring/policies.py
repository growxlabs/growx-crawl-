"""
GrowX Ranking Policies.
Defines seniority tier scoring, signal importance weights, decay parameters, and normalization rules.
"""

from typing import Dict

# Seniority weights for buyer persona evaluation
SENIORITY_TIER_SCORES: Dict[str, float] = {
    "c_suite": 1.0,
    "executive": 1.0,
    "vp": 0.95,
    "vice_president": 0.95,
    "director": 0.85,
    "head": 0.85,
    "manager": 0.65,
    "lead": 0.65,
    "individual_contributor": 0.40,
}

# Signal candidate intrinsic relevance weights
SIGNAL_TYPE_WEIGHTS: Dict[str, float] = {
    "location_expansion": 0.90,
    "hiring_growth": 0.85,
    "leadership_change": 0.80,
    "funding_raised": 0.85,
    "tech_adoption": 0.75,
    "product_launch": 0.70,
    "partnership": 0.65,
}

# Default decay thresholds in days
FRESH_SIGNAL_DAYS = 30
MEDIUM_SIGNAL_DAYS = 90
EXPIRED_SIGNAL_DAYS = 180

# Staleness thresholds
STALE_EMPLOYMENT_DAYS = 180
STALE_COMPANY_FACT_DAYS = 270


def normalize_score(val: float) -> float:
    """Ensures a numerical score is clamped to [0.0, 1.0] and rounded to 3 decimals."""
    return round(min(1.0, max(0.0, float(val))), 3)
