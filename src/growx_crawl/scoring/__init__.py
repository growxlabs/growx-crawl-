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
    ProspectRankingService,
    ScoringService,
    prospect_ranking_service,
    scoring_service,
)
from growx_crawl.scoring.models import (
    AccountScoreResult,
    ContactabilityResult,
    FreshnessResult,
    PersonScoreResult,
    ProspectEntity,
    ProspectScoreEntity,
    ProspectScoreHistoryEntity,
    ProspectStatus,
    RankingExplanationEntity,
    RankingProfileEntity,
    RankingReasonCode,
    RankingStatus,
    ScoreComponentType,
    SignalScoreResult,
    TimingScoreResult,
)
from growx_crawl.scoring.profiles import (
    BUILTIN_PROFILES,
    RankingProfileConfig,
    RankingProfileRegistry,
    profile_registry,
)
from growx_crawl.scoring.prospect_ranker import ProspectRanker
from growx_crawl.scoring.explain import RankingExplainer
from growx_crawl.scoring.repository import BaseRankingRepository, SqliteRankingRepository

__all__ = [
    # Legacy exports
    "LeadScorer",
    "calculate_data_confidence",
    "calculate_icp_fit",
    "calculate_buying_signal",
    "CompanyScoreBreakdown",
    "ScoringService",
    "scoring_service",
    # Phase 13 Ranking exports
    "RankingStatus",
    "ProspectStatus",
    "ScoreComponentType",
    "RankingReasonCode",
    "ProspectEntity",
    "RankingProfileEntity",
    "ProspectScoreEntity",
    "ProspectScoreHistoryEntity",
    "RankingExplanationEntity",
    "AccountScoreResult",
    "PersonScoreResult",
    "SignalScoreResult",
    "TimingScoreResult",
    "ContactabilityResult",
    "FreshnessResult",
    "RankingProfileConfig",
    "RankingProfileRegistry",
    "profile_registry",
    "BUILTIN_PROFILES",
    "ProspectRanker",
    "RankingExplainer",
    "BaseRankingRepository",
    "SqliteRankingRepository",
    "ProspectRankingService",
    "prospect_ranking_service",
]

