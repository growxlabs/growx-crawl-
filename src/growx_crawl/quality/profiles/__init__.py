"""
GrowX Quality Profiles Package.
"""

from typing import Any, Dict
from growx_crawl.quality.profiles.canonical import CANONICAL_INGESTION_PROFILES
from growx_crawl.quality.profiles.outreach import OUTREACH_PROFILES
from growx_crawl.quality.profiles.personalization import PERSONALIZATION_PROFILES
from growx_crawl.quality.profiles.prospect import PROSPECT_PROFILES

ALL_PROFILES: Dict[str, Dict[str, Any]] = {
    **CANONICAL_INGESTION_PROFILES,
    **PROSPECT_PROFILES,
    **PERSONALIZATION_PROFILES,
    **OUTREACH_PROFILES,
}


def get_quality_profile(name: str) -> Dict[str, Any]:
    """Returns profile configuration by name with fallback defaults."""
    if name in ALL_PROFILES:
        return ALL_PROFILES[name]
    return {
        "required_fields": [],
        "recommended_fields": [],
        "min_completeness_ratio": 0.50,
    }


__all__ = [
    "CANONICAL_INGESTION_PROFILES",
    "PROSPECT_PROFILES",
    "PERSONALIZATION_PROFILES",
    "OUTREACH_PROFILES",
    "ALL_PROFILES",
    "get_quality_profile",
]
