import uuid
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field
from growx_crawl.core.enums import MatchDecision, PriorityLevel


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Email(BaseModel):
    id: str = Field(default_factory=lambda: f"eml_{uuid.uuid4().hex[:12]}")
    company_id: str
    email: str
    normalized_email: str
    is_generic: bool = False
    source_url: str
    created_at: str = Field(default_factory=utc_now_iso)


class Phone(BaseModel):
    id: str = Field(default_factory=lambda: f"phn_{uuid.uuid4().hex[:12]}")
    company_id: str
    phone: str
    normalized_phone: str
    raw_phone: str
    country_code: Optional[str] = None
    source_url: str
    created_at: str = Field(default_factory=utc_now_iso)


class SocialProfile(BaseModel):
    id: str = Field(default_factory=lambda: f"soc_{uuid.uuid4().hex[:12]}")
    company_id: str
    platform: str  # instagram, linkedin, facebook, youtube, whatsapp
    url: str
    normalized_url: str
    handle: Optional[str] = None
    source_url: str
    created_at: str = Field(default_factory=utc_now_iso)


class Contact(BaseModel):
    id: str = Field(default_factory=lambda: f"cnt_{uuid.uuid4().hex[:12]}")
    company_id: str
    job_id: str
    name: str
    title: Optional[str] = None
    decision_maker_tier: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    source_url: str
    confidence: float = 1.0
    created_at: str = Field(default_factory=utc_now_iso)


class Company(BaseModel):
    id: str = Field(default_factory=lambda: f"cmp_{uuid.uuid4().hex[:12]}")
    job_id: str
    name: str
    normalized_name: str
    domain: str
    website: str
    industry: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    source: str = "crawl"
    source_url: str
    confidence: float = 1.0
    discovered_from: List[str] = Field(default_factory=list)
    query_variant: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    website_missing: bool = False
    review_status: str = "pending"
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)

    # In-memory relationships
    emails: List[Email] = Field(default_factory=list)
    phones: List[Phone] = Field(default_factory=list)
    social_profiles: List[SocialProfile] = Field(default_factory=list)
    contacts: List[Contact] = Field(default_factory=list)


class LeadCandidate(BaseModel):
    id: str = Field(default_factory=lambda: f"led_{uuid.uuid4().hex[:12]}")
    company_id: str
    job_id: str
    score: int
    priority: PriorityLevel
    score_reasons: List[str] = Field(default_factory=list)
    status: str = "new"
    created_at: str = Field(default_factory=utc_now_iso)


class DedupeRecord(BaseModel):
    id: str = Field(default_factory=lambda: f"ddp_{uuid.uuid4().hex[:12]}")
    canonical_company_id: str
    duplicate_company_id: str
    match_signals: List[str]
    confidence: float
    decision: MatchDecision
    created_at: str = Field(default_factory=utc_now_iso)
