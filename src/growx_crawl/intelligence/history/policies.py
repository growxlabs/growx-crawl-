"""
GrowX Change Detection Policies.
Configurable per-predicate policies for disappearance, reappearance, and significance defaults.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChangePolicy(BaseModel):
    """Per-predicate change detection policy."""
    predicate_pattern: str  # glob pattern, e.g. "company.technology" or "company.*"
    disappearance_threshold_days: int = 90
    reappearance_enabled: bool = True
    min_misses_for_removal: int = 2
    significance_default: str = "medium"
    policy_version: str = "v1"


# Built-in default policies
DEFAULT_POLICIES: List[ChangePolicy] = [
    ChangePolicy(
        predicate_pattern="company.employee_count",
        disappearance_threshold_days=180,
        min_misses_for_removal=3,
        significance_default="high",
    ),
    ChangePolicy(
        predicate_pattern="company.employee_range",
        disappearance_threshold_days=180,
        min_misses_for_removal=3,
        significance_default="high",
    ),
    ChangePolicy(
        predicate_pattern="company.technology",
        disappearance_threshold_days=90,
        min_misses_for_removal=3,
        reappearance_enabled=True,
        significance_default="medium",
    ),
    ChangePolicy(
        predicate_pattern="company.location",
        disappearance_threshold_days=180,
        min_misses_for_removal=2,
        significance_default="high",
    ),
    ChangePolicy(
        predicate_pattern="company.product",
        disappearance_threshold_days=120,
        min_misses_for_removal=3,
        significance_default="medium",
    ),
    ChangePolicy(
        predicate_pattern="company.service",
        disappearance_threshold_days=120,
        min_misses_for_removal=3,
        significance_default="medium",
    ),
    ChangePolicy(
        predicate_pattern="person.title",
        disappearance_threshold_days=60,
        min_misses_for_removal=2,
        significance_default="medium",
    ),
]


class PolicyRegistry:
    """Loads and matches change detection policies per predicate."""

    def __init__(self, policies: Optional[List[ChangePolicy]] = None):
        self._policies = policies or list(DEFAULT_POLICIES)

    def get_policy(self, predicate: str) -> ChangePolicy:
        """Find the best-matching policy for a given predicate."""
        # Exact match first
        for p in self._policies:
            if p.predicate_pattern == predicate:
                return p

        # Prefix match (e.g. "company.*" matches "company.technology")
        for p in self._policies:
            if p.predicate_pattern.endswith("*"):
                prefix = p.predicate_pattern[:-1]
                if predicate.startswith(prefix):
                    return p

        # Default policy
        return ChangePolicy(
            predicate_pattern=predicate,
            disappearance_threshold_days=90,
            min_misses_for_removal=2,
            significance_default="medium",
        )

    def add_policy(self, policy: ChangePolicy) -> None:
        self._policies.append(policy)
