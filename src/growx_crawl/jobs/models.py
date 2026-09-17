"""
Persistent Job Queue and Worker Domain Models.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from growx_crawl.shared.ids import generate_id


class PersistentJobStatus(str, Enum):
    QUEUED = "queued"
    CLAIMED = "claimed"
    RUNNING = "running"
    RETRYING = "retrying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PersistentJobType(str, Enum):
    CRAWL_BATCH = "crawl_batch"
    BROWSER_RENDER = "browser_render"
    SCREENSHOT = "screenshot"
    ENTITY_RESOLUTION = "entity_resolution"
    FACT_EXTRACTION = "fact_extraction"
    ICP_EVALUATION = "icp_evaluation"
    PROSPECT_RANKING = "prospect_ranking"
    VERIFY_COMPANY = "verify_company"
    VERIFY_PERSON = "verify_person"
    VERIFY_DOMAIN = "verify_domain"
    VERIFY_FACTS = "verify_facts"
    NIGHTLY_RUN = "nightly_run"
    CUSTOM = "custom"


class WorkerType(str, Enum):
    CRAWLER = "crawler"
    BROWSER = "browser"
    INTELLIGENCE = "intelligence"
    VERIFICATION = "verification"
    COORDINATOR = "coordinator"


class WorkerStatus(str, Enum):
    ACTIVE = "active"
    BUSY = "busy"
    IDLE = "idle"
    OFFLINE = "offline"
    DRAINING = "draining"


class JobEntity(BaseModel):
    id: str = Field(default_factory=lambda: generate_id("job"))
    job_type: str
    status: PersistentJobStatus = PersistentJobStatus.QUEUED
    priority: int = 50
    payload_json: Dict[str, Any] = Field(default_factory=dict)
    result_json: Dict[str, Any] = Field(default_factory=dict)
    claimed_by_worker_id: Optional[str] = None
    claimed_at: Optional[str] = None
    lease_expires_at: Optional[str] = None
    heartbeat_at: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    failure_reason: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class WorkerEntity(BaseModel):
    id: str = Field(default_factory=lambda: generate_id("wrk"))
    worker_type: str
    hostname: str = "localhost"
    process_id: Optional[int] = None
    status: WorkerStatus = WorkerStatus.ACTIVE
    current_job_id: Optional[str] = None
    version: str = "1.0.0"
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_heartbeat_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
