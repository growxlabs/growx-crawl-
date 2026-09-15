import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ObservedFact(BaseModel):
    id: str = Field(default_factory=lambda: f"fct_{uuid.uuid4().hex[:12]}")
    company_id: str
    key: str
    value: Any
    source_url: str
    confidence: float = 1.0
    extraction_type: str = "text"
    observed_at: str = Field(default_factory=utc_now_iso)


class Location(BaseModel):
    id: str = Field(default_factory=lambda: f"loc_{uuid.uuid4().hex[:12]}")
    company_id: str
    name: Optional[str] = None
    address: str
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    source_url: str
    is_primary: bool = False
    confidence: float = 1.0
    created_at: str = Field(default_factory=utc_now_iso)


class BDELeadBrief(BaseModel):
    company_name: str
    industry: Optional[str] = None
    category: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    website: Optional[str] = None
    website_missing: bool = False
    description: Optional[str] = None

    primary_phone: Optional[str] = None
    primary_email: Optional[str] = None
    whatsapp: Optional[str] = None

    instagram: Optional[str] = None
    linkedin: Optional[str] = None
    facebook: Optional[str] = None

    primary_decision_maker: Optional[str] = None
    decision_maker_role: Optional[str] = None
    decision_maker_tier: Optional[str] = None
    decision_maker_confidence: float = 0.0

    products_services: List[str] = Field(default_factory=list)
    observed_signals: Dict[str, Any] = Field(default_factory=dict)
    prospect_flags: List[str] = Field(default_factory=list)

    lead_score: int = 0
    priority: str = "Low"
    score_breakdown: Dict[str, int] = Field(default_factory=dict)
    score_reasons: List[str] = Field(default_factory=list)

    data_completeness_pct: int = 0
    contactability_score_pct: int = 0
    research_summary: str = ""
    source: str = "crawl"
    source_url: str = ""
    confidence: float = 1.0
    collected_at: str = Field(default_factory=utc_now_iso)
