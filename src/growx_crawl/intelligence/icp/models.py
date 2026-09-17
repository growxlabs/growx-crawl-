"""
GrowX ICP Intelligence Models.
Defines Ideal Customer Profiles, versions, criteria, exclusions, personas, fit scores, and reason codes.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from growx_crawl.shared.time import utc_iso_now


class ICPType(str, Enum):
    SELLER_DERIVED = "seller_derived"
    PRODUCT_DERIVED = "product_derived"
    PROJECT_SPECIFIC = "project_specific"
    CAMPAIGN_SPECIFIC = "campaign_specific"
    MANUAL = "manual"
    HYBRID = "hybrid"


class ICPStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    SUPERSEDED = "superseded"


class CriterionCategory(str, Enum):
    FIRMOGRAPHIC = "firmographic"
    TECHNOGRAPHIC = "technographic"
    GEOGRAPHIC = "geographic"
    OPERATIONAL = "operational"
    SIGNAL = "signal"
    USE_CASE = "use_case"


class RequirementType(str, Enum):
    REQUIRED = "required"
    PREFERRED = "preferred"
    BOOST = "boost"
    NEUTRAL = "neutral"
    PENALTY = "penalty"
    EXCLUDE = "exclude"


class CriterionOperator(str, Enum):
    EQUALS = "equals"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    RANGE = "range"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    GTE = "greater_than_or_equal"
    LTE = "less_than_or_equal"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"
    CHANGED_WITHIN = "changed_within"



class ExclusionType(str, Enum):
    COMPETITOR = "competitor"
    EXISTING_CUSTOMER = "existing_customer"
    GEOGRAPHY = "geography"
    SIZE = "size"
    VERTICAL = "vertical"
    BAD_FIT = "bad_fit"


class FitStatus(str, Enum):
    EXCELLENT_FIT = "excellent_fit"
    STRONG_FIT = "strong_fit"
    POSSIBLE_FIT = "possible_fit"
    WEAK_FIT = "weak_fit"
    EXCLUDED = "excluded"
    INSUFFICIENT_DATA = "insufficient_data"


class PersonaCategory(str, Enum):
    ECONOMIC_BUYER = "economic_buyer"
    TECHNICAL_BUYER = "technical_buyer"
    OPERATIONAL_BUYER = "operational_buyer"
    CHAMPION = "champion"
    INFLUENCER = "influencer"
    USER = "user"
    BLOCKER = "blocker"


class ReasonCode(str, Enum):
    INDUSTRY_MATCH = "INDUSTRY_MATCH"
    SIZE_MATCH = "SIZE_MATCH"
    GEOGRAPHY_MATCH = "GEOGRAPHY_MATCH"
    TECH_MATCH = "TECH_MATCH"
    OPERATIONS_MATCH = "OPERATIONS_MATCH"
    RECENT_EXPANSION = "RECENT_EXPANSION"
    WRONG_GEOGRAPHY = "WRONG_GEOGRAPHY"
    TOO_SMALL = "TOO_SMALL"
    COMPETITOR_EXCLUDED = "COMPETITOR_EXCLUDED"
    EXISTING_CUSTOMER_EXCLUDED = "EXISTING_CUSTOMER_EXCLUDED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    MUST_HAVE_FAILED = "MUST_HAVE_FAILED"
    HARD_EXCLUSION = "HARD_EXCLUSION"
    PERSONA_TITLE_MATCH = "PERSONA_TITLE_MATCH"
    PERSONA_SENIORITY_MATCH = "PERSONA_SENIORITY_MATCH"


class ICPEntity(BaseModel):
    """Canonical Ideal Customer Profile parent container."""
    id: str
    seller_company_id: str
    name: str
    description: Optional[str] = None
    status: str = ICPStatus.DRAFT.value
    source_type: str = ICPType.SELLER_DERIVED.value
    current_version_id: Optional[str] = None
    created_at: str = Field(default_factory=utc_iso_now)
    updated_at: str = Field(default_factory=utc_iso_now)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class ICPVersionEntity(BaseModel):
    """Immutable, versioned targeting model."""
    id: str
    icp_id: str
    version: int = 1
    status: str = ICPStatus.DRAFT.value
    created_at: str = Field(default_factory=utc_iso_now)
    created_by: str = "system"
    seller_snapshot_id: Optional[str] = None
    policy_version: str = "v1"
    model_run_id: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class SellerSnapshotEntity(BaseModel):
    """Captures seller state and verified facts at the time of ICP generation."""
    id: str
    seller_company_id: str
    fact_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    verified_at: Optional[str] = None
    created_at: str = Field(default_factory=utc_iso_now)


class ICPCriterionEntity(BaseModel):
    """Individual targeting rule or preference within an ICP version."""
    id: str
    icp_version_id: str
    category: str = CriterionCategory.FIRMOGRAPHIC.value
    field: str
    operator: str = CriterionOperator.EQUALS.value
    value_json: Any
    weight: float = 1.0
    requirement_type: str = RequirementType.PREFERRED.value
    source: str = "seller_fact"
    confidence: float = 1.0
    created_at: str = Field(default_factory=utc_iso_now)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class ICPExclusionEntity(BaseModel):
    """Hard disqualification rule that overrides positive fit score."""
    id: str
    icp_version_id: str
    rule_type: str = ExclusionType.BAD_FIT.value
    field: str
    operator: str = CriterionOperator.EQUALS.value
    value_json: Any
    reason: str
    created_at: str = Field(default_factory=utc_iso_now)


class ICPPersonaEntity(BaseModel):
    """Decision maker or target persona within target accounts."""
    id: str
    icp_version_id: str
    name: str
    department: str
    seniority: str
    title_patterns: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    persona_category: str = PersonaCategory.TECHNICAL_BUYER.value
    priority: int = 1
    confidence: float = 1.0
    created_at: str = Field(default_factory=utc_iso_now)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class ICPCompanyScoreEntity(BaseModel):
    """Evaluated fit score and confidence for a company against an ICP version."""
    id: str
    icp_version_id: str
    company_id: str
    fit_score: float = 0.0
    data_confidence: float = 0.0
    status: str = FitStatus.POSSIBLE_FIT.value
    evaluated_at: str = Field(default_factory=utc_iso_now)
    valid_until: Optional[str] = None
    fingerprint: Optional[str] = None
    explanation_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class ICPPersonScoreEntity(BaseModel):
    """Evaluated fit score and persona alignment for a person inside a company."""
    id: str
    icp_version_id: str
    person_id: str
    company_id: str
    persona_id: Optional[str] = None
    fit_score: float = 0.0
    employment_confidence: float = 1.0
    role_matched: Optional[str] = None
    evaluated_at: str = Field(default_factory=utc_iso_now)
    explanation_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class ICPEvidenceEntity(BaseModel):
    """Source-backed evidence verifying why a criterion was established."""
    id: str
    icp_version_id: str
    criterion_id: Optional[str] = None
    source_type: str
    source_id: Optional[str] = None
    fact_id: Optional[str] = None
    evidence_id: Optional[str] = None
    confidence: float = 1.0
    created_at: str = Field(default_factory=utc_iso_now)
