from typing import Dict, Optional

AUTHORITY_WEIGHTS: Dict[str, float] = {
    "official": 0.98,
    "registry": 0.95,
    "first_party": 0.90,
    "trusted_directory": 0.80,
    "third_party": 0.70,
    "user_supplied": 0.65,
    "search_snippet": 0.50,
    "unknown": 0.50,
}


def compute_fact_confidence(
    authority_class: str = "first_party",
    extractor_confidence: float = 1.0,
    num_independent_sources: int = 1,
    is_verified: bool = False,
) -> float:
    """
    Computes calibrated fact confidence based on source authority, extractor certainty,
    and multi-source agreement without conflating mathematical certainty with operational signal.
    """
    auth_weight = AUTHORITY_WEIGHTS.get(authority_class.strip().lower(), 0.50)
    base_conf = auth_weight * min(max(extractor_confidence, 0.1), 1.0)

    # Multi-source agreement boost (Section 50)
    if num_independent_sources > 1:
        boost = min((num_independent_sources - 1) * 0.04, 0.12)
        base_conf += boost

    if is_verified:
        base_conf = max(base_conf, 0.95)

    return round(min(max(base_conf, 0.0), 0.99), 2)
