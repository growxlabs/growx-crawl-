from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CompanyAnalysis(BaseModel):
    domain: str
    company_name: str
    tagline: str = ""
    summary: str = ""
    primary_offer: str = ""
    value_proposition: str = ""
    target_audience: List[str] = Field(default_factory=list)
    features: List[str] = Field(default_factory=list)
    pricing_model: str = "Subscription / Custom"
    tech_stack: List[str] = Field(default_factory=list)
    recent_announcements: List[str] = Field(default_factory=list)
    crawled_pages_count: int = 1


class ICPProfile(BaseModel):
    target_industries: List[str] = Field(default_factory=list)
    company_size: List[str] = Field(default_factory=list)
    target_roles: List[str] = Field(default_factory=list)
    geographies: List[str] = Field(default_factory=list)
    pain_points: List[str] = Field(default_factory=list)
    trigger_events: List[str] = Field(default_factory=list)
    search_dorks: List[str] = Field(default_factory=list)


class OutreachSequence(BaseModel):
    email_subject: str
    email_body: str
    email_followup_1: str
    email_followup_2: str
    linkedin_note: str
    twitter_dm: str


class ProspectLead(BaseModel):
    id: str
    name: str
    first_name: str
    last_name: str
    title: str
    company_name: str
    company_domain: str
    email: Optional[str] = None
    email_status: str = "verified"  # verified, catch_all, risky, unverified
    email_confidence: int = 95
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    location: Optional[str] = "United States"
    relevance_score: int = 90
    personalization_hook: str = ""
    outreach: Optional[OutreachSequence] = None
    canonical_company_id: Optional[str] = None
    canonical_domain_id: Optional[str] = None
    canonical_person_id: Optional[str] = None
    verification_gate_decision: Optional[str] = None
    verification_status: Optional[str] = None


class AutoGTMResult(BaseModel):
    run_id: str
    domain: str
    created_at: str
    analysis: CompanyAnalysis
    icp: ICPProfile
    leads: List[ProspectLead] = Field(default_factory=list)
    stats: Dict[str, Any] = Field(default_factory=dict)
