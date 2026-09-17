"""
GrowX Competitor Graph Policies.
Configuration rules, threshold parameters, and canonical pair helpers.
"""

from typing import List, Set
from pydantic import BaseModel, Field


def canonical_pair(company_a: str, company_b: str) -> str:
    """
    Produces a stable, deterministic symmetric pair string: min:max.
    Ensures identical canonical keys regardless of query direction.
    """
    a = company_a.strip().lower()
    b = company_b.strip().lower()
    return f"{min(a, b)}:{max(a, b)}"


class CompetitorVerificationPolicy(BaseModel):
    """Configurable scoring weights, threshold gates, and blocking conditions."""
    policy_version: str = "v1"

    # Strength thresholds
    min_strength_direct: float = 0.60
    min_strength_adjacent: float = 0.35
    min_strength_substitute: float = 0.30

    # Confidence thresholds
    min_confidence_verified: float = 0.70
    min_confidence_supported: float = 0.45
    min_evidence_count_verified: int = 1

    # Overlap component weights (sum to 1.0)
    offering_weight: float = 0.35
    customer_weight: float = 0.25
    market_weight: float = 0.20
    geography_weight: float = 0.10
    explicit_evidence_weight: float = 0.10

    # Blocking relationship types from identity graph
    blocking_relationship_types: List[str] = Field(
        default_factory=lambda: [
            "parent",
            "subsidiary",
            "brand_owner",
            "partner",
            "supplier",
            "customer",
            "acquired",
        ]
    )


DEFAULT_COMPETITOR_POLICY = CompetitorVerificationPolicy()
