"""
GrowX Historical Intelligence Models.
Timeline events, trends, temporal summaries, and backfill tracking.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from growx_crawl.shared.time import utc_iso_now


class ChangeEventType(str, Enum):
    FACT_CREATED = "fact_created"
    FACT_CHANGED = "fact_changed"
    FACT_REMOVED = "fact_removed"
    FACT_REAPPEARED = "fact_reappeared"
    RELATIONSHIP_STARTED = "relationship_started"
    RELATIONSHIP_ENDED = "relationship_ended"
    TECHNOLOGY_ADDED = "technology_added"
    TECHNOLOGY_REMOVED = "technology_removed"
    LOCATION_ADDED = "location_added"
    LOCATION_REMOVED = "location_removed"
    EMPLOYMENT_STARTED = "employment_started"
    EMPLOYMENT_ENDED = "employment_ended"
    PRODUCT_ADDED = "product_added"
    PRODUCT_REMOVED = "product_removed"
    DOMAIN_CHANGED = "domain_changed"
    INTERPRETATION_REVISED = "interpretation_revised"


class Significance(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TrendType(str, Enum):
    EMPLOYEE_GROWTH = "employee_growth"
    HIRING_GROWTH = "hiring_growth"
    LOCATION_EXPANSION = "location_expansion"
    TECHNOLOGY_CHANGE_RATE = "technology_change_rate"
    LEADERSHIP_CHANGE_RATE = "leadership_change_rate"
    PRODUCT_EXPANSION = "product_expansion"


class TrendWindow(str, Enum):
    D30 = "30d"
    D90 = "90d"
    D180 = "180d"
    D365 = "365d"


class BackfillStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class TimelineEventEntity(BaseModel):
    """Core timeline event capturing a single meaningful change for an entity."""
    id: str
    entity_type: str  # company, person, domain, location
    entity_id: str
    event_type: str  # ChangeEventType value
    occurred_at: str  # when the change actually happened (best estimate)
    detected_at: str = Field(default_factory=utc_iso_now)
    source_id: Optional[str] = None
    fact_id: Optional[str] = None
    observation_id: Optional[str] = None
    evidence_ids: List[str] = Field(default_factory=list)
    predicate: Optional[str] = None
    previous_value_json: Dict[str, Any] = Field(default_factory=dict)
    new_value_json: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0
    verification_state: str = "unverified"
    significance: str = "medium"  # Significance value
    fingerprint: str = ""  # stable hash for idempotency
    extractor_version: Optional[str] = None
    policy_version: str = "v1"
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class TrendEntity(BaseModel):
    """Derived temporal trend for an entity over a time window."""
    id: str
    entity_type: str
    entity_id: str
    trend_type: str  # TrendType value
    window_start: str
    window_end: str
    value_json: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0
    calculation_version: str = "v1"
    source_fact_ids: List[str] = Field(default_factory=list)
    derived: bool = True
    created_at: str = Field(default_factory=utc_iso_now)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class CompanyTemporalSummary(BaseModel):
    """Denormalized current temporal summary for search integration."""
    company_id: str
    last_change_at: Optional[str] = None
    change_count_30d: int = 0
    change_count_90d: int = 0
    latest_signal_type: Optional[str] = None
    latest_signal_at: Optional[str] = None
    updated_at: str = Field(default_factory=utc_iso_now)


class CompanyTrendSummary(BaseModel):
    """Denormalized trend summary for quick lookup."""
    company_id: str
    employee_growth_90d: Optional[float] = None
    employee_growth_365d: Optional[float] = None
    leadership_changes_180d: int = 0
    location_growth_365d: int = 0
    technology_changes_180d: int = 0
    updated_at: str = Field(default_factory=utc_iso_now)


class BackfillRunEntity(BaseModel):
    """Tracks a historical backfill operation."""
    id: str
    entity_type: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    status: str = "running"  # BackfillStatus value
    processed_count: int = 0
    error_count: int = 0
    last_cursor: Optional[str] = None
    created_at: str = Field(default_factory=utc_iso_now)
    completed_at: Optional[str] = None
