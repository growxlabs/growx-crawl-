"""
GrowX Prospect Ranking Models.
Defines canonical entities, score breakdown structures, status enums, and explainable reason codes.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from growx_crawl.shared.time import utc_iso_now


class RankingStatus(str, Enum):
    """Workflow status determining campaign prioritization and queue routing."""
    PRIORITY = "priority"
    STRONG = "strong"
    POSSIBLE = "possible"
    RESEARCH_MORE = "research_more"
    REVERIFY = "reverify"
    NOT_ELIGIBLE = "not_eligible"


class ProspectStatus(str, Enum):
    """Lifecycle status of a prospect account/contact."""
    CANDIDATE = "candidate"
    RANKED = "ranked"
    RESEARCHING = "researching"
    QUALIFIED = "qualified"
    REJECTED = "rejected"
    CAMPAIGN_READY = "campaign_ready"
    CONTACTED = "contacted"


class ScoreComponentType(str, Enum):
    """Individual dimension components comprising the composite ranking."""
    ACCOUNT = "account"
    PERSON = "person"
    SIGNAL = "signal"
    TIMING = "timing"
    CONTACTABILITY = "contactability"
    PENALTY = "penalty"


class RankingReasonCode(str, Enum):
    """Standardized machine-readable audit tags explaining priority ranking."""
    # Positive fit & identity drivers
    HIGH_ICP_FIT = "HIGH_ICP_FIT"
    STRONG_PERSONA_MATCH = "STRONG_PERSONA_MATCH"
    VERIFIED_COMPANY = "VERIFIED_COMPANY"
    CURRENT_EMPLOYMENT = "CURRENT_EMPLOYMENT"
    EMAIL_VALID = "EMAIL_VALID"
    # Signal & timing drivers
    RECENT_EXPANSION = "RECENT_EXPANSION"
    RECENT_LEADERSHIP_CHANGE = "RECENT_LEADERSHIP_CHANGE"
    ACTIVE_GROWTH_PATTERN = "ACTIVE_GROWTH_PATTERN"
    HIGH_INTENT_SIGNAL = "HIGH_INTENT_SIGNAL"
    TECH_ADOPTION = "TECH_ADOPTION"
    FUNDING_RAISED = "FUNDING_RAISED"
    # Contactability & penalties
    ROLE_MAILBOX_PENALTY = "ROLE_MAILBOX_PENALTY"
    CATCH_ALL_PENALTY = "CATCH_ALL_PENALTY"
    MISSING_EMAIL = "MISSING_EMAIL"
    WEAK_CONTACTABILITY = "WEAK_CONTACTABILITY"
    STALE_COMPANY_SIZE = "STALE_COMPANY_SIZE"
    STALE_EMPLOYMENT = "STALE_EMPLOYMENT"
    RECENTLY_CONTACTED = "RECENTLY_CONTACTED"
    # Hard blocks
    SUPPRESSED_CONTACT = "SUPPRESSED_CONTACT"
    INVALID_EMAIL = "INVALID_EMAIL"
    HARD_ICP_EXCLUSION = "HARD_ICP_EXCLUSION"
    IDENTITY_CONFLICT = "IDENTITY_CONFLICT"
    BLOCKED_QUALITY_GATE = "BLOCKED_QUALITY_GATE"
    COMPETITOR_EXCLUDED = "COMPETITOR_EXCLUDED"
    WRONG_GEOGRAPHY = "WRONG_GEOGRAPHY"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class ProspectEntity(BaseModel):
    """Canonical Prospect container associating a company and optional buyer person."""
    id: str
    project_id: str
    company_id: str
    person_id: Optional[str] = None
    icp_version_id: Optional[str] = None
    status: str = ProspectStatus.CANDIDATE.value
    created_at: str = Field(default_factory=utc_iso_now)
    updated_at: str = Field(default_factory=utc_iso_now)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class RankingProfileEntity(BaseModel):
    """Versioned ranking profile governing weight distribution and thresholds."""
    id: str
    name: str
    version: int = 1
    config_json: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    created_at: str = Field(default_factory=utc_iso_now)
    updated_at: str = Field(default_factory=utc_iso_now)


class ProspectScoreEntity(BaseModel):
    """Comprehensive multi-dimensional evaluated ranking result for a prospect."""
    id: str
    prospect_id: str
    company_id: str
    person_id: Optional[str] = None
    icp_version_id: Optional[str] = None
    ranking_profile_id: str
    account_score: float = 0.0
    person_score: float = 0.0
    signal_score: float = 0.0
    timing_score: float = 0.0
    quality_score: float = 0.0
    verification_score: float = 0.0
    contactability_score: float = 0.0
    penalty_score: float = 0.0
    raw_score: float = 0.0
    confidence_factor: float = 1.0
    final_score: float = 0.0
    status: str = RankingStatus.POSSIBLE.value
    rank_position: Optional[int] = None
    calculated_at: str = Field(default_factory=utc_iso_now)
    valid_until: Optional[str] = None
    fingerprint: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class ProspectScoreHistoryEntity(BaseModel):
    """Snapshot preserving historical score and rank state at evaluation time."""
    id: str
    prospect_id: str
    score_id: str
    ranking_profile_id: str
    rank_position: Optional[int] = None
    final_score: float
    status: str
    calculated_at: str = Field(default_factory=utc_iso_now)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class RankingExplanationEntity(BaseModel):
    """Atomic audit contribution explaining a specific factor's impact on rank."""
    id: str
    score_id: str
    reason_code: str
    component: str
    contribution: float
    direction: str = "positive"
    evidence_refs: List[str] = Field(default_factory=list)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


