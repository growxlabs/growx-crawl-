"""
GrowX Employment Verification.
Validates the employment association between a person and a company.
"""

from typing import Any, Dict
from growx_crawl.normalization.domain import get_registrable_domain
from growx_crawl.shared.ids import generate_id
from growx_crawl.verification.models import VerificationResultEntity, VerificationStatus


async def verify_employment(
    person_id: str,
    company_id: str,
    person_email: str,
    company_domain: str,
) -> VerificationResultEntity:
    """Verifies person employment by verifying that corporate email domain matches company domain."""
    confidence = 0.5
    checks = []

    if person_email and "@" in person_email and company_domain:
        email_domain = person_email.split("@")[1].lower()
        reg_email_domain = get_registrable_domain(email_domain)
        reg_company_domain = get_registrable_domain(company_domain)

        if reg_email_domain == reg_company_domain:
            confidence = 0.95
            checks.append("email_domain_matches_company_domain")
        else:
            checks.append("mismatched_domain")

    status = VerificationStatus.VERIFIED if confidence >= 0.8 else VerificationStatus.UNVERIFIED
    return VerificationResultEntity(
        id=generate_id("ver_"),
        entity_type="employment",
        entity_id=f"{person_id}:{company_id}",
        status=status,
        confidence=confidence,
        details_json={"checks": checks, "email": person_email, "company_domain": company_domain},
    )
