"""
GrowX ICP Exclusion Engine.
Evaluates hard exclusions (competitors, existing customers, prohibited geographies/sizes).
Hard exclusions strictly override any weighted positive fit score.
"""

from typing import Any, Dict, List, Optional, Tuple
from growx_crawl.intelligence.icp.models import (
    CriterionOperator,
    ExclusionType,
    ICPExclusionEntity,
    ReasonCode,
)


class ExclusionEngine:
    """Evaluates disqualifying criteria that eliminate prospects from targeting."""

    def evaluate_exclusions(
        self,
        exclusions: List[ICPExclusionEntity],
        company_data: Dict[str, Any],
        seller_competitor_ids: Optional[List[str]] = None,
        existing_customer_ids: Optional[List[str]] = None,
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Evaluates exclusions.
        Returns:
            is_excluded: True if company is disqualified.
            reason_code: standardized reason code.
            explanation: narrative explanation.
        """
        company_id = company_data.get("id") or company_data.get("company_id")

        # 1. Automatic Competitor Guard (Section 37)
        if company_id and seller_competitor_ids and company_id in seller_competitor_ids:
            # Check if an exclusion rule for competitors is active
            has_comp_rule = any(e.rule_type == ExclusionType.COMPETITOR.value for e in exclusions)
            if has_comp_rule:
                return (
                    True,
                    ReasonCode.COMPETITOR_EXCLUDED.value,
                    "Company identified as direct seller competitor (excluded from targeting).",
                )

        # 2. Existing Customer Guard (Section 36)
        if company_id and existing_customer_ids and company_id in existing_customer_ids:
            has_cust_rule = any(
                e.rule_type == ExclusionType.EXISTING_CUSTOMER.value for e in exclusions
            )
            if has_cust_rule:
                return (
                    True,
                    ReasonCode.EXISTING_CUSTOMER_EXCLUDED.value,
                    "Company is an existing customer of the seller.",
                )

        # 3. Explicit Exclusion Rules
        for ex in exclusions:
            val = company_data.get(ex.field.lower())
            if val is None:
                continue

            matched = self._match_exclusion(ex.operator, val, ex.value_json)
            if matched:
                return (
                    True,
                    ReasonCode.HARD_EXCLUSION.value,
                    f"Disqualified by rule: {ex.reason} ({ex.field} {ex.operator} {ex.value_json})",
                )

        return False, None, None

    def _match_exclusion(self, operator: str, raw_val: Any, target_val: Any) -> bool:
        op = operator.strip().lower()

        if op == CriterionOperator.EQUALS.value:
            if isinstance(raw_val, str) and isinstance(target_val, str):
                return raw_val.strip().lower() == target_val.strip().lower()
            return raw_val == target_val

        if op == CriterionOperator.IN.value:
            targets = (
                [str(t).strip().lower() for t in target_val]
                if isinstance(target_val, list)
                else [str(target_val).strip().lower()]
            )
            return str(raw_val).strip().lower() in targets

        if op == CriterionOperator.NOT_IN.value:
            targets = (
                [str(t).strip().lower() for t in target_val]
                if isinstance(target_val, list)
                else [str(target_val).strip().lower()]
            )
            return str(raw_val).strip().lower() not in targets

        if op == CriterionOperator.LESS_THAN.value:
            try:
                return float(raw_val) < float(target_val)
            except Exception:
                return False

        if op == CriterionOperator.GREATER_THAN.value:
            try:
                return float(raw_val) > float(target_val)
            except Exception:
                return False

        return False
