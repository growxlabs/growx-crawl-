"""
GrowX Continuous Data Factory Subsystem.
Operationalizes GrowX as a continuous, compounding data production system
that discovers, crawls, resolves, verifies, quality-checks, tracks history,
and indexes source-backed company/person intelligence.
"""

from growx_crawl.data_factory.checkpoints import CheckpointManager
from growx_crawl.data_factory.metrics import DataFactoryMetrics
from growx_crawl.data_factory.models import (
    CrawlMode,
    DataFactoryCheckpoint,
    DataFactoryPlan,
    DataFactoryRun,
    FactoryStage,
    FailedJob,
    MorningSummary,
    PriorityTier,
    RunStatus,
    RunType,
    StageProgressEvent,
    TargetSegment,
)
from growx_crawl.data_factory.pipeline import DataFactoryPipeline
from growx_crawl.data_factory.planner import DataFactoryPlanner
from growx_crawl.data_factory.prioritization import CrawlPrioritizer
from growx_crawl.data_factory.quotas import BudgetGuard
from growx_crawl.data_factory.refresh import RefreshPlanner
from growx_crawl.data_factory.repository import (
    DataFactoryRepository,
    InMemoryDataFactoryRepository,
    SqliteDataFactoryRepository,
)
from growx_crawl.data_factory.scheduler import DataFactoryScheduler, factory_scheduler
from growx_crawl.data_factory.service import DataFactoryService, data_factory_service
from growx_crawl.data_factory.stages import (
    CrawlStage,
    DiscoverStage,
    ExtractStage,
    FactsStage,
    HistoryStage,
    IndexStage,
    QualityStage,
    ResolveStage,
    VerifyStage,
)

__all__ = [
    # Facade
    "DataFactoryService",
    "data_factory_service",
    # Enums & Models
    "RunType",
    "RunStatus",
    "FactoryStage",
    "PriorityTier",
    "CrawlMode",
    "TargetSegment",
    "DataFactoryPlan",
    "DataFactoryRun",
    "DataFactoryCheckpoint",
    "FailedJob",
    "MorningSummary",
    "StageProgressEvent",
    # Components
    "DataFactoryPipeline",
    "DataFactoryPlanner",
    "CheckpointManager",
    "BudgetGuard",
    "CrawlPrioritizer",
    "RefreshPlanner",
    "DataFactoryMetrics",
    "DataFactoryScheduler",
    "factory_scheduler",
    # Repositories
    "DataFactoryRepository",
    "InMemoryDataFactoryRepository",
    "SqliteDataFactoryRepository",
    # Stages
    "DiscoverStage",
    "CrawlStage",
    "ExtractStage",
    "ResolveStage",
    "FactsStage",
    "VerifyStage",
    "QualityStage",
    "HistoryStage",
    "IndexStage",
]
