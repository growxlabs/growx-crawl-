"""
GrowX Intelligence History Package.
"""

from growx_crawl.intelligence.history.change_detector import ChangeDetector, detect_value_change
from growx_crawl.intelligence.history.models import (
    BackfillRunEntity,
    BackfillStatus,
    ChangeEventType,
    CompanyTemporalSummary,
    CompanyTrendSummary,
    Significance,
    TimelineEventEntity,
    TrendEntity,
    TrendType,
    TrendWindow,
)
from growx_crawl.intelligence.history.policies import ChangePolicy, PolicyRegistry
from growx_crawl.intelligence.history.repository import (
    BaseHistoricalRepository,
    SqliteHistoricalRepository,
)
from growx_crawl.intelligence.history.service import (
    HistoricalIntelligenceService,
    history_service,
)
from growx_crawl.intelligence.history.significance import SignificanceEngine
from growx_crawl.intelligence.history.timelines import TimelineBuilder
from growx_crawl.intelligence.history.trends import TrendEngine

# Backward-compatible aliases
HistoryService = HistoricalIntelligenceService

__all__ = [
    "ChangeDetector",
    "detect_value_change",
    "ChangeEventType",
    "Significance",
    "TrendType",
    "TrendWindow",
    "BackfillStatus",
    "TimelineEventEntity",
    "TrendEntity",
    "CompanyTemporalSummary",
    "CompanyTrendSummary",
    "BackfillRunEntity",
    "ChangePolicy",
    "PolicyRegistry",
    "BaseHistoricalRepository",
    "SqliteHistoricalRepository",
    "HistoricalIntelligenceService",
    "HistoryService",
    "history_service",
    "SignificanceEngine",
    "TimelineBuilder",
    "TrendEngine",
]
