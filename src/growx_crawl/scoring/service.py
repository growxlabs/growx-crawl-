"""
GrowX Scoring Service.
Maintains strict separation between:
1. Data Confidence
2. ICP Fit
3. Buying Signal
4. Priority
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from growx_crawl.core.enums import PriorityLevel
from growx_crawl.scoring.buying_signal import calculate_buying_signal
from growx_crawl.scoring.data_confidence import calculate_data_confidence
from growx_crawl.scoring.icp_fit import calculate_icp_fit


class CompanyScoreBreakdown(BaseModel):
    data_confidence: float = Field(ge=0.0, le=100.0)
    icp_fit: float = Field(ge=0.0, le=100.0)
    buying_signal: float = Field(ge=0.0, le=100.0)
    priority: PriorityLevel
    reasons: List[str] = Field(default_factory=list)


class ScoringService:
    """Canonical service boundary for evaluating multidimensional lead scores."""

    def score_company(
        self,
        company_data: Dict[str, Any],
        target_industry: Optional[str] = None,
        target_location: Optional[str] = None,
        signals: Optional[List[Dict[str, Any]]] = None,
    ) -> CompanyScoreBreakdown:
        conf_score, conf_reasons = calculate_data_confidence(company_data)
        icp_score, icp_reasons = calculate_icp_fit(company_data, target_industry, target_location)
        sig_score, sig_reasons = calculate_buying_signal(signals or [])

        # Priority evaluates multi-factor balance
        composite = (conf_score * 0.25) + (icp_score * 0.45) + (sig_score * 0.30)
        if composite >= 75.0 or (icp_score >= 80.0 and conf_score >= 60.0):
            priority = PriorityLevel.HIGH
        elif composite >= 50.0:
            priority = PriorityLevel.MEDIUM
        else:
            priority = PriorityLevel.LOW

        all_reasons = conf_reasons + icp_reasons + sig_reasons
        return CompanyScoreBreakdown(
            data_confidence=conf_score,
            icp_fit=icp_score,
            buying_signal=sig_score,
            priority=priority,
            reasons=all_reasons,
        )


scoring_service = ScoringService()
