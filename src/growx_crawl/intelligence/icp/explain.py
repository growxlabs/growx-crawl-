"""
GrowX ICP Explainer.
Produces explainable targeting summaries, positive/negative drivers, and reason code lists.
"""

from typing import Any, Dict, List, Optional
from growx_crawl.intelligence.icp.models import FitStatus, ReasonCode


class ICPExplainer:
    """Explains company and person fit determinations."""

    @staticmethod
    def explain_company_fit(
        company_name: str,
        fit_score: float,
        data_confidence: float,
        status: str,
        reason_codes: List[str],
        positive_drivers: List[str],
        negative_drivers: List[str],
        unknown_factors: List[str],
    ) -> Dict[str, Any]:
        """Constructs an explainability packet for company fit evaluation."""
        if status == FitStatus.EXCLUDED.value:
            narrative = f"{company_name} is disqualified from targeting: {', '.join(negative_drivers)}."
        elif status == FitStatus.INSUFFICIENT_DATA.value:
            narrative = f"{company_name} lacks sufficient verified data to determine ICP fit (confidence: {data_confidence})."
        else:
            status_label = status.replace("_", " ").title()
            drivers_str = f" Driven by {', '.join(positive_drivers)}." if positive_drivers else ""
            concerns_str = f" Concerns: {', '.join(negative_drivers)}." if negative_drivers else ""
            narrative = f"{company_name} evaluated as {status_label} ({int(fit_score * 100)}% match, {int(data_confidence * 100)}% confidence).{drivers_str}{concerns_str}"

        return {
            "narrative": narrative,
            "fit_score": fit_score,
            "data_confidence": data_confidence,
            "status": status,
            "reason_codes": reason_codes,
            "positive_drivers": positive_drivers,
            "negative_drivers": negative_drivers,
            "positive_factors": positive_drivers,
            "negative_factors": negative_drivers,
            "unknown_factors": unknown_factors,
        }


    @staticmethod
    def explain_person_fit(
        person_name: str,
        role_matched: Optional[str],
        fit_score: float,
        employment_confidence: float,
        reasons: List[str],
    ) -> Dict[str, Any]:
        """Constructs an explainability packet for person fit evaluation."""
        if not role_matched or fit_score < 0.30:
            narrative = f"{person_name} does not align with targeted buyer personas."
        else:
            narrative = f"{person_name} identified as target buyer role '{role_matched}' ({int(fit_score * 100)}% persona match, {int(employment_confidence * 100)}% employment confidence)."

        return {
            "narrative": narrative,
            "fit_score": fit_score,
            "employment_confidence": employment_confidence,
            "role_matched": role_matched,
            "reason_codes": reasons,
        }
