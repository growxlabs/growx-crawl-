"""
GrowX Company Verification.
Answers: 'Does this company appear to exist as a real operating entity?'
Evaluates official domain reachability, business name validity, website content support,
and contact presence.
"""

from typing import Any, Dict, List, Optional
from growx_crawl.shared.ids import generate_id
from growx_crawl.shared.time import utc_iso_now
from growx_crawl.verification.confidence import compute_verification_confidence
from growx_crawl.verification.domain import verify_domain
from growx_crawl.verification.freshness import calculate_valid_until
from growx_crawl.verification.models import (
    ReasonCode,
    VerificationCheckEntity,
    VerificationResultEntity,
    VerificationStatus,
)
from growx_crawl.verification.policies import get_policy


class CompanyVerifier:
    """Verifies company entity authenticity, web presence, and business reachability."""

    async def verify(
        self,
        company_id: str,
        company_data: Dict[str, Any],
        policy_name: str = "company_default_v1",
    ) -> VerificationResultEntity:
        policy = get_policy(policy_name)
        name = (company_data.get("name") or "").strip()
        domain = (company_data.get("domain") or "").strip()

        checks: List[VerificationCheckEntity] = []
        reason_codes: List[str] = []

        if not name:
            return VerificationResultEntity(
                id=generate_id("ver_"),
                subject_type="company",
                subject_id=company_id,
                verification_type="company",
                status=VerificationStatus.INVALID,
                confidence=0.0,
                policy_name=policy.name,
                policy_version=policy.version,
                reason_codes=["COMPANY_MISSING_NAME"],
                details_json={"error": "Company has no canonical name"},
            )

        checks.append(VerificationCheckEntity(
            id=generate_id("chk_"),
            verification_run_id="",
            check_type="name_exists",
            status="passed",
            score=1.0,
            reason_code="CANONICAL_NAME_EXISTS",
        ))
        reason_codes.append("CANONICAL_NAME_EXISTS")

        domain_reachable = False
        if domain:
            dom_res = await verify_domain(domain)
            if dom_res.status in (VerificationStatus.VERIFIED, VerificationStatus.SUPPORTED):
                domain_reachable = True
                checks.append(VerificationCheckEntity(
                    id=generate_id("chk_"),
                    verification_run_id="",
                    check_type="domain_active",
                    status="passed",
                    score=dom_res.confidence,
                    reason_code=ReasonCode.OFFICIAL_DOMAIN_ACTIVE,
                ))
                reason_codes.append(ReasonCode.OFFICIAL_DOMAIN_ACTIVE)
            else:
                checks.append(VerificationCheckEntity(
                    id=generate_id("chk_"),
                    verification_run_id="",
                    check_type="domain_active",
                    status="warning",
                    score=0.2,
                    reason_code=ReasonCode.DOMAIN_UNREACHABLE,
                ))
                reason_codes.append(ReasonCode.DOMAIN_UNREACHABLE)

        # Contactability & Description presence
        has_contacts = bool(company_data.get("emails") or company_data.get("phones"))
        has_description = bool(company_data.get("description"))

        if has_contacts:
            checks.append(VerificationCheckEntity(
                id=generate_id("chk_"),
                verification_run_id="",
                check_type="contact_presence",
                status="passed",
                score=1.0,
                reason_code="CONTACT_INFO_PRESENT",
            ))
            reason_codes.append("CONTACT_INFO_PRESENT")

        if has_description:
            checks.append(VerificationCheckEntity(
                id=generate_id("chk_"),
                verification_run_id="",
                check_type="description_presence",
                status="passed",
                score=1.0,
                reason_code="DESCRIPTION_PRESENT",
            ))

        # Scoring
        base_source = 0.90 if domain_reachable else 0.50
        identity_strength = 0.95 if (name and domain) else 0.60
        tech_score = 0.95 if domain_reachable else 0.30

        conf = compute_verification_confidence(
            subject_type="company",
            base_source_score=base_source,
            identity_strength=identity_strength,
            source_agreement=0.85,
            technical_checks_score=tech_score,
            freshness_score=1.0,
            conflict_penalty=0.0,
        )

        if domain_reachable and conf >= policy.min_confidence:
            v_status = VerificationStatus.VERIFIED
        elif domain_reachable or (has_contacts and has_description):
            v_status = VerificationStatus.SUPPORTED
        elif domain:
            v_status = VerificationStatus.UNCERTAIN
        else:
            v_status = VerificationStatus.UNVERIFIED

        valid_until = calculate_valid_until(None, policy.ttl_hours).strftime("%Y-%m-%dT%H:%M:%SZ")

        return VerificationResultEntity(
            id=generate_id("ver_"),
            subject_type="company",
            subject_id=company_id,
            verification_type="company",
            status=v_status,
            confidence=conf,
            policy_name=policy.name,
            policy_version=policy.version,
            reason_codes=reason_codes,
            checks=checks,
            verified_at=utc_iso_now(),
            valid_until=valid_until,
            details_json={
                "company_name": name,
                "domain": domain,
                "domain_reachable": domain_reachable,
                "has_contacts": has_contacts,
                "has_description": has_description,
            },
        )


company_verifier = CompanyVerifier()


async def verify_company(
    company_id: str,
    company_data: Dict[str, Any],
    policy_name: str = "company_default_v1",
) -> VerificationResultEntity:
    return await company_verifier.verify(company_id, company_data, policy_name)
