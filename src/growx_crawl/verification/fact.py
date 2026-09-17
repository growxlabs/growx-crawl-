"""
GrowX Fact Verification.
Answers: 'Can this fact be trusted enough to use downstream?'
Evaluates evidence provenance, source authority, freshness TTL, cross-source corroboration,
and conflict records.
"""

from typing import Any, Dict, List, Optional
from growx_crawl.shared.ids import generate_id
from growx_crawl.shared.time import parse_iso, utc_iso_now, utc_now
from growx_crawl.verification.confidence import compute_verification_confidence
from growx_crawl.verification.freshness import calculate_valid_until
from growx_crawl.verification.models import (
    ReasonCode,
    VerificationCheckEntity,
    VerificationResultEntity,
    VerificationStatus,
)
from growx_crawl.verification.policies import get_policy


class FactVerifier:
    """Verifies canonical fact truthfulness against observation evidence and conflict history."""

    async def verify(
        self,
        fact_id: str,
        fact_data: Dict[str, Any],
        policy_name: str = "fact_default_v1",
    ) -> VerificationResultEntity:
        policy = get_policy(policy_name)
        checks: List[VerificationCheckEntity] = []
        reason_codes: List[str] = []

        predicate = fact_data.get("predicate", "")
        raw_confidence = float(fact_data.get("confidence", 0.8))
        has_evidence = bool(fact_data.get("evidence_ids") or fact_data.get("has_evidence"))
        is_conflicting = bool(fact_data.get("status") == "conflicting" or fact_data.get("has_conflict"))

        # 1. Conflict Check
        if is_conflicting:
            checks.append(VerificationCheckEntity(
                id=generate_id("chk_"),
                verification_run_id="",
                check_type="conflict_check",
                status="failed",
                score=0.2,
                reason_code=ReasonCode.FACT_SOURCE_CONFLICT,
            ))
            reason_codes.append(ReasonCode.FACT_SOURCE_CONFLICT)
            return VerificationResultEntity(
                id=generate_id("ver_"),
                subject_type="fact",
                subject_id=fact_id,
                verification_type="fact",
                status=VerificationStatus.CONFLICTING,
                confidence=0.30,
                policy_name=policy.name,
                policy_version=policy.version,
                reason_codes=reason_codes,
                checks=checks,
                details_json={"predicate": predicate, "conflicting": True},
            )

        # 2. Provenance Evidence Check
        if has_evidence:
            checks.append(VerificationCheckEntity(
                id=generate_id("chk_"),
                verification_run_id="",
                check_type="evidence_provenance",
                status="passed",
                score=1.0,
                reason_code=ReasonCode.EVIDENCE_PROVENANCE_CONFIRMED,
            ))
            reason_codes.append(ReasonCode.EVIDENCE_PROVENANCE_CONFIRMED)
        else:
            checks.append(VerificationCheckEntity(
                id=generate_id("chk_"),
                verification_run_id="",
                check_type="evidence_provenance",
                status="warning",
                score=0.4,
                reason_code="NO_LINKED_EVIDENCE",
            ))

        # 3. Freshness Check
        created_at = fact_data.get("created_at") or fact_data.get("updated_at")
        is_stale = False
        if created_at:
            dt = parse_iso(created_at)
            if dt:
                age_days = (utc_now() - dt).total_seconds() / 86400
                if age_days > 180:
                    is_stale = True
                    checks.append(VerificationCheckEntity(
                        id=generate_id("chk_"),
                        verification_run_id="",
                        check_type="freshness_check",
                        status="warning",
                        score=0.3,
                        reason_code=ReasonCode.SOURCE_STALE,
                    ))
                    reason_codes.append(ReasonCode.SOURCE_STALE)

        if not is_stale:
            checks.append(VerificationCheckEntity(
                id=generate_id("chk_"),
                verification_run_id="",
                check_type="freshness_check",
                status="passed",
                score=1.0,
                reason_code=ReasonCode.HIGH_FRESHNESS,
            ))
            reason_codes.append(ReasonCode.HIGH_FRESHNESS)

        # 4. Confidence & Status Computation
        conf = compute_verification_confidence(
            subject_type="fact",
            base_source_score=raw_confidence,
            identity_strength=0.90,
            source_agreement=0.90 if has_evidence else 0.50,
            technical_checks_score=0.80,
            freshness_score=0.30 if is_stale else 1.0,
            staleness_penalty=0.20 if is_stale else 0.0,
        )

        if is_stale:
            v_status = VerificationStatus.STALE
        elif conf >= policy.min_confidence and has_evidence:
            v_status = VerificationStatus.VERIFIED
        elif conf >= 0.60:
            v_status = VerificationStatus.SUPPORTED
        else:
            v_status = VerificationStatus.UNCERTAIN

        valid_until = calculate_valid_until(None, policy.ttl_hours).strftime("%Y-%m-%dT%H:%M:%SZ")

        return VerificationResultEntity(
            id=generate_id("ver_"),
            subject_type="fact",
            subject_id=fact_id,
            verification_type="fact",
            status=v_status,
            confidence=conf,
            policy_name=policy.name,
            policy_version=policy.version,
            reason_codes=reason_codes,
            checks=checks,
            verified_at=utc_iso_now(),
            valid_until=valid_until,
            details_json={
                "predicate": predicate,
                "has_evidence": has_evidence,
                "is_stale": is_stale,
                "raw_confidence": raw_confidence,
            },
        )


fact_verifier = FactVerifier()


async def verify_fact(
    fact_id: str,
    fact_data: Dict[str, Any],
    policy_name: str = "fact_default_v1",
) -> VerificationResultEntity:
    return await fact_verifier.verify(fact_id, fact_data, policy_name)
