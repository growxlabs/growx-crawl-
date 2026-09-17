"""
GrowX Quality Gates Engine.
Implements the 5 dedicated gate levels:
1. Canonical Ingestion
2. Intelligence Trust
3. Prospect Eligibility
4. Personalization Eligibility
5. Outreach Eligibility
"""

from typing import Any, Dict, List, Optional
from growx_crawl.quality.actions import RequiredAction, map_reasons_to_actions
from growx_crawl.quality.models import GateType, QualityDecision, QualityRuleResult, QualityStatus, RuleType
from growx_crawl.quality.policies import get_quality_policy
from growx_crawl.quality.profiles import get_quality_profile
from growx_crawl.quality.reasons import QualityReasonCode
from growx_crawl.quality.rules import QualityRuleEvaluator
from growx_crawl.quality.scoring import compute_quality_score
from growx_crawl.shared.time import calculate_future_utc_iso


class CanonicalIngestionGate:
    """Gate 1: Decides whether a raw observation is sound enough to enter canonical storage."""

    @staticmethod
    def evaluate(data: Dict[str, Any], policy_name: str = "canonical_ingestion_v1") -> QualityDecision:
        policy = get_quality_policy(GateType.CANONICAL_INGESTION, policy_name)
        rules: List[QualityRuleResult] = []
        reasons: List[str] = []

        # 1. Hard identity conflict
        conflict_res = QualityRuleEvaluator.check_hard_conflicts(data)
        if conflict_res:
            rules.append(conflict_res)
            reasons.append(conflict_res.reason_code)
            return QualityDecision(
                gate_type=GateType.CANONICAL_INGESTION,
                status=QualityStatus.QUARANTINE,
                score=0.10,
                reasons=reasons,
                required_actions=map_reasons_to_actions(reasons),
                policy_id=policy.id,
                policy_version=policy.version,
                rule_results=rules,
            )

        # 2. Required fields
        req_res = QualityRuleEvaluator.check_required_fields(
            data,
            required_fields=["subject_type", "subject_id"],
            rule_name="canonical_identity_check",
        )
        rules.append(req_res)
        if req_res.status == "failed":
            reasons.append(QualityReasonCode.MISSING_CANONICAL_IDENTITY.value)
            return QualityDecision(
                gate_type=GateType.CANONICAL_INGESTION,
                status=QualityStatus.QUARANTINE,
                score=0.0,
                reasons=reasons,
                required_actions=map_reasons_to_actions(reasons),
                policy_id=policy.id,
                policy_version=policy.version,
                rule_results=rules,
            )

        # 3. Provenance check
        if not data.get("source_id") and not data.get("source_url") and not data.get("source"):
            rules.append(QualityRuleResult(
                rule_name="provenance_source_check",
                rule_type=RuleType.REQUIRED,
                status="failed",
                score_delta=-0.40,
                reason_code=QualityReasonCode.OBSERVATION_SOURCE_MISSING.value,
            ))
            reasons.append(QualityReasonCode.OBSERVATION_SOURCE_MISSING.value)
            return QualityDecision(
                gate_type=GateType.CANONICAL_INGESTION,
                status=QualityStatus.QUARANTINE,
                score=0.20,
                reasons=reasons,
                required_actions=map_reasons_to_actions(reasons),
                policy_id=policy.id,
                policy_version=policy.version,
                rule_results=rules,
            )

        reasons.append(QualityReasonCode.CANONICAL_IDENTITY_VALID.value)
        return QualityDecision(
            gate_type=GateType.CANONICAL_INGESTION,
            status=QualityStatus.PASS,
            score=1.0,
            reasons=reasons,
            required_actions=[],
            policy_id=policy.id,
            policy_version=policy.version,
            rule_results=rules,
        )


