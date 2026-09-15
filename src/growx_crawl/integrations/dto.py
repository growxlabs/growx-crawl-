import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class GrowXLabsContactPayload(BaseModel):
    name: str
    title: Optional[str] = None
    decision_maker_tier: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None


class GrowXLabsLeadPayload(BaseModel):
    external_reference: str
    company_name: str
    industry: Optional[str] = None
    category: Optional[str] = None

    website: Optional[str] = None
    domain: Optional[str] = None

    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

    phone: Optional[str] = None
    email: Optional[str] = None
    whatsapp: Optional[str] = None

    instagram: Optional[str] = None
    linkedin: Optional[str] = None

    primary_contact: Optional[GrowXLabsContactPayload] = None
    products_services: List[str] = Field(default_factory=list)
    research_summary: Optional[str] = None

    lead_score: int = 0
    priority: str = "Low"
    score_reasons: List[str] = Field(default_factory=list)

    data_completeness_pct: int = 0
    contactability_score_pct: int = 0

    source: str = "growx-crawl"
    source_url: Optional[str] = None
    collected_at: str = Field(default_factory=utc_now_iso)


class GrowXLabsIngestionEnvelope(BaseModel):
    schema_version: str = "1"
    source: str = "growx-crawl"
    crawl_job_id: str
    batch_index: int = 1
    batch_count: int = 1
    idempotency_key: str = Field(default_factory=lambda: f"idemp_{uuid.uuid4().hex[:12]}")
    submitted_at: str = Field(default_factory=utc_now_iso)
    leads: List[GrowXLabsLeadPayload] = Field(default_factory=list)
