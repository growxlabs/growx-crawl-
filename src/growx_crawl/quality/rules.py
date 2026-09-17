"""
GrowX Data Quality Rule Engine.
Evaluates atomic rules across required attributes, hard blocks, soft penalties,
freshness, verification, completeness, conflicts, and duplicate suppression.
"""

from typing import Any, Dict, List, Optional, Tuple
from growx_crawl.quality.models import QualityRuleResult, RuleType
from growx_crawl.quality.reasons import QualityReasonCode


class QualityRuleEvaluator:
    """Evaluates rules in deterministic sequence: hard blocks first, then completeness, then soft scoring."""

    @staticmethod
    def check_required_fields(
        data: Dict[str, Any],
        required_fields: List[str],
        rule_name: str = "required_fields_check",
    ) -> QualityRuleResult:
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            return QualityRuleResult(
                rule_name=rule_name,
                rule_type=RuleType.REQUIRED,
                status="failed",
                score_delta=-0.50,
                reason_code=QualityReasonCode.MISSING_REQUIRED_FIELDS.value,
                details={"missing_fields": missing},
            )
        return QualityRuleResult(
            rule_name=rule_name,
            rule_type=RuleType.REQUIRED,
            status="passed",
            score_delta=0.0,
            reason_code=QualityReasonCode.CANONICAL_IDENTITY_VALID.value,
        )

    @staticmethod
    def check_hard_suppression(
        email: str,
        suppressed_emails: Optional[List[str]] = None,
    ) -> Optional[QualityRuleResult]:
        clean_email = (email or "").strip().lower()
        if suppressed_emails and clean_email in [e.lower() for e in suppressed_emails]:
            return QualityRuleResult(
                rule_name="email_suppression_check",
                rule_type=RuleType.HARD_BLOCK,
                status="failed",
                score_delta=-1.0,
                reason_code=QualityReasonCode.EMAIL_SUPPRESSED.value,
                details={"email": clean_email, "suppressed": True},
            )
        return None

    @staticmethod
    def check_hard_conflicts(data: Dict[str, Any]) -> Optional[QualityRuleResult]:
        if data.get("has_unresolved_conflict") or data.get("identity_conflict") or data.get("has_hard_conflict"):
            return QualityRuleResult(
                rule_name="identity_conflict_check",
                rule_type=RuleType.HARD_BLOCK,
                status="failed",
                score_delta=-1.0,
                reason_code=QualityReasonCode.HARD_IDENTITY_CONFLICT.value,
                details={"conflict": data.get("conflict_details", "Hard entity clash detected")},
            )
        return None

    @staticmethod
    def check_duplicate_prospect(
        prospect_id: str,
        existing_prospect_ids: Optional[List[str]] = None,
    ) -> Optional[QualityRuleResult]:
        if existing_prospect_ids and prospect_id in existing_prospect_ids:
            return QualityRuleResult(
                rule_name="duplicate_prospect_check",
                rule_type=RuleType.HARD_BLOCK,
                status="failed",
                score_delta=-1.0,
                reason_code=QualityReasonCode.DUPLICATE_PROSPECT.value,
                details={"duplicate_id": prospect_id},
            )
        return None

    @staticmethod
    def check_completeness(
        data: Dict[str, Any],
        recommended_fields: List[str],
        min_ratio: float = 0.60,
    ) -> QualityRuleResult:
        if not recommended_fields:
            return QualityRuleResult(
                rule_name="completeness_check",
                rule_type=RuleType.COMPLETENESS,
                status="passed",
                score_delta=0.0,
                reason_code=QualityReasonCode.PROFILE_COMPLETENESS_MET.value,
                details={"ratio": 1.0},
            )

        present = [f for f in recommended_fields if bool(data.get(f))]
        ratio = round(len(present) / len(recommended_fields), 3)

        if ratio >= min_ratio:
            return QualityRuleResult(
                rule_name="completeness_check",
                rule_type=RuleType.COMPLETENESS,
                status="passed",
                score_delta=round(ratio * 0.40, 3),
                reason_code=QualityReasonCode.PROFILE_COMPLETENESS_MET.value,
                details={"ratio": ratio, "present_fields": present},
            )
        return QualityRuleResult(
            rule_name="completeness_check",
            rule_type=RuleType.COMPLETENESS,
            status="warning",
            score_delta=-0.20,
            reason_code=QualityReasonCode.PROFILE_INCOMPLETE.value,
            details={"ratio": ratio, "missing_recommended": [f for f in recommended_fields if f not in present]},
        )

    @staticmethod
    def check_verification(
        verification_status: Optional[str],
        min_confidence: float = 0.75,
        confidence: float = 1.0,
    ) -> QualityRuleResult:
        status_clean = (verification_status or "unverified").lower()
        if status_clean in ("verified", "supported") and confidence >= min_confidence:
            return QualityRuleResult(
                rule_name="verification_check",
                rule_type=RuleType.VERIFICATION,
                status="passed",
                score_delta=0.30,
                reason_code=QualityReasonCode.COMPANY_VERIFIED.value,
                details={"status": status_clean, "confidence": confidence},
            )
        elif status_clean in ("stale", "aging"):
            return QualityRuleResult(
                rule_name="verification_check",
                rule_type=RuleType.FRESHNESS,
                status="warning",
                score_delta=-0.15,
                reason_code=QualityReasonCode.DATA_STALE.value,
                details={"status": status_clean},
            )
        return QualityRuleResult(
            rule_name="verification_check",
            rule_type=RuleType.VERIFICATION,
            status="failed",
            score_delta=-0.30,
            reason_code=QualityReasonCode.COMPANY_UNVERIFIED.value,
            details={"status": status_clean, "confidence": confidence},
        )
