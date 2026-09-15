import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from growx_crawl.core.enums import JobStatus


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class CrawlJob(BaseModel):
    id: str = Field(default_factory=lambda: f"job_{uuid.uuid4().hex[:12]}")
    query: str
    industry: Optional[str] = None
    location: Optional[str] = None
    status: JobStatus = JobStatus.QUEUED
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    discovered_count: int = 0
    processed_count: int = 0
    lead_count: int = 0
    duplicate_count: int = 0
    failure_count: int = 0
    configuration: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_now_iso)
