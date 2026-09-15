from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class CrawlEvent(BaseModel):
    event: str
    job_id: str
    timestamp: str = Field(default_factory=utc_now_iso)
    data: Dict[str, Any] = Field(default_factory=dict)
