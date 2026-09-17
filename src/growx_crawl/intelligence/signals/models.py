"""
GrowX Intelligence Signals Models.
Signal entities and signal candidate entities for GTM signal detection.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from growx_crawl.shared.time import utc_iso_now


class SignalType(str, Enum):
    HIRING_GROWTH = "hiring_growth"
    LEADERSHIP_CHANGE = "leadership_change"
    LOCATION_EXPANSION = "location_expansion"
    TECHNOLOGY_ADOPTION = "technology_adoption"
    TECHNOLOGY_REMOVAL = "technology_removal"
    PRODUCT_LAUNCH = "product_launch"
    MARKET_EXPANSION = "market_expansion"
    OPERATIONAL_EXPANSION = "operational_expansion"
    FUNDING_RAISED = "funding_raised"
    TECH_STACK_ACTIVE = "tech_stack_active"


class SignalCandidateStatus(str, Enum):
    CANDIDATE = "candidate"
    SUPPORTED = "supported"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"


class SignalEntity(BaseModel):
    """Legacy signal entity preserved for backward compatibility."""
    id: str
    entity_id: str  # canonical company or person ID
    signal_type: str  # hiring_growth, tech_stack_change, funding_raised, new_product_launch
    title: str
    description: str
    confidence: float = 1.0
    detected_at: str = Field(default_factory=utc_iso_now)
    source_observation_id: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class SignalCandidateEntity(BaseModel):
    """Evidence-backed signal candidate traceable to timeline events and facts."""
    id: str
    entity_type: str = "company"
    entity_id: str
    signal_type: str  # SignalType value
    trigger_event_ids: List[str] = Field(default_factory=list)
    detected_at: str = Field(default_factory=utc_iso_now)
    occurred_at: Optional[str] = None  # when the triggering change happened
    expires_at: Optional[str] = None
    confidence: float = 1.0
    significance: str = "medium"
    status: str = "candidate"  # SignalCandidateStatus value
    policy_version: str = "v1"
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
