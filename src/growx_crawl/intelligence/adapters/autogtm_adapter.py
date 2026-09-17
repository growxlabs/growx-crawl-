import logging
from typing import Any, Dict, List, Optional
from growx_crawl.intelligence.facts.service import fact_service

logger = logging.getLogger("growx_crawl.intelligence.adapters.autogtm_adapter")


class AutoGTMAdapter:
    """
    Adapter allowing AutoGTM pipelines to consume provenance-backed canonical facts
    instead of fragile raw crawler fields (Section 76).
    """

    def __init__(self):
        self.fact_service = fact_service

    def get_verified_company_intelligence(
        self,
        company_id: str,
        scope_type: str = "global",
        scope_id: str = "global",
    ) -> Dict[str, Any]:
        """
        Retrieves current canonical facts for a company, formatted for AutoGTM analysis.
        """
        facts = self.fact_service.list_current(
            subject_type="company",
            subject_id=company_id,
            scope_type=scope_type,
            scope_id=scope_id,
        )

        intel: Dict[str, Any] = {
            "company_id": company_id,
            "industry": None,
            "employee_count": None,
            "employee_range": None,
            "revenue_range": None,
            "description": None,
            "technologies": [],
            "products": [],
            "services": [],
            "overall_confidence": 1.0,
            "facts_count": len(facts),
        }

        confidences = []

        for f in facts:
            confidences.append(f.confidence)
            val = f.current_value_json.get("value") or f.current_value_json

            if f.predicate == "company.industry":
                intel["industry"] = val if isinstance(val, str) else str(val)
            elif f.predicate == "company.employee_count":
                intel["employee_count"] = val if isinstance(val, int) else f.current_value_json.get("value")
            elif f.predicate == "company.employee_range":
                intel["employee_range"] = f.current_value_json
            elif f.predicate == "company.revenue_range":
                intel["revenue_range"] = f.current_value_json
            elif f.predicate == "company.description":
                intel["description"] = val if isinstance(val, str) else str(val)
            elif f.predicate == "company.technology":
                items = f.current_value_json.get("values") or [val if isinstance(val, str) else f.current_value_json.get("value")]
                for item in items:
                    if item and item not in intel["technologies"]:
                        intel["technologies"].append(item)
            elif f.predicate == "company.product":
                items = f.current_value_json.get("values") or [val if isinstance(val, str) else f.current_value_json.get("value")]
                for item in items:
                    if item and item not in intel["products"]:
                        intel["products"].append(item)
            elif f.predicate == "company.service":
                items = f.current_value_json.get("values") or [val if isinstance(val, str) else f.current_value_json.get("value")]
                for item in items:
                    if item and item not in intel["services"]:
                        intel["services"].append(item)

        if confidences:
            intel["overall_confidence"] = round(sum(confidences) / len(confidences), 2)

        return intel


autogtm_adapter = AutoGTMAdapter()
