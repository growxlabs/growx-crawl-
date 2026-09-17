"""
GrowX Employment Verification.
Answers: 'Is this person currently employed by this company?'
Evaluates corporate email domain alignment, official team page listings,
and time-decay freshness.
"""

from typing import Any, Dict, List, Optional
from growx_crawl.normalization.domain import get_registrable_domain
from growx_crawl.shared.ids import generate_id
from growx_crawl.shared.time import parse_iso, utc_iso_now, utc_now
from growx_crawl.verification.confidence import compute_verification_confidence
from growx_crawl.verification.freshness import calculate_valid_until
from growx_crawl.verification.models import (
    EmploymentState,
    ReasonCode,
    VerificationCheckEntity,
    VerificationResultEntity,
    VerificationStatus,
)
from growx_crawl.verification.policies import get_policy


class EmploymentVerifier:
    """Verifies person-company employment linkages and time-sensitive recency."""

    async def verify(
        self,
        person_id: str,
        company_id: str,
        person_email: str = "",
        company_domain: str = "",
        observed_at_iso: Optional[str] = None,
        on_team_page: bool = False,
        policy_name: str = "employment_default_v1",
    ) -> VerificationResultEntity:
        policy = get_policy(policy_name)
        checks: List[VerificationCheckEntity] = []
        reason_codes: List[str] = []

        # 1. Freshness evaluation (days since observed)
        age_days = 30
        if observed_at_iso:
            obs_dt = parse_iso(observed_at_iso)
            if obs_dt:
                age_days = max(int((utc_now() - obs_dt).total_seconds() / 86400), 0)

        is_stale = age_days > 365
        is_aging = 180 < age_days <= 365

        # 2. Corporate Email Domain Match
        email_match = False
        if person_email and "@" in person_email and company_domain:
            e_dom = get_registrable_domain(person_email.split("@")[1])
            c_dom = get_registrable_domain(company_domain)
            if e_dom and c_dom and e_dom == c_dom:
                email_match = True
                checks.append(VerificationCheckEntity(
                    id=generate_id("chk_"),
                    verification_run_id="",
                    check_type="email_domain_match",
                    status="passed",
                    score=1.0,
                    reason_code="WORK_EMAIL_DOMAIN_MATCH",
                ))
                reason_codes.append("WORK_EMAIL_DOMAIN_MATCH")
            else:
                checks.append(VerificationCheckEntity(
                    id=generate_id("chk_"),
                    verification_run_id="",
                    check_type="email_domain_match",
                    status="warning",
                    score=0.2,
                    reason_code=ReasonCode.EMAIL_DOMAIN_MISMATCH,
                ))
                reason_codes.append(ReasonCode.EMAIL_DOMAIN_MISMATCH)

        # 3. Team Page Evidence
        if on_team_page:
            checks.append(VerificationCheckEntity(
                id=generate_id("chk_"),
                verification_run_id="",
                check_type="team_page_presence",
                status="passed",
                score=1.0,
                reason_code=ReasonCode.EMPLOYMENT_CONFIRMED,
            ))
            reason_codes.append(ReasonCode.EMPLOYMENT_CONFIRMED)

        # 4. State & Confidence Mapping
        if is_stale:
            state = EmploymentState.STALE
            v_status = VerificationStatus.STALE
            reason_codes.append(ReasonCode.EMPLOYMENT_STALE)
            conf = 0.40
        elif (email_match or on_team_page) and not is_aging:
            state = EmploymentState.CURRENT_VERIFIED
            v_status = VerificationStatus.VERIFIED
            conf = 0.95 if (email_match and on_team_page) else 0.88
        elif email_match or on_team_page:
            state = EmploymentState.CURRENT_SUPPORTED
            v_status = VerificationStatus.SUPPORTED
            conf = 0.75
        elif person_email:
            state = EmploymentState.UNCERTAIN
            v_status = VerificationStatus.UNCERTAIN
            conf = 0.50
        else:
            state = EmploymentState.UNCERTAIN
            v_status = VerificationStatus.UNVERIFIED
            conf = 0.30

        technical_score = 1.0 if email_match else 0.4
        freshness_score = 0.2 if is_stale else (0.6 if is_aging else 1.0)

        final_conf = compute_verification_confidence(
            subject_type="employment",
            base_source_score=0.85,
            identity_strength=0.90 if (email_match or on_team_page) else 0.50,
            source_agreement=0.85,
            technical_checks_score=technical_score,
            freshness_score=freshness_score,
            staleness_penalty=0.4 if is_stale else (0.15 if is_aging else 0.0),
        )

        valid_until = calculate_valid_until(None, policy.ttl_hours).strftime("%Y-%m-%dT%H:%M:%SZ")

        return VerificationResultEntity(
            id=generate_id("ver_"),
            subject_type="employment",
            subject_id=f"{person_id}:{company_id}",
            verification_type="employment",
            status=v_status,
            confidence=final_conf,
            policy_name=policy.name,
            policy_version=policy.version,
            reason_codes=reason_codes,
            checks=checks,
            verified_at=utc_iso_now(),
            valid_until=valid_until,
            details_json={
                "person_id": person_id,
                "company_id": company_id,
                "employment_state": state.value,
                "email_matched": email_match,
                "on_team_page": on_team_page,
                "age_days": age_days,
            },
        )


employment_verifier = EmploymentVerifier()


async def verify_employment(
    person_id: str,
    company_id: str,
    person_email: str = "",
    company_domain: str = "",
    observed_at_iso: Optional[str] = None,
    on_team_page: bool = False,
    policy_name: str = "employment_default_v1",
) -> VerificationResultEntity:
    return await employment_verifier.verify(
        person_id, company_id, person_email, company_domain, observed_at_iso, on_team_page, policy_name
    )