# --- Intermediate Calculation Payloads ---

class AccountScoreResult(BaseModel):
    score: float = 0.0
    icp_fit: float = 0.0
    verification_score: float = 0.0
    quality_score: float = 0.0
    momentum_score: float = 0.0
    reason_codes: List[str] = Field(default_factory=list)
    contributions: Dict[str, float] = Field(default_factory=dict)


class PersonScoreResult(BaseModel):
    score: float = 0.0
    persona_fit: float = 0.0
    seniority_score: float = 0.0
    role_relevance: float = 0.0
    employment_confidence: float = 1.0
    matched_role: Optional[str] = None
    reason_codes: List[str] = Field(default_factory=list)
    contributions: Dict[str, float] = Field(default_factory=dict)


class SignalScoreResult(BaseModel):
    score: float = 0.0
    active_signals_count: int = 0
    signals_evaluated: List[Dict[str, Any]] = Field(default_factory=list)
    reason_codes: List[str] = Field(default_factory=list)
    contributions: Dict[str, float] = Field(default_factory=dict)


class TimingScoreResult(BaseModel):
    score: float = 0.0
    recency_factor: float = 1.0
    decay_details: Dict[str, Any] = Field(default_factory=dict)
    reason_codes: List[str] = Field(default_factory=list)
    contributions: Dict[str, float] = Field(default_factory=dict)


class ContactabilityResult(BaseModel):
    score: float = 0.0
    is_suppressed: bool = False
    is_valid_email: bool = True
    email_type: str = "unknown"  # corporate, personal, role_mailbox, invalid
    reason_codes: List[str] = Field(default_factory=list)
    contributions: Dict[str, float] = Field(default_factory=dict)


class FreshnessResult(BaseModel):
    overall_freshness: float = 1.0
    fact_freshness_days: int = 0
    employment_freshness_days: int = 0
    is_stale_employment: bool = False
    is_stale_company: bool = False
    reason_codes: List[str] = Field(default_factory=list)
    penalties: float = 0.0


class HardBlockResult(BaseModel):
    is_blocked: bool = False
    reason_code: Optional[str] = None
    block_message: Optional[str] = None
