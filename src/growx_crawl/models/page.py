import uuid
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class FetchedPage(BaseModel):
    id: str = Field(default_factory=lambda: f"pg_{uuid.uuid4().hex[:12]}")
    job_id: str
    target_id: str
    url: str
    status_code: int = 200
    content_type: str = "text/html"
    html_content: str = ""
    title: Optional[str] = None
    text_content: Optional[str] = None
    created_at: str = Field(default_factory=utc_now_iso)
