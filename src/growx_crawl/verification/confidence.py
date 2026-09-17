"""
GrowX Verification Confidence Engine.
Implements the multi-factor operational trust formula and subject-specific weight profiles.
"""

from typing import Dict, List, Optional

CONFIDENCE_PROFILES: Dict[str, Dict[str, float]] = {
    "company": {
        "base_source_weight": 0.20,
        "identity_weight": 0.25,
        "source_agreement_weight": 0.20,
        "technical_checks_weight": 0.25,
        "freshness_weight": 0.10,
    },
    "domain": {
        "base_source_weight": 0.10,
        "identity_weight": 0.10,
        "source_agreement_weight": 0.10,
        "technical_checks_weight": 0.60,
        "freshness_weight": 0.10,
    },
    "company_domain": {
        "base_source_weight": 0.20,
        "identity_weight": 0.35,
        "source_agreement_weight": 0.20,
        "technical_checks_weight": 0.15,
        "freshness_weight": 0.10,
    },
    "person": {
        "base_source_weight": 0.25,
        "identity_weight": 0.30,
        "source_agreement_weight": 0.25,
        "technical_checks_weight": 0.10,
        "freshness_weight": 0.10,
    },
    "employment": {
        "base_source_weight": 0.20,
        "identity_weight": 0.25,
        "source_agreement_weight": 0.25,
        "technical_checks_weight": 0.15,
        "freshness_weight": 0.15,
    },
    "email": {
        "base_source_weight": 0.10,
        "identity_weight": 0.15,
        "source_agreement_weight": 0.10,
        "technical_checks_weight": 0.55,
        "freshness_weight": 0.10,
    },
    "fact": {
        "base_source_weight": 0.30,
        "identity_weight": 0.15,
        "source_agreement_weight": 0.30,
        "technical_checks_weight": 0.10,
        "freshness_weight": 0.15,
    },
}


def compute_verification_confidence(
    subject_type: str,
    base_source_score: float = 0.80,
    identity_strength: float = 0.80,
    source_agreement: float = 0.80,
    technical_checks_score: float = 0.80,
    freshness_score: float = 1.0,
    conflict_penalty: float = 0.0,
    staleness_penalty: float = 0.0,
) -> float:
    """
    Computes operational verification confidence [0.0, 1.0] using subject-specific weights.
    """
    weights = CONFIDENCE_PROFILES.get(subject_type.lower(), CONFIDENCE_PROFILES["company"])

    raw_score = (
        base_source_score * weights["base_source_weight"]
        + identity_strength * weights["identity_weight"]
        + source_agreement * weights["source_agreement_weight"]
        + technical_checks_score * weights["technical_checks_weight"]
        + freshness_score * weights["freshness_weight"]
        - conflict_penalty
        - staleness_penalty
    )

    return round(min(max(raw_score, 0.0), 1.0), 3)


def calculate_verification_confidence(check_scores: List[float]) -> float:
    """Backward-compatible helper combining raw check scores."""
    if not check_scores:
        return 0.0
    min_score = min(check_scores)
    avg_score = sum(check_scores) / len(check_scores)
    return round(min_score * 0.4 + avg_score * 0.6, 3)
