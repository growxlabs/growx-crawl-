"""
GrowX Competitor Graph Models.
Defines competitive profiles, relationships, evidence, rejections, and summaries.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from growx_crawl.shared.time import utc_iso_now


class RelationshipType(str, Enum):
    DIRECT = "direct"
    ADJACENT = "adjacent"
    SUBSTITUTE = "substitute"
    EMERGING = "emerging"
    REGIONAL = "regional"
    PRODUCT_LEVEL = "product_level"
    UNKNOWN = "unknown"


class RelationshipStatus(str, Enum):
    CANDIDATE = "candidate"
    SUPPORTED = "supported"
    VERIFIED = "verified"
    UNCERTAIN = "uncertain"
    REJECTED = "rejected"
    STALE = "stale"
    HISTORICAL = "historical"


class EvidenceType(str, Enum):
    SHARED_OFFERING = "shared_offering"
    SHARED_MARKET = "shared_market"
    COMPARISON_PAGE = "comparison_page"
    ALTERNATIVE_PAGE = "alternative_page"
    SEARCH_COOCCURRENCE = "search_cooccurrence"
    CUSTOMER_OVERLAP = "customer_overlap"
    REVIEW_PLATFORM = "review_platform"
    EXPLICIT_COMPETITOR_MENTION = "explicit_competitor_mention"
    ANALYST_REPORT = "analyst_report"


class ReasonCode(str, Enum):
    SAME_MARKET = "SAME_MARKET"
    SAME_CUSTOMER_SEGMENT = "SAME_CUSTOMER_SEGMENT"
    OFFERING_OVERLAP = "OFFERING_OVERLAP"
    GEOGRAPHY_OVERLAP = "GEOGRAPHY_OVERLAP"
    EXPLICIT_COMPARISON = "EXPLICIT_COMPARISON"
    PARENT_RELATIONSHIP_CONFLICT = "PARENT_RELATIONSHIP_CONFLICT"
    CUSTOMER_RELATIONSHIP_CONFLICT = "CUSTOMER_RELATIONSHIP_CONFLICT"
    SUPPLIER_RELATIONSHIP_CONFLICT = "SUPPLIER_RELATIONSHIP_CONFLICT"
    DIFFERENT_GEOGRAPHY_NO_REMOTE = "DIFFERENT_GEOGRAPHY_NO_REMOTE"


class CompetitiveProfile(BaseModel):
    """Derived competitive profile for a company based on verified facts and identity."""
    company_id: str
    company_name: str
    industries: List[str] = Field(default_factory=list)
    products: List[str] = Field(default_factory=list)
    services: List[str] = Field(default_factory=list)
    target_customers: List[str] = Field(default_factory=list)
    company_size: Optional[str] = None
    geographies: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    positioning_terms: List[str] = Field(default_factory=list)
    buying_problems: List[str] = Field(default_factory=list)
    pricing_motion: Optional[str] = None
    data_quality_score: float = 1.0
    created_at: str = Field(default_factory=utc_iso_now)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class CompetitorRelationshipEntity(BaseModel):
    """Represents a directional or symmetric competitive edge between two companies."""
    id: str
    company_id: str
    competitor_company_id: str
    canonical_pair: str
    relationship_type: str = RelationshipType.UNKNOWN.value
    status: str = RelationshipStatus.CANDIDATE.value
    confidence: float = 0.0
    strength: float = 0.0
    market_overlap: float = 0.0
    offering_overlap: float = 0.0
    customer_overlap: float = 0.0
    geography_overlap: float = 0.0
    evidence_count: int = 0
    first_seen_at: str = Field(default_factory=utc_iso_now)
    last_seen_at: str = Field(default_factory=utc_iso_now)
    last_verified_at: Optional[str] = None
    valid_until: Optional[str] = None
    scoring_version: str = "v1"
    policy_version: str = "v1"
    reasons: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_iso_now)
    updated_at: str = Field(default_factory=utc_iso_now)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class CompetitorEvidenceEntity(BaseModel):
    """Source-backed evidence verifying or supporting a competitive relationship."""
    id: str
    relationship_id: str
    source_id: Optional[str] = None
    fact_id: Optional[str] = None
    observation_id: Optional[str] = None
    object_ref_id: Optional[str] = None
    evidence_type: str = EvidenceType.SHARED_OFFERING.value
    support_type: str = "positive"  # positive, neutral, negative
    captured_at: str = Field(default_factory=utc_iso_now)
    confidence: float = 1.0
    created_at: str = Field(default_factory=utc_iso_now)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class CompetitorRejectionEntity(BaseModel):
    """Persisted record of an evaluated and explicitly rejected competitor pair."""
    canonical_pair: str
    company_a: str
    company_b: str
    reason_code: str
    rejected_at: str = Field(default_factory=utc_iso_now)
    policy_version: str = "v1"
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class CompanyCompetitorSummary(BaseModel):
    """Denormalized competitor intelligence summary for fast GTM lookups."""
    company_id: str
    top_competitor_ids: List[str] = Field(default_factory=list)
    competitor_count: int = 0
    verified_competitor_count: int = 0
    last_refreshed_at: Optional[str] = None
    updated_at: str = Field(default_factory=utc_iso_now)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
