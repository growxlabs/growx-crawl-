from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class CompanyEntity(BaseModel):
    id: str
    canonical_name: str
    legal_name: Optional[str] = None
    normalized_name: str
    primary_domain_id: Optional[str] = None
    industry: Optional[str] = None
    employee_range: Optional[str] = None
    country_code: Optional[str] = None
    summary: Optional[str] = None
    status: str = "active"
    first_seen_at: str = Field(default_factory=utc_now_iso)
    last_seen_at: str = Field(default_factory=utc_now_iso)
    last_crawled_at: Optional[str] = None
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class CompanyAliasEntity(BaseModel):
    id: str
    company_id: str
    alias: str
    normalized_alias: str
    source_id: Optional[str] = None
    first_seen_at: str = Field(default_factory=utc_now_iso)
    last_seen_at: str = Field(default_factory=utc_now_iso)


class DomainEntity(BaseModel):
    id: str
    registrable_domain: str
    hostname: str
    normalized_domain: str  # UNIQUE
    scheme: str = "https"
    status: str = "active"
    first_seen_at: str = Field(default_factory=utc_now_iso)
    last_seen_at: str = Field(default_factory=utc_now_iso)
    last_crawled_at: Optional[str] = None
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class CompanyDomainEntity(BaseModel):
    company_id: str
    domain_id: str
    relationship_type: str = "primary"
    confidence: float = 1.0
    is_primary: bool = True
    first_seen_at: str = Field(default_factory=utc_now_iso)
    last_verified_at: Optional[str] = None


class PersonEntity(BaseModel):
    id: str
    full_name: str
    normalized_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    headline: Optional[str] = None
    location_text: Optional[str] = None
    first_seen_at: str = Field(default_factory=utc_now_iso)
    last_seen_at: str = Field(default_factory=utc_now_iso)
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class EmploymentEntity(BaseModel):
    id: str
    person_id: str
    company_id: str
    title: str
    normalized_title: str
    department: Optional[str] = None
    seniority: Optional[str] = None
    is_current: bool = True
    source_id: Optional[str] = None
    confidence: float = 1.0
    first_seen_at: str = Field(default_factory=utc_now_iso)
    last_seen_at: str = Field(default_factory=utc_now_iso)
    last_verified_at: Optional[str] = None


class SourceEntity(BaseModel):
    id: str
    source_type: str
    url: str
    domain_id: Optional[str] = None
    content_hash: Optional[str] = None
    observed_at: str = Field(default_factory=utc_now_iso)
    created_at: str = Field(default_factory=utc_now_iso)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class CrawlJobEntity(BaseModel):
    id: str
    target: str
    status: str = "pending"
    config_json: Dict[str, Any] = Field(default_factory=dict)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    attempts: int = 1
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class CrawlRunEntity(BaseModel):
    id: str
    job_id: str
    target_url: str
    domain_id: Optional[str] = None
    fetcher_type: str = "fast"
    http_status: Optional[int] = 200
    started_at: str = Field(default_factory=utc_now_iso)
    completed_at: Optional[str] = None
    duration_ms: Optional[int] = None
    page_count: int = 1
    success: bool = True
    error_code: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
