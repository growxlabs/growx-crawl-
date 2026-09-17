"""
GrowX Competitor Verification Engine.
Applies blocking rules (parent/subsidiary, supplier/customer) and verification gates.
"""

from typing import List, Optional, Tuple
from growx_crawl.intelligence.competitors.explain import CompetitorExplainer
from growx_crawl.intelligence.competitors.models import (
    CompetitiveProfile,
    CompetitorEvidenceEntity,
    ReasonCode,
    RelationshipStatus,
    RelationshipType,
)
from growx_crawl.intelligence.competitors.policies import (
    CompetitorVerificationPolicy,
    DEFAULT_COMPETITOR_POLICY,
)


class CompetitorVerifier:
    """Verifies competitive edges against corporate relationships and evidence gates."""

    def __init__(self, policy: CompetitorVerificationPolicy = DEFAULT_COMPETITOR_POLICY):
        self.policy = policy
        self.explainer = CompetitorExplainer()

    def verify(
        self,
        profile_a: CompetitiveProfile,
        profile_b: CompetitiveProfile,
        strength: float,
        confidence: float,
        market_overlap: float,
        offering_overlap: float,
        customer_overlap: float,
        geography_overlap: float,
        evidence_list: List[CompetitorEvidenceEntity],
        corporate_relationship: Optional[str] = None,
    ) -> Tuple[str, List[str]]:
        """
        Determines the RelationshipStatus and reason codes for a competitor candidate.
        Returns (status, reasons).
        """
        # 1. Blocking Condition: Parent/Subsidiary/Supplier/Customer Guard (Sections 27-29)
        if corporate_relationship:
            corp_norm = corporate_relationship.strip().lower()
            if corp_norm in self.policy.blocking_relationship_types:
                reasons = self.explainer.generate_reasons(
                    market_overlap=market_overlap,
                    offering_overlap=offering_overlap,
                    customer_overlap=customer_overlap,
                    geography_overlap=geography_overlap,
                    blocking_conflict=corp_norm,
                )
                return RelationshipStatus.REJECTED.value, reasons

        # 2. Check geography blocking (completely disjoint with no remote/global overlap)
        if geography_overlap == 0.0 and market_overlap < 0.20:
            reasons = [ReasonCode.DIFFERENT_GEOGRAPHY_NO_REMOTE.value]
            return RelationshipStatus.REJECTED.value, reasons

        # 3. Generate normal positive reasons
        reasons = self.explainer.generate_reasons(
            market_overlap=market_overlap,
            offering_overlap=offering_overlap,
            customer_overlap=customer_overlap,
            geography_overlap=geography_overlap,
            evidence_list=evidence_list,
        )

        # 4. Status determination
        # Verified: high confidence, sufficient strength, and evidence backing
        if (
            confidence >= self.policy.min_confidence_verified
            and strength >= self.policy.min_strength_adjacent
            and len(evidence_list) >= self.policy.min_evidence_count_verified
        ):
            return RelationshipStatus.VERIFIED.value, reasons

        # Supported: moderate confidence and strength
        if (
            confidence >= self.policy.min_confidence_supported
            and strength >= self.policy.min_strength_substitute
        ):
            return RelationshipStatus.SUPPORTED.value, reasons

        # Uncertain: some strength but weak confidence
        if strength >= 0.25:
            return RelationshipStatus.UNCERTAIN.value, reasons

        # Weak overlap remains candidate or rejected
        if strength < 0.15:
            return RelationshipStatus.REJECTED.value, reasons

        return RelationshipStatus.CANDIDATE.value, reasons
