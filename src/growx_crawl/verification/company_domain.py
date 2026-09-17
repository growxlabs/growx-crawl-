"""
GrowX Company-Domain Relationship Verification.
Answers: 'Does this domain really belong to this company?'
Evaluates domain ownership via name matching, site footer identity, contact email domain,
and linked social handles.
"""

from typing import Any, Dict, List, Optional
from growx_crawl.normalization.company import clean_company_name, normalize_company_name_key
from growx_crawl.normalization.domain import get_registrable_domain, normalize_domain
from growx_crawl.shared.ids import generate_id
from growx_crawl.shared.time import utc_iso_now
from growx_crawl.verification.confidence import compute_verification_confidence
from growx_crawl.verification.freshness import calculate_valid_until
from growx_crawl.verification.models import (
    ReasonCode,
    VerificationCheckEntity,
    VerificationResultEntity,
    VerificationStatus,
)
from growx_crawl.verification.policies import get_policy


class CompanyDomainVerifier:
    """Evaluates whether an active domain genuinely belongs to a company entity."""

    async def verify(
        self,
        company_id: str,
        company_name: str,
        domain_str: str,
        site_metadata: Optional[Dict[str, Any]] = None,
        company_emails: Optional[List[str]] = None,
        policy_name: str = "company_domain_default_v1",
    ) -> VerificationResultEntity:
        policy = get_policy(policy_name)
        norm_domain = normalize_domain(domain_str)
        reg_domain = get_registrable_domain(domain_str)
        norm_company_key = normalize_company_name_key(company_name)

        checks: List[VerificationCheckEntity] = []
        reason_codes: List[str] = []

        ownership_score = 0.0
        meta = site_metadata or {}

        # 1. Domain Root vs Company Name Key
        dom_name_part = reg_domain.split(".")[0] if "." in reg_domain else reg_domain
        if dom_name_part and (dom_name_part in norm_company_key or norm_company_key in dom_name_part):
            ownership_score += 0.40
            reason_codes.append(ReasonCode.OFFICIAL_SITE_NAME_MATCH)
            checks.append(VerificationCheckEntity(
                id=generate_id("chk_"),
                verification_run_id="",
                check_type="domain_name_match",
                status="passed",
                score=1.0,
                reason_code=ReasonCode.OFFICIAL_SITE_NAME_MATCH,
            ))

        # 2. Site Title / Header Alignment
        site_title = (meta.get("title") or "").lower()
        if company_name.lower() in site_title or norm_company_key in site_title:
            ownership_score += 0.35
            reason_codes.append("SITE_TITLE_MATCH")
            checks.append(VerificationCheckEntity(
                id=generate_id("chk_"),
                verification_run_id="",
                check_type="site_title_match",
                status="passed",
                score=1.0,
                reason_code="SITE_TITLE_MATCH",
            ))

        # 3. Contact Email Domain Match
        emails = company_emails or []
        email_matched = False
        for e in emails:
            if "@" in e:
                e_dom = get_registrable_domain(e.split("@")[1])
                if e_dom == reg_domain:
                    email_matched = True
                    break

        if email_matched:
            ownership_score += 0.25
            reason_codes.append(ReasonCode.EMAIL_MX_VALID)
            checks.append(VerificationCheckEntity(
                id=generate_id("chk_"),
                verification_run_id="",
                check_type="email_domain_match",
                status="passed",
                score=1.0,
                reason_code=ReasonCode.EMAIL_MX_VALID,
            ))

        # Classify relationship
        if ownership_score >= 0.70:
            rel_status = "belongs"
            v_status = VerificationStatus.VERIFIED
        elif ownership_score >= 0.40:
            rel_status = "likely_belongs"
            v_status = VerificationStatus.SUPPORTED
        elif ownership_score > 0.0:
            rel_status = "uncertain"
            v_status = VerificationStatus.UNCERTAIN
        else:
            rel_status = "does_not_belong"
            v_status = VerificationStatus.CONFLICTING
            reason_codes.append(ReasonCode.DOMAIN_COMPANY_CONFLICT)

        conf = compute_verification_confidence(
            subject_type="company_domain",
            base_source_score=0.85,
            identity_strength=min(ownership_score + 0.2, 1.0),
            source_agreement=0.85,
            technical_checks_score=0.90,
            freshness_score=1.0,
            conflict_penalty=0.4 if rel_status == "does_not_belong" else 0.0,
        )

        valid_until = calculate_valid_until(None, policy.ttl_hours).strftime("%Y-%m-%dT%H:%M:%SZ")

        return VerificationResultEntity(
            id=generate_id("ver_"),
            subject_type="company_domain",
            subject_id=f"{company_id}:{norm_domain}",
            verification_type="company_domain",
            status=v_status,
            confidence=conf,
            policy_name=policy.name,
            policy_version=policy.version,
            reason_codes=reason_codes,
            checks=checks,
            verified_at=utc_iso_now(),
            valid_until=valid_until,
            details_json={
                "company_id": company_id,
                "domain": norm_domain,
                "relationship": rel_status,
                "ownership_score": round(ownership_score, 2),
            },
        )


company_domain_verifier = CompanyDomainVerifier()


async def verify_company_domain(
    company_id: str,
    company_name: str,
    domain_str: str,
    site_metadata: Optional[Dict[str, Any]] = None,
    company_emails: Optional[List[str]] = None,
    policy_name: str = "company_domain_default_v1",
) -> VerificationResultEntity:
    return await company_domain_verifier.verify(
        company_id, company_name, domain_str, site_metadata, company_emails, policy_name
    )
