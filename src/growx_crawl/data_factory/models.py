"""
GrowX Data Factory Models.
Defines entity models, plans, checkpoints, failed job dead-letters,
and morning intelligence summaries for Phase 09.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from growx_crawl.shared.time import utc_iso_now


class RunType(str, Enum):
    NIGHTLY = "nightly"
    MANUAL = "manual"
    BACKFILL = "backfill"
    REFRESH = "refresh"
    TARGETED = "targeted"
    REPROCESS = "reprocess"


class RunStatus(str, Enum):
    PLANNED = "planned"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FactoryStage(str, Enum):
    PLAN = "plan"
    DISCOVERY = "discovery"
    CRAWL = "crawl"
    EXTRACT = "extract"
    RESOLVE = "resolve"
    FACTS = "facts"
    VERIFY = "verify"
    QUALITY = "quality"
    HISTORY = "history"
    INDEX = "index"
    COMPLETE = "complete"


class PriorityTier(str, Enum):
    P0 = "P0"  # Active GTM campaign
    P1 = "P1"  # High-value stale
    P2 = "P2"  # New discovery
    P3 = "P3"  # Background refresh
    P4 = "P4"  # Low-value archive


class CrawlMode(str, Enum):
    LIGHT = "light"          # Homepage, about, contact
    STANDARD = "standard"    # Core company pages, team, offerings, careers
    DEEP = "deep"            # Broader recursive site crawl
    REFRESH = "refresh"      # Only evidence required for stale facts


class TargetSegment(BaseModel):
    name: str
    industry_terms: List[str] = Field(default_factory=list)
    geo_terms: List[str] = Field(default_factory=list)
    company_size_hints: List[str] = Field(default_factory=list)
    search_queries: List[str] = Field(default_factory=list)
    crawl_depth: int = 2
    priority: PriorityTier = PriorityTier.P1


class DataFactoryPlan(BaseModel):
    id: str
    version: str = "v1"
    run_type: RunType = RunType.NIGHTLY
    target_segments: List[TargetSegment] = Field(default_factory=list)
    discovery_sources: List[str] = Field(default_factory=lambda: ["search", "seed", "expansion"])
    max_companies: int = 500
    max_pages: int = 1000
    max_browser_sessions: int = 50
    max_runtime_minutes: int = 480
    refresh_budget: int = 200
    ai_budget: float = 10.0
    verification_budget: float = 5.0
    crawl_mode: CrawlMode = CrawlMode.STANDARD
    priority_rules: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_iso_now)


class DataFactoryRun(BaseModel):
    id: str
    run_type: RunType
    status: RunStatus
    started_at: str = Field(default_factory=utc_iso_now)
    completed_at: Optional[str] = None
    plan_version: str = "v1"
    checkpoint: FactoryStage = FactoryStage.PLAN
    discovery_count: int = 0
    crawl_count: int = 0
    entity_count: int = 0
    verification_count: int = 0
    quality_pass_count: int = 0
    error_count: int = 0
    estimated_cost: float = 0.0
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class DataFactoryCheckpoint(BaseModel):
    run_id: str
    stage: FactoryStage
    cursor: Optional[str] = None
    status: str = "in_progress"  # in_progress, completed, failed
    processed_count: int = 0
    failed_count: int = 0
    updated_at: str = Field(default_factory=utc_iso_now)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class FailedJob(BaseModel):
    id: str
    run_id: str
    stage: FactoryStage
    subject_id: Optional[str] = None
    error_code: str
    attempts: int = 1
    last_error: Optional[str] = None
    created_at: str = Field(default_factory=utc_iso_now)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class MorningSummary(BaseModel):
    run_id: str
    started_at: str
    completed_at: str
    queries_run: int = 0
    new_domains: int = 0
    companies_created: int = 0
    companies_updated: int = 0
    people_created: int = 0
    facts_added: int = 0
    facts_changed: int = 0
    verified_companies: int = 0
    quality_trusted_entities: int = 0
    errors: int = 0
    estimated_cost: float = 0.0
    cost_per_company: float = 0.0
    report_markdown: str = ""
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class StageProgressEvent(BaseModel):
    run_id: str
    stage: FactoryStage
    status: str
    processed: int = 0
    total: int = 0
    message: str = ""
    timestamp: str = Field(default_factory=utc_iso_now)