class IntelligenceTrustGate:
    """Gate 2: Decides whether an extracted fact should be trusted as canonical intelligence."""

    @staticmethod
    def evaluate(fact_data: Dict[str, Any], policy_name: str = "intelligence_trust_v1") -> QualityDecision:
        policy = get_quality_policy(GateType.INTELLIGENCE_TRUST, policy_name)
        rules: List[QualityRuleResult] = []
        reasons: List[str] = []

        # Hard conflict check
        if fact_data.get("status") == "conflicting":
            reasons.append(QualityReasonCode.UNRESOLVED_ENTITY_CONFLICT.value)
            return QualityDecision(
                gate_type=GateType.INTELLIGENCE_TRUST,
                status=QualityStatus.BLOCKED,
                score=0.20,
                reasons=reasons,
                required_actions=map_reasons_to_actions(reasons),
                policy_id=policy.id,
                policy_version=policy.version,
                rule_results=rules,
            )

        # Freshness check
        if fact_data.get("status") == "stale":
            reasons.append(QualityReasonCode.DATA_STALE.value)
            return QualityDecision(
                gate_type=GateType.INTELLIGENCE_TRUST,
                status=QualityStatus.REVERIFY,
                score=0.45,
                reasons=reasons,
                required_actions=map_reasons_to_actions(reasons),
                policy_id=policy.id,
                policy_version=policy.version,
                rule_results=rules,
            )

        # Evidence count & confidence
        evidence_count = fact_data.get("evidence_count", 0)
        confidence = fact_data.get("confidence", 0.5)

        if evidence_count < 1:
            reasons.append(QualityReasonCode.INSUFFICIENT_EVIDENCE.value)
            return QualityDecision(
                gate_type=GateType.INTELLIGENCE_TRUST,
                status=QualityStatus.LIMITED,
                score=0.40,
                reasons=reasons,
                required_actions=map_reasons_to_actions(reasons),
                policy_id=policy.id,
                policy_version=policy.version,
                rule_results=rules,
            )

        if confidence < policy.min_score:
            reasons.append(QualityReasonCode.LOW_FACT_CONFIDENCE.value)
            status = QualityStatus.LIMITED if confidence >= 0.5 else QualityStatus.BLOCKED
            return QualityDecision(
                gate_type=GateType.INTELLIGENCE_TRUST,
                status=status,
                score=confidence,
                reasons=reasons,
                required_actions=map_reasons_to_actions(reasons),
                policy_id=policy.id,
                policy_version=policy.version,
                rule_results=rules,
            )

        reasons.append(QualityReasonCode.EVIDENCE_SUFFICIENT.value)
        reasons.append(QualityReasonCode.FACT_CONFIDENCE_ACCEPTABLE.value)
        return QualityDecision(
            gate_type=GateType.INTELLIGENCE_TRUST,
            status=QualityStatus.PASS,
            score=confidence,
            reasons=reasons,
            required_actions=[],
            policy_id=policy.id,
            policy_version=policy.version,
            rule_results=rules,
        )


