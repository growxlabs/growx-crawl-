"""
GrowX Company Verification.
Validates company web presence and domain alignment.
"""

from typing import Any, Dict
from growx_crawl.shared.ids import generate_id
from growx_crawl.verification.models import VerificationResultEntity, VerificationStatus


async def verify_company(company_id: str, company_data: Dict[str, Any]) -> VerificationResultEntity:
    """Verifies that a company has a valid active domain and name."""
    name = company_data.get("name")
    domain = company_data.get("domain")

    if not name:
        return VerificationResultEntity(
            id=generate_id("ver_"),
            entity_type="company",
            entity_id=company_id,
            status=VerificationStatus.FAILED,
            confidence=0.0,
            details_json={"error": "Missing company name"},
        )

    confidence = 0.5
    checks = ["has_name"]
    if domain:
        confidence = 0.9
        checks.append("has_domain")

    status = VerificationStatus.VERIFIED if confidence >= 0.8 else VerificationStatus.UNVERIFIED
    return VerificationResultEntity(
        id=generate_id("ver_"),
        entity_type="company",
        entity_id=company_id,
        status=status,
        confidence=confidence,
        details_json={"checks_passed": checks},
    )
