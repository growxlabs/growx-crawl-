"""
GrowX Fact Verification.
Validates individual canonical facts against evidence provenance and confidence criteria.
"""

from typing import Any, Dict
from growx_crawl.shared.ids import generate_id
from growx_crawl.verification.models import VerificationResultEntity, VerificationStatus


async def verify_fact(
    fact_id: str,
    fact_data: Dict[str, Any],
) -> VerificationResultEntity:
    """Verifies that a fact has valid evidence and confidence exceeding threshold."""
    confidence = float(fact_data.get("confidence") or 0.0)
    has_evidence = bool(fact_data.get("evidence_count", 0) > 0 or fact_data.get("has_evidence"))

    status = VerificationStatus.VERIFIED if (confidence >= 0.70 and has_evidence) else VerificationStatus.UNVERIFIED
    return VerificationResultEntity(
        id=generate_id("ver_"),
        entity_type="fact",
        entity_id=fact_id,
        status=status,
        confidence=confidence,
        details_json={"confidence": confidence, "has_evidence": has_evidence},
    )
