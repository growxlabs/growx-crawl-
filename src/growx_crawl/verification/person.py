"""
GrowX Person Verification.
Validates individual identity and professional profile linkages.
"""

from typing import Any, Dict
from growx_crawl.shared.ids import generate_id
from growx_crawl.verification.models import VerificationResultEntity, VerificationStatus


async def verify_person(person_id: str, person_data: Dict[str, Any]) -> VerificationResultEntity:
    """Verifies that a person record meets standard identity criteria."""
    name = person_data.get("name")
    email = person_data.get("email")
    linkedin = person_data.get("linkedin_url")

    if not name:
        return VerificationResultEntity(
            id=generate_id("ver_"),
            entity_type="person",
            entity_id=person_id,
            status=VerificationStatus.FAILED,
            confidence=0.0,
            details_json={"error": "Missing person name"},
        )

    score = 0.5
    checks = ["name_present"]
    if email:
        score += 0.3
        checks.append("email_present")
    if linkedin:
        score += 0.2
        checks.append("linkedin_present")

    confidence = min(score, 1.0)
    status = VerificationStatus.VERIFIED if confidence >= 0.8 else VerificationStatus.UNVERIFIED
    return VerificationResultEntity(
        id=generate_id("ver_"),
        entity_type="person",
        entity_id=person_id,
        status=status,
        confidence=confidence,
        details_json={"checks_passed": checks},
    )
