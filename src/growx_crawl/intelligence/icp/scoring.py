"""
GrowX ICP Scorer.
Computes explainable company fit scores, data confidence, and person buyer alignment.
Enforces hard exclusions, must-have condition gating, and missing-data confidence separation.
"""

import hashlib
import json
from typing import Any, Dict, List, Optional
from growx_crawl.intelligence.icp.criteria import CriterionEvaluator
from growx_crawl.intelligence.icp.exclusions import ExclusionEngine
from growx_crawl.intelligence.icp.explain import ICPExplainer
from growx_crawl.intelligence.icp.models import (
    FitStatus,
    ICPCompanyScoreEntity,
    ICPCriterionEntity,
    ICPExclusionEntity,
    ICPPersonaEntity,
    ICPPersonScoreEntity,
    ReasonCode,
    RequirementType,
)
from growx_crawl.intelligence.icp.personas import PersonaMatcher
from growx_crawl.intelligence.icp.policies import DEFAULT_ICP_POLICY, ICPEvaluationPolicy
from growx_crawl.shared.ids import generate_id
from growx_crawl.shared.time import utc_iso_now


class ICPScorer:
    """Evaluates prospects against structured ICP definitions."""

    def __init__(
        self,
        criterion_evaluator: Optional[CriterionEvaluator] = None,
        exclusion_engine: Optional[ExclusionEngine] = None,
        persona_matcher: Optional[PersonaMatcher] = None,
        policy: ICPEvaluationPolicy = DEFAULT_ICP_POLICY,
    ):
        self.criterion_evaluator = criterion_evaluator or CriterionEvaluator()
        self.exclusion_engine = exclusion_engine or ExclusionEngine()
        self.persona_matcher = persona_matcher or PersonaMatcher()
        self.policy = policy
        self.explainer = ICPExplainer()

    def score_company(
        self,
        icp_version_id: str,
        criteria: List[ICPCriterionEntity],
        exclusions: List[ICPExclusionEntity],
        company_data: Dict[str, Any],
        facts: Optional[List[Any]] = None,
        signals: Optional[List[Any]] = None,
        seller_competitor_ids: Optional[List[str]] = None,
        existing_customer_ids: Optional[List[str]] = None,
    ) -> ICPCompanyScoreEntity:
        """
        Evaluates a company prospect against an ICP version.
        Separates fit score from data confidence and applies hard exclusions.
        """
        company_id = company_data.get("id") or company_data.get("company_id") or "unknown"
        company_name = company_data.get("canonical_name") or company_data.get("company_name") or company_id

        # 1. Evaluate Hard Exclusions (Section 34, 44)
        is_excluded, excl_reason, excl_narrative = self.exclusion_engine.evaluate_exclusions(
            exclusions=exclusions,
            company_data=company_data,
            seller_competitor_ids=seller_competitor_ids,
            existing_customer_ids=existing_customer_ids,
        )
        if is_excluded:
            explanation = self.explainer.explain_company_fit(
                company_name=company_name,
                fit_score=0.0,
                data_confidence=1.0,
                status=FitStatus.EXCLUDED.value,
                reason_codes=[excl_reason or ReasonCode.HARD_EXCLUSION.value],
                positive_drivers=[],
                negative_drivers=[excl_narrative or "Disqualified by exclusion rule"],
                unknown_factors=[],
            )
            return ICPCompanyScoreEntity(
                id=generate_id("sc_"),
                icp_version_id=icp_version_id,
                company_id=company_id,
                fit_score=0.0,
                data_confidence=1.0,
                status=FitStatus.EXCLUDED.value,
                fingerprint=self._compute_fingerprint(icp_version_id, company_id, company_data),
                explanation_json=explanation,
            )

        # 2. Evaluate Individual Criteria
        total_weight = 0.0
        earned_score = 0.0
        must_have_failed = False
        unknown_count = 0
        reason_codes: List[str] = []
        positive_drivers: List[str] = []
        negative_drivers: List[str] = []
        unknown_factors: List[str] = []

        for crit in criteria:
            total_weight += crit.weight
            matched, contrib, r_code = self.criterion_evaluator.evaluate_criterion(
                criterion=crit,
                company_data=company_data,
                facts=facts,
                signals=signals,
            )

            if matched is None:
                # Missing data policy (Sections 82–84): unknown attribute
                unknown_count += 1
                unknown_factors.append(crit.field)

            elif matched:
                earned_score += contrib
                if r_code and r_code not in reason_codes:
                    reason_codes.append(r_code)
                positive_drivers.append(f"{crit.field} matched")
            else:
                # Mismatch
                if r_code and r_code not in reason_codes:
                    reason_codes.append(r_code)
                if crit.requirement_type == RequirementType.REQUIRED.value:
                    must_have_failed = True
                    if ReasonCode.MUST_HAVE_FAILED.value not in reason_codes:
                        reason_codes.append(ReasonCode.MUST_HAVE_FAILED.value)
                    negative_drivers.append(f"Required condition failed: {crit.field}")
                else:
                    negative_drivers.append(f"{crit.field} mismatch")


        # 3. Calculate Fit Score
        if total_weight > 0:
            raw_fit = max(0.0, earned_score / total_weight)
        else:
            raw_fit = 0.5

        if must_have_failed:
            raw_fit = min(raw_fit, 0.25)

        fit_score = min(1.0, max(0.0, round(raw_fit, 3)))

        # 4. Calculate Data Confidence (Kept strictly separate per Section 39)
        num_criteria = max(1, len(criteria))
        unknown_ratio = unknown_count / num_criteria
        data_confidence = round(max(0.1, 1.0 - (unknown_ratio * self.policy.missing_data_confidence_penalty * 3.0)), 3)

        # 5. Determine Fit Status
        if data_confidence < self.policy.minimum_data_confidence_gate:
            status = FitStatus.INSUFFICIENT_DATA.value
            reason_codes.append(ReasonCode.INSUFFICIENT_DATA.value)
        elif fit_score >= self.policy.min_fit_excellent:
            status = FitStatus.EXCELLENT_FIT.value
        elif fit_score >= self.policy.min_fit_strong:
            status = FitStatus.STRONG_FIT.value
        elif fit_score >= self.policy.min_fit_possible:
            status = FitStatus.POSSIBLE_FIT.value
        else:
            status = FitStatus.WEAK_FIT.value

        explanation = self.explainer.explain_company_fit(
            company_name=company_name,
            fit_score=fit_score,
            data_confidence=data_confidence,
            status=status,
            reason_codes=reason_codes,
            positive_drivers=positive_drivers,
            negative_drivers=negative_drivers,
            unknown_factors=unknown_factors,
        )

        return ICPCompanyScoreEntity(
            id=generate_id("sc_"),
            icp_version_id=icp_version_id,
            company_id=company_id,
            fit_score=fit_score,
            data_confidence=data_confidence,
            status=status,
            fingerprint=self._compute_fingerprint(icp_version_id, company_id, company_data),
            explanation_json=explanation,
        )

    def score_person(
        self,
        icp_version_id: str,
        personas: List[ICPPersonaEntity],
        person_data: Dict[str, Any],
        company_id: str,
    ) -> ICPPersonScoreEntity:
        """Evaluates an individual against target buyer personas."""
        person_id = person_data.get("id") or person_data.get("person_id") or "unknown"
        person_name = person_data.get("name") or person_id
        emp_confidence = float(person_data.get("employment_confidence", 1.0))

        matched_persona, p_score, matched_role, reasons = self.persona_matcher.match_person(
            personas=personas,
            person_data=person_data,
        )

        explanation = self.explainer.explain_person_fit(
            person_name=person_name,
            role_matched=matched_role,
            fit_score=p_score,
            employment_confidence=emp_confidence,
            reasons=reasons,
        )

        return ICPPersonScoreEntity(
            id=generate_id("psc_"),
            icp_version_id=icp_version_id,
            person_id=person_id,
            company_id=company_id,
            persona_id=matched_persona.id if matched_persona else None,
            fit_score=p_score,
            employment_confidence=emp_confidence,
            role_matched=matched_role,
            explanation_json=explanation,
        )

    def _compute_fingerprint(
        self,
        icp_version_id: str,
        company_id: str,
        company_data: Dict[str, Any],
    ) -> str:
        """Generates a stable cache fingerprint for idempotency (Section 107-108)."""
        h = hashlib.sha256()
        h.update(icp_version_id.encode())
        h.update(company_id.encode())
        for k in sorted(company_data.keys()):
            h.update(f"{k}:{company_data[k]}".encode())
        return h.hexdigest()