class ProspectEligibilityGate:
    """Gate 3: Decides whether a company/person record is complete and verified enough for prospecting."""

    @staticmethod
    def evaluate(
        prospect_data: Dict[str, Any],
        policy_name: str = "prospect_eligibility_v1",
        existing_prospect_ids: Optional[List[str]] = None,
    ) -> QualityDecision:
        policy = get_quality_policy(GateType.PROSPECT_ELIGIBILITY, policy_name)
        profile = get_quality_profile(policy.profile)
        rules: List[QualityRuleResult] = []
        reasons: List[str] = []

        # 1. Duplicate check
        p_id = prospect_data.get("id") or prospect_data.get("domain") or ""
        dup_res = QualityRuleEvaluator.check_duplicate_prospect(p_id, existing_prospect_ids)
        if dup_res:
            rules.append(dup_res)
            reasons.append(dup_res.reason_code)
            return QualityDecision(
                gate_type=GateType.PROSPECT_ELIGIBILITY,
                status=QualityStatus.BLOCKED,
                score=0.0,
                reasons=reasons,
                required_actions=map_reasons_to_actions(reasons),
                policy_id=policy.id,
                policy_version=policy.version,
                rule_results=rules,
            )

        # 2. Required attributes (e.g. name, domain)
        req_res = QualityRuleEvaluator.check_required_fields(
            prospect_data,
            required_fields=profile.get("required_fields", ["name", "domain"]),
        )
        rules.append(req_res)
        if req_res.status == "failed":
            reasons.append(QualityReasonCode.MISSING_PRIMARY_DOMAIN.value)
            return QualityDecision(
                gate_type=GateType.PROSPECT_ELIGIBILITY,
                status=QualityStatus.BLOCKED,
                score=0.20,
                reasons=reasons,
                required_actions=map_reasons_to_actions(reasons),
                policy_id=policy.id,
                policy_version=policy.version,
                rule_results=rules,
            )

        # 3. Verification check
        ver_status = prospect_data.get("verification_status") or "unverified"
        ver_conf = float(prospect_data.get("verification_confidence", 1.0))
        ver_res = QualityRuleEvaluator.check_verification(ver_status, confidence=ver_conf)
        rules.append(ver_res)
        reasons.append(ver_res.reason_code)
        if ver_status in ("verified", "supported") and ver_conf >= 0.75:
            reasons.append(QualityReasonCode.DOMAIN_VERIFIED.value)
        elif ver_status in ("stale", "aging"):
            reasons.append(QualityReasonCode.DOMAIN_STALE.value)
        else:
            reasons.append(QualityReasonCode.DOMAIN_UNVERIFIED.value)

        # 4. Completeness
        rec_fields = profile.get("recommended_fields", ["industry", "description", "city"])
        comp_res = QualityRuleEvaluator.check_completeness(prospect_data, rec_fields)
        rules.append(comp_res)
        reasons.append(comp_res.reason_code)

        comp_ratio = comp_res.details.get("ratio", 0.5)
        score, _ = compute_quality_score(
            has_required=True,
            completeness_ratio=comp_ratio,
            verification_confidence=ver_conf if ver_status == "verified" else 0.4,
        )

        if ver_status in ("stale", "aging"):
            status = QualityStatus.REVERIFY
        elif ver_status == "unverified":
            status = QualityStatus.LIMITED
        elif score < policy.min_score:
            status = QualityStatus.LIMITED
        else:
            status = QualityStatus.PASS

        return QualityDecision(
            gate_type=GateType.PROSPECT_ELIGIBILITY,
            status=status,
            score=score,
            reasons=reasons,
            required_actions=map_reasons_to_actions(reasons),
            policy_id=policy.id,
            policy_version=policy.version,
            rule_results=rules,
        )


class PersonalizationGate:
    """Gate 4: Decides whether context and facts are sufficient for LLM sales sequence drafting."""

    @staticmethod
    def evaluate(context_data: Dict[str, Any], policy_name: str = "personalization_v1") -> QualityDecision:
        policy = get_quality_policy(GateType.PERSONALIZATION_ELIGIBILITY, policy_name)
        profile = get_quality_profile(policy.profile)
        rules: List[QualityRuleResult] = []
        reasons: List[str] = []

        # Required fields (company, lead name, offer)
        req_res = QualityRuleEvaluator.check_required_fields(
            context_data,
            required_fields=profile.get("required_fields", ["company_name", "lead_name", "sender_offer"]),
        )
        rules.append(req_res)
        if req_res.status == "failed":
            reasons.append(QualityReasonCode.PROFILE_INCOMPLETE.value)
            return QualityDecision(
                gate_type=GateType.PERSONALIZATION_ELIGIBILITY,
                status=QualityStatus.BLOCKED,
                score=0.20,
                reasons=reasons,
                required_actions=map_reasons_to_actions(reasons),
                policy_id=policy.id,
                policy_version=policy.version,
                rule_results=rules,
            )

        # Hook / Evidence presence
        hook = context_data.get("personalization_hook")
        if not hook:
            reasons.append(QualityReasonCode.INSUFFICIENT_EVIDENCE.value)
            return QualityDecision(
                gate_type=GateType.PERSONALIZATION_ELIGIBILITY,
                status=QualityStatus.LIMITED,
                score=0.55,
                reasons=reasons,
                required_actions=[RequiredAction.COLLECT_MORE_EVIDENCE.value],
                policy_id=policy.id,
                policy_version=policy.version,
                rule_results=rules,
            )

        reasons.append(QualityReasonCode.EVIDENCE_SUFFICIENT.value)
        return QualityDecision(
            gate_type=GateType.PERSONALIZATION_ELIGIBILITY,
            status=QualityStatus.PASS,
            score=0.85,
            reasons=reasons,
            required_actions=[],
            policy_id=policy.id,
            policy_version=policy.version,
            rule_results=rules,
        )


