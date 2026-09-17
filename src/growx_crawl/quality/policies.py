"""
GrowX Quality Policy Registry.
Maintains versioned, declarative quality gate policies across all five gating tiers.
"""

from typing import Dict, Optional
from growx_crawl.quality.models import GateType, QualityPolicy

STANDARD_QUALITY_POLICIES: Dict[str, QualityPolicy] = {
    # Gate 1: Canonical Ingestion
    "canonical_ingestion_v1": QualityPolicy(
        id="pol_ingestion_v1",
        name="canonical_ingestion_v1",
        gate_type=GateType.CANONICAL_INGESTION,
        profile="company_minimal",
        version="v1",
        min_score=0.50,
        rules_config={"allow_quarantine": True, "strict_types": True},
        ttl_hours=720,  # 30 days
    ),
    # Gate 2: Intelligence Trust
    "intelligence_trust_v1": QualityPolicy(
        id="pol_intel_trust_v1",
        name="intelligence_trust_v1",
        gate_type=GateType.INTELLIGENCE_TRUST,
        profile="fact_minimal",
        version="v1",
        min_score=0.70,
        rules_config={"min_evidence_count": 1, "max_age_days": 180},
        ttl_hours=168,  # 7 days
    ),
    # Gate 3: Prospect Eligibility
    "prospect_eligibility_v1": QualityPolicy(
        id="pol_prospect_v1",
        name="prospect_eligibility_v1",
        gate_type=GateType.PROSPECT_ELIGIBILITY,
        profile="prospect_eligible",
        version="v1",
        min_score=0.75,
        rules_config={"require_verified_company": True, "check_duplicate": True},
        ttl_hours=168,
    ),
    # Gate 4: Personalization Eligibility
    "personalization_v1": QualityPolicy(
        id="pol_personalization_v1",
        name="personalization_v1",
        gate_type=GateType.PERSONALIZATION_ELIGIBILITY,
        profile="personalization_ready",
        version="v1",
        min_score=0.75,
        rules_config={"require_evidence_hook": True, "exclude_stale_facts": True},
        ttl_hours=72,  # 3 days
    ),
    # Gate 5: Outreach Eligibility
    "outreach_v1": QualityPolicy(
        id="pol_outreach_v1",
        name="outreach_v1",
        gate_type=GateType.OUTREACH_ELIGIBILITY,
        profile="outreach_eligible",
        version="v1",
        min_score=0.80,
        rules_config={
            "suppression_check": True,
            "forbid_role_addresses": True,
            "forbid_catchall": True,
            "max_email_age_hours": 168,
        },
        ttl_hours=72,
    ),
}

ALL_POLICIES = STANDARD_QUALITY_POLICIES


def get_quality_policy(gate_type: GateType, policy_name: Optional[str] = None) -> QualityPolicy:
    """Retrieves policy for a specific gate type with fallback default."""
    if policy_name and policy_name in STANDARD_QUALITY_POLICIES:
        return STANDARD_QUALITY_POLICIES[policy_name]

    # Match by gate type
    for p in STANDARD_QUALITY_POLICIES.values():
        if p.gate_type == gate_type:
            return p

    # Fallback generic policy
    return QualityPolicy(
        id=f"pol_{gate_type.value}_default",
        name=f"{gate_type.value}_default",
        gate_type=gate_type,
        profile="default",
        version="v1",
        min_score=0.70,
    )
