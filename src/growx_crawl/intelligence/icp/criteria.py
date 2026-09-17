"""
GrowX ICP Criterion Evaluator.
Evaluates individual firmographic, technographic, geographic, and signal rules.
Handles missing data as unknown rather than automatically false.
"""

from typing import Any, Dict, List, Optional, Tuple
from growx_crawl.intelligence.icp.models import (
    CriterionCategory,
    CriterionOperator,
    ICPCriterionEntity,
    ReasonCode,
    RequirementType,
)


COUNTRY_ALIASES = {
    "us": "united states",
    "usa": "united states",
    "united states of america": "united states",
    "uk": "united kingdom",
    "gb": "united kingdom",
    "great britain": "united kingdom",
    "in": "india",
    "ca": "canada",
    "au": "australia",
    "de": "germany",
    "fr": "france",
    "sg": "singapore",
}


def _norm_val(v: Any) -> str:
    s = str(v).strip().lower()
    return COUNTRY_ALIASES.get(s, s)


class CriterionEvaluator:
    """Evaluates individual ICP criteria against prospect data."""

    def evaluate_criterion(
        self,
        criterion: ICPCriterionEntity,
        company_data: Dict[str, Any],
        facts: Optional[List[Any]] = None,
        signals: Optional[List[Any]] = None,
    ) -> Tuple[Optional[bool], float, Optional[str]]:
        """
        Evaluates a criterion.
        Returns:
            matched: True if matched, False if mismatched, None if data is unknown.
            score: weight-adjusted score contribution.
            reason_code: standardized reason code if matched or failed.
        """
        raw_val = self._extract_field_value(criterion.field, company_data, facts, signals)

        # Missing data policy (Sections 82–84): None means unknown, not mismatch
        if raw_val is None:
            return None, 0.0, None

        matched = self._apply_operator(criterion.operator, raw_val, criterion.value_json)

        weight = criterion.weight
        req_type = criterion.requirement_type

        if matched:
            reason = self._resolve_positive_reason(criterion.category, criterion.field)
            if req_type == RequirementType.BOOST.value:
                score = weight * 1.5
            elif req_type == RequirementType.REQUIRED.value:
                score = weight * 1.2
            elif req_type == RequirementType.PENALTY.value:
                score = -weight
            else:
                score = weight
            return True, score, reason
        else:
            reason = self._resolve_negative_reason(criterion.category, criterion.field)
            if req_type == RequirementType.REQUIRED.value:
                score = -weight * 2.0
            elif req_type == RequirementType.PENALTY.value:
                score = -weight
            else:
                score = 0.0
            return False, score, reason

    def _extract_field_value(
        self,
        field: str,
        company_data: Dict[str, Any],
        facts: Optional[List[Any]] = None,
        signals: Optional[List[Any]] = None,
    ) -> Any:
        """Extracts field from company attributes, facts, or signals."""
        f_norm = field.strip().lower()

        # Check company_data dict directly
        if f_norm in company_data and company_data[f_norm] is not None:
            return company_data[f_norm]

        # Alias mappings
        aliases = {
            "industry": ["industry", "industries", "category"],
            "country": ["country_code", "country", "location"],
            "city": ["city", "location"],
            "employee_count": ["employee_count", "employees", "size", "employee_range"],
            "employee_range": ["employee_range", "employee_count", "size"],
            "technologies": ["technologies_used", "technologies", "tech_stack"],
            "products": ["products", "services"],
        }
        for alias in aliases.get(f_norm, []):
            if alias in company_data and company_data[alias] is not None:
                return company_data[alias]

        # Check facts list if provided
        if facts:
            fact_predicate = f"company.{f_norm}"
            for fact in facts:
                pred = getattr(fact, "predicate", "") or (
                    fact.get("predicate") if isinstance(fact, dict) else ""
                )
                if pred in (f_norm, fact_predicate):
                    val_json = getattr(fact, "current_value_json", {}) or (
                        fact.get("current_value_json") if isinstance(fact, dict) else {}
                    )
                    return val_json.get("value") if isinstance(val_json, dict) else val_json

        # Check signals for temporal criteria (e.g. employee growth, expansion)
        if signals:
            for sig in signals:
                sig_type = getattr(sig, "signal_type", "") or (
                    sig.get("signal_type") if isinstance(sig, dict) else ""
                )
                if sig_type == f_norm:
                    return True
                if f_norm == "employee_growth" and sig_type == "hiring_growth":
                    return True
                if f_norm == "expansion" and sig_type in ("location_expansion", "hiring_growth"):
                    return True

        return None

    def _apply_operator(self, operator: str, raw_val: Any, target_val: Any) -> bool:
        """Applies comparison operator."""
        op = operator.strip().lower()

        if op in (CriterionOperator.EXISTS.value, "exists"):
            return bool(raw_val)
        if op in (CriterionOperator.NOT_EXISTS.value, "not_exists"):
            return not bool(raw_val)

        if op in (CriterionOperator.EQUALS.value, "equals", "eq"):
            if isinstance(raw_val, str) and isinstance(target_val, str):
                return _norm_val(raw_val) == _norm_val(target_val)
            return raw_val == target_val

        if op in (CriterionOperator.IN.value, "in"):
            targets = (
                [_norm_val(t) for t in target_val]
                if isinstance(target_val, list)
                else [_norm_val(target_val)]
            )
            if isinstance(raw_val, list):
                raw_list = [_norm_val(r) for r in raw_val]
                return any(r in targets for r in raw_list)
            return _norm_val(raw_val) in targets

        if op in (CriterionOperator.NOT_IN.value, "not_in"):
            targets = (
                [_norm_val(t) for t in target_val]
                if isinstance(target_val, list)
                else [_norm_val(target_val)]
            )
            return _norm_val(raw_val) not in targets

        if op in (CriterionOperator.CONTAINS.value, "contains"):
            if isinstance(raw_val, list):
                raw_str_list = [str(r).strip().lower() for r in raw_val]
                return str(target_val).strip().lower() in raw_str_list
            return str(target_val).strip().lower() in str(raw_val).strip().lower()

        if op in (CriterionOperator.GREATER_THAN.value, "greater_than", "gt"):
            try:
                return float(self._parse_numeric(raw_val)) > float(target_val)
            except Exception:
                return False

        if op in (
            CriterionOperator.GREATER_THAN_OR_EQUAL.value,
            CriterionOperator.GTE.value,
            "greater_than_or_equal",
            "gte",
        ):
            try:
                return float(self._parse_numeric(raw_val)) >= float(target_val)
            except Exception:
                return False

        if op in (CriterionOperator.LESS_THAN.value, "less_than", "lt"):
            try:
                return float(self._parse_numeric(raw_val)) < float(target_val)
            except Exception:
                return False

        if op in (
            CriterionOperator.LESS_THAN_OR_EQUAL.value,
            CriterionOperator.LTE.value,
            "less_than_or_equal",
            "lte",
        ):
            try:
                return float(self._parse_numeric(raw_val)) <= float(target_val)
            except Exception:
                return False

        if op in (CriterionOperator.RANGE.value, "range"):
            try:
                val = float(self._parse_numeric(raw_val))
                if isinstance(target_val, (list, tuple)) and len(target_val) == 2:
                    return float(target_val[0]) <= val <= float(target_val[1])
            except Exception:
                return False

        return False

    def _parse_numeric(self, val: Any) -> float:
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            # Parse ranges like "51-200" into midpoint or minimum
            cleaned = val.replace(",", "").strip()
            if "-" in cleaned:
                parts = cleaned.split("-")
                return float(parts[0].strip())
            return float(cleaned)
        raise ValueError(f"Cannot parse numeric from {val}")

    def _resolve_positive_reason(self, category: str, field: str) -> str:
        f = field.lower()
        if "industry" in f:
            return ReasonCode.INDUSTRY_MATCH.value
        if "size" in f or "employee" in f:
            return ReasonCode.SIZE_MATCH.value
        if "country" in f or "city" in f or "geo" in f:
            return ReasonCode.GEOGRAPHY_MATCH.value
        if "tech" in f or "erp" in f or "crm" in f:
            return ReasonCode.TECH_MATCH.value
        if "growth" in f or "expansion" in f or "hiring" in f:
            return ReasonCode.RECENT_EXPANSION.value
        return ReasonCode.OPERATIONS_MATCH.value

    def _resolve_negative_reason(self, category: str, field: str) -> str:
        f = field.lower()
        if "country" in f or "geo" in f:
            return ReasonCode.WRONG_GEOGRAPHY.value
        if "size" in f or "employee" in f:
            return ReasonCode.TOO_SMALL.value
        return ReasonCode.MUST_HAVE_FAILED.value