class OutreachEligibilityGate:
    """Gate 5: The final high-stakes gate ensuring recipient email, suppression, and delivery safety."""

    @staticmethod
    def evaluate(
        outreach_data: Dict[str, Any],
        policy_name: str = "outreach_v1",
        suppressed_emails: Optional[List[str]] = None,
    ) -> QualityDecision:
        policy = get_quality_policy(GateType.OUTREACH_ELIGIBILITY, policy_name)
        rules: List[QualityRuleResult] = []
        reasons: List[str] = []

        email = (outreach_data.get("email") or "").strip().lower()

        # 1. Hard block: Missing email
        if not email:
            reasons.append(QualityReasonCode.EMAIL_UNVERIFIED.value)
            return QualityDecision(
                gate_type=GateType.OUTREACH_ELIGIBILITY,
                status=QualityStatus.BLOCKED,
                score=0.0,
                reasons=reasons,
                required_actions=[RequiredAction.UPDATE_CONTACT_INFO.value],
                policy_id=policy.id,
                policy_version=policy.version,
                rule_results=rules,
            )

        # 2. Hard block: Suppression check
        supp_res = QualityRuleEvaluator.check_hard_suppression(email, suppressed_emails)
        if supp_res:
            rules.append(supp_res)
            reasons.append(supp_res.reason_code)
            return QualityDecision(
                gate_type=GateType.OUTREACH_ELIGIBILITY,
                status=QualityStatus.BLOCKED,
                score=0.0,
                reasons=reasons,
                required_actions=map_reasons_to_actions(reasons),
                policy_id=policy.id,
                policy_version=policy.version,
                rule_results=rules,
            )
        reasons.append(QualityReasonCode.SUPPRESSION_CLEAR.value)

        # 3. Email verification status
        email_status = (
            outreach_data.get("email_status")
            or outreach_data.get("email_verification_status")
            or "unverified"
        ).lower()
        is_role = bool(outreach_data.get("is_role_account") or outreach_data.get("is_role"))
        is_catchall = bool(outreach_data.get("is_catchall"))
        employment_status = (outreach_data.get("employment_status") or "verified").lower()

        # 4. Employment staleness check
        if employment_status in ("stale", "ended"):
            reasons.append(QualityReasonCode.STALE_EMPLOYMENT.value)
            return QualityDecision(
                gate_type=GateType.OUTREACH_ELIGIBILITY,
                status=QualityStatus.REVERIFY,
                score=0.50,
                reasons=reasons,
                required_actions=[RequiredAction.REFRESH_EMPLOYMENT.value],
                policy_id=policy.id,
                policy_version=policy.version,
                rule_results=rules,
            )

        # 5. Role account or Catch-all checks
        if is_role:
            reasons.append(QualityReasonCode.EMAIL_ROLE_ACCOUNT.value)
            return QualityDecision(
                gate_type=GateType.OUTREACH_ELIGIBILITY,
                status=QualityStatus.LIMITED,
                score=0.60,
                reasons=reasons,
                required_actions=[RequiredAction.REVERIFY_EMAIL.value],
                policy_id=policy.id,
                policy_version=policy.version,
                rule_results=rules,
            )

        if is_catchall:
            reasons.append(QualityReasonCode.EMAIL_CATCHALL.value)
            return QualityDecision(
                gate_type=GateType.OUTREACH_ELIGIBILITY,
                status=QualityStatus.LIMITED,
                score=0.65,
                reasons=reasons,
                required_actions=[RequiredAction.REVERIFY_EMAIL.value],
                policy_id=policy.id,
                policy_version=policy.version,
                rule_results=rules,
            )

        if email_status not in ("verified", "valid"):
            reasons.append(QualityReasonCode.EMAIL_UNVERIFIED.value)
            return QualityDecision(
                gate_type=GateType.OUTREACH_ELIGIBILITY,
                status=QualityStatus.REVERIFY,
                score=0.45,
                reasons=reasons,
                required_actions=[RequiredAction.REVERIFY_EMAIL.value],
                policy_id=policy.id,
                policy_version=policy.version,
                rule_results=rules,
            )

        reasons.append(QualityReasonCode.EMAIL_VERIFIED.value)
        reasons.append(QualityReasonCode.EMPLOYMENT_VERIFIED.value)

        return QualityDecision(
            gate_type=GateType.OUTREACH_ELIGIBILITY,
            status=QualityStatus.PASS,
            score=0.95,
            reasons=reasons,
            required_actions=[],
            policy_id=policy.id,
            policy_version=policy.version,
            rule_results=rules,
        )
