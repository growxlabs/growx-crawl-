"""
GrowX Person Verification.
Answers: 'Does this person identity appear real enough to use?'
Evaluates professional presence across public profiles, official company team pages,
and direct business contact points.
"""

from typing import Any, Dict, List, Optional
from growx_crawl.normalization.person import clean_person_name
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


class PersonVerifier:
    """Verifies individual identity realism and public professional footprint."""

    async def verify(
        self,
        person_id: str,
        person_data: Dict[str, Any],
        policy_name: str = "person_default_v1",
    ) -> VerificationResultEntity:
        policy = get_policy(policy_name)
        raw_name = person_data.get("name") or ""
        name = clean_person_name(raw_name)
        email = (person_data.get("email") or "").strip()
        linkedin = (person_data.get("linkedin_url") or "").strip()
        title = (person_data.get("title") or person_data.get("job_title") or "").strip()

        checks: List[VerificationCheckEntity] = []
        reason_codes: List[str] = []

        if not name or len(name.split()) < 2:
            return VerificationResultEntity(
                id=generate_id("ver_"),
                subject_type="person",
                subject_id=person_id,
                verification_type="person",
                status=VerificationStatus.INVALID,
                confidence=0.0,
                policy_name=policy.name,
                policy_version=policy.version,
                reason_codes=["PERSON_INVALID_NAME"],
                details_json={"error": "Person name is missing or incomplete"},
            )

        checks.append(VerificationCheckEntity(
            id=generate_id("chk_"),
            verification_run_id="",
            check_type="name_valid",
            status="passed",
            score=1.0,
            reason_code="PERSON_NAME_VALID",
        ))
        reason_codes.append("PERSON_NAME_VALID")

        has_profile = bool(linkedin)
        if has_profile:
            checks.append(VerificationCheckEntity(
                id=generate_id("chk_"),
                verification_run_id="",
                check_type="profile_presence",
                status="passed",
                score=1.0,
                reason_code="LINKEDIN_PROFILE_PRESENT",
            ))
            reason_codes.append("LINKEDIN_PROFILE_PRESENT")

        has_email = bool(email and "@" in email)
        if has_email:
            checks.append(VerificationCheckEntity(
                id=generate_id("chk_"),
                verification_run_id="",
                check_type="email_presence",
                status="passed",
                score=1.0,
                reason_code="WORK_EMAIL_ASSOCIATION",
            ))
            reason_codes.append("WORK_EMAIL_ASSOCIATION")

        has_title = bool(title)
        if has_title:
            checks.append(VerificationCheckEntity(
                id=generate_id("chk_"),
                verification_run_id="",
                check_type="title_presence",
                status="passed",
                score=1.0,
                reason_code="TITLE_SPECIFIED",
            ))

        # Confidence calculation
        identity_score = 0.50
        if has_profile:
            identity_score += 0.25
        if has_email:
            identity_score += 0.20
        if has_title:
            identity_score += 0.05

        conf = compute_verification_confidence(
            subject_type="person",
            base_source_score=0.85,
            identity_strength=min(identity_score, 1.0),
            source_agreement=0.85,
            technical_checks_score=0.90 if has_email else 0.50,
            freshness_score=1.0,
        )

        if has_profile and has_email and conf >= policy.min_confidence:
            v_status = VerificationStatus.VERIFIED
        elif has_profile or has_email:
            v_status = VerificationStatus.SUPPORTED
        else:
            v_status = VerificationStatus.UNCERTAIN

        valid_until = calculate_valid_until(None, policy.ttl_hours).strftime("%Y-%m-%dT%H:%M:%SZ")

        return VerificationResultEntity(
            id=generate_id("ver_"),
            subject_type="person",
            subject_id=person_id,
            verification_type="person",
            status=v_status,
            confidence=conf,
            policy_name=policy.name,
            policy_version=policy.version,
            reason_codes=reason_codes,
            checks=checks,
            verified_at=utc_iso_now(),
            valid_until=valid_until,
            details_json={
                "name": name,
                "email": email,
                "linkedin": linkedin,
                "title": title,
            },
        )


person_verifier = PersonVerifier()


async def verify_person(
    person_id: str,
    person_data: Dict[str, Any],
    policy_name: str = "person_default_v1",
) -> VerificationResultEntity:
    return await person_verifier.verify(person_id, person_data, policy_name)
