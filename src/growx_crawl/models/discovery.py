import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class DiscoveryCandidate(BaseModel):
    id: str = Field(default_factory=lambda: f"dsc_{uuid.uuid4().hex[:12]}")
    job_id: str
    company_name: Optional[str] = None
    domain: Optional[str] = None
    website: Optional[str] = None
    url: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    category: Optional[str] = None
    source: str = "discovery"
    source_url: Optional[str] = None
    external_id: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    discovered_from: List[str] = Field(default_factory=list)
    query_variant: Optional[str] = None
    website_missing: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_now_iso)
