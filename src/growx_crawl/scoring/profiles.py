"""
GrowX Ranking Profiles.
Defines versioned weighting profiles, component distributions, and threshold policies.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from growx_crawl.scoring.models import RankingProfileEntity


class RankingProfileConfig(BaseModel):
    """Configuration governing component weights, thresholds, and penalty rates."""
    name: str = "Default Ranking Profile"
    version: int = 1
    enabled: bool = True

    # Component weights (sum to 1.0)
    account_weight: float = 0.35
    person_weight: float = 0.25
    signal_weight: float = 0.15
    timing_weight: float = 0.15
    contactability_weight: float = 0.10

    # Status classification thresholds
    priority_threshold: float = 0.80
    strong_threshold: float = 0.65
    possible_threshold: float = 0.50

    # Workflow triggers
    reverify_staleness_days: int = 180
    min_confidence_reverify: float = 0.60
    min_data_research_more: float = 0.45

    # Signal & timing curves
    signal_decay_halflife_days: int = 45
    signal_max_age_days: int = 180
    multi_signal_cap: float = 1.0

    # Penalties
    role_mailbox_penalty: float = 0.20
    catch_all_penalty: float = 0.10
    missing_email_penalty: float = 0.15
    stale_employment_penalty: float = 0.25
    stale_company_penalty: float = 0.15


# Pre-seeded Built-In Profiles
BUILTIN_PROFILES: Dict[str, RankingProfileConfig] = {
    "default_v1": RankingProfileConfig(
        name="Default Balanced Profile",
        version=1,
        account_weight=0.35,
        person_weight=0.25,
        signal_weight=0.15,
        timing_weight=0.15,
        contactability_weight=0.10,
        priority_threshold=0.80,
        strong_threshold=0.65,
        possible_threshold=0.50,
    ),
    "high_intent_v1": RankingProfileConfig(
        name="High Intent Profile",
        version=1,
        account_weight=0.25,
        person_weight=0.20,
        signal_weight=0.30,
        timing_weight=0.20,
        contactability_weight=0.05,
        priority_threshold=0.78,
        strong_threshold=0.65,
        possible_threshold=0.50,
    ),
    "account_first_v1": RankingProfileConfig(
        name="Account-First Profile",
        version=1,
        account_weight=0.50,
        person_weight=0.20,
        signal_weight=0.15,
        timing_weight=0.10,
        contactability_weight=0.05,
        priority_threshold=0.82,
        strong_threshold=0.68,
        possible_threshold=0.50,
    ),
    "person_first_v1": RankingProfileConfig(
        name="Person-First Profile",
        version=1,
        account_weight=0.25,
        person_weight=0.45,
        signal_weight=0.10,
        timing_weight=0.10,
        contactability_weight=0.10,
        priority_threshold=0.80,
        strong_threshold=0.65,
        possible_threshold=0.50,
    ),
}


class RankingProfileRegistry:
    """Registry maintaining active and custom ranking profiles."""

    def __init__(self):
        self._profiles: Dict[str, RankingProfileConfig] = dict(BUILTIN_PROFILES)

    def get_profile(self, profile_id_or_name: str) -> RankingProfileConfig:
        clean = profile_id_or_name.strip()
        if clean in self._profiles:
            return self._profiles[clean]
        # Default fallback
        return self._profiles["default_v1"]

    def register_profile(self, name: str, config: RankingProfileConfig) -> None:
        self._profiles[name] = config

    def list_profiles(self) -> Dict[str, RankingProfileConfig]:
        return dict(self._profiles)


profile_registry = RankingProfileRegistry()
