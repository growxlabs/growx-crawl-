import uuid
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field
from growx_crawl.core.enums import TargetStatus


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class CrawlTarget(BaseModel):
    id: str = Field(default_factory=lambda: f"tgt_{uuid.uuid4().hex[:12]}")
    job_id: str
    url: str
    domain: str
    source: str = "discovery"
    status: TargetStatus = TargetStatus.QUEUED
    depth: int = 0
    retry_count: int = 0
    last_error: Optional[str] = None
    discovered_at: str = Field(default_factory=utc_now_iso)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
