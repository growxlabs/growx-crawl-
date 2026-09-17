"""
GrowX Scoring Package.
Maintains separated scores for data confidence, ICP fit, buying signal, and priority.
"""

from growx_crawl.scoring.scorer import LeadScorer
from growx_crawl.scoring.data_confidence import calculate_data_confidence
from growx_crawl.scoring.icp_fit import calculate_icp_fit
from growx_crawl.scoring.buying_signal import calculate_buying_signal
from growx_crawl.scoring.service import (
    CompanyScoreBreakdown,
    ScoringService,
    scoring_service,
)

__all__ = [
    "LeadScorer",
    "calculate_data_confidence",
    "calculate_icp_fit",
    "calculate_buying_signal",
    "CompanyScoreBreakdown",
    "ScoringService",
    "scoring_service",
]
