"""
GrowX Competitor Graph Explainer.
Generates machine-readable ReasonCodes and human-readable explanation narratives.
"""

from typing import List, Optional
from growx_crawl.intelligence.competitors.models import (
    CompetitiveProfile,
    CompetitorEvidenceEntity,
    EvidenceType,
    ReasonCode,
    RelationshipType,
)


class CompetitorExplainer:
    """Produces explainable rationales for competitive edges."""

    @staticmethod
    def generate_reasons(
        market_overlap: float,
        offering_overlap: float,
        customer_overlap: float,
        geography_overlap: float,
        evidence_list: Optional[List[CompetitorEvidenceEntity]] = None,
        blocking_conflict: Optional[str] = None,
    ) -> List[str]:
        """Generates standardized machine-readable ReasonCodes."""
        reasons: List[str] = []

        if blocking_conflict:
            conf = blocking_conflict.lower()
            if conf in ("parent", "subsidiary", "brand_owner"):
                reasons.append(ReasonCode.PARENT_RELATIONSHIP_CONFLICT.value)
            elif conf in ("customer",):
                reasons.append(ReasonCode.CUSTOMER_RELATIONSHIP_CONFLICT.value)
            elif conf in ("supplier", "partner"):
                reasons.append(ReasonCode.SUPPLIER_RELATIONSHIP_CONFLICT.value)
            return reasons

        if market_overlap >= 0.40:
            reasons.append(ReasonCode.SAME_MARKET.value)

        if customer_overlap >= 0.40:
            reasons.append(ReasonCode.SAME_CUSTOMER_SEGMENT.value)

        if offering_overlap >= 0.35:
            reasons.append(ReasonCode.OFFERING_OVERLAP.value)

        if geography_overlap >= 0.50:
            reasons.append(ReasonCode.GEOGRAPHY_OVERLAP.value)
        elif geography_overlap < 0.10:
            reasons.append(ReasonCode.DIFFERENT_GEOGRAPHY_NO_REMOTE.value)

        if evidence_list:
            for ev in evidence_list:
                if ev.evidence_type in (
                    EvidenceType.COMPARISON_PAGE.value,
                    EvidenceType.ALTERNATIVE_PAGE.value,
                    EvidenceType.EXPLICIT_COMPETITOR_MENTION.value,
                ):
                    if ReasonCode.EXPLICIT_COMPARISON.value not in reasons:
                        reasons.append(ReasonCode.EXPLICIT_COMPARISON.value)

        return reasons

    @staticmethod
    def generate_narrative(
        company_a_name: str,
        company_b_name: str,
        relationship_type: str,
        reasons: List[str],
        market_overlap: float,
        offering_overlap: float,
    ) -> str:
        """Constructs a concise narrative summary explaining the relationship."""
        rel_label = relationship_type.replace("_", " ").title()
        details = []

        if ReasonCode.PARENT_RELATIONSHIP_CONFLICT.value in reasons:
            return f"{company_a_name} and {company_b_name} share a corporate parent/subsidiary structure (non-competitive)."
        if ReasonCode.CUSTOMER_RELATIONSHIP_CONFLICT.value in reasons:
            return f"{company_a_name} and {company_b_name} maintain a customer relationship rather than direct competition."
        if ReasonCode.SUPPLIER_RELATIONSHIP_CONFLICT.value in reasons:
            return f"{company_a_name} and {company_b_name} maintain a vendor/partner relationship."

        if ReasonCode.OFFERING_OVERLAP.value in reasons:
            details.append(f"overlapping capabilities/products ({int(offering_overlap * 100)}% match)")
        if ReasonCode.SAME_CUSTOMER_SEGMENT.value in reasons:
            details.append("shared target buyer personas")
        if ReasonCode.SAME_MARKET.value in reasons:
            details.append("shared industry market")
        if ReasonCode.EXPLICIT_COMPARISON.value in reasons:
            details.append("explicit third-party comparison/alternative evidence")

        narrative = f"{company_a_name} and {company_b_name} identified as {rel_label} competitors"
        if details:
            narrative += f" due to {', '.join(details)}."
        else:
            narrative += "."
        return narrative
