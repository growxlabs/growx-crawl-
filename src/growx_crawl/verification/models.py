"""
GrowX Verification Models.
Defines verification entities, status enums, and policy rules.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from growx_crawl.shared.time import utc_iso_now


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    RISKY = "risky"
    FAILED = "failed"


class VerificationResultEntity(BaseModel):
    id: str
    entity_type: str  # company, domain, person, employment, email, fact
    entity_id: str
    status: VerificationStatus
    confidence: float
    policy_name: str = "standard"
    details_json: Dict[str, Any] = Field(default_factory=dict)
    verified_at: str = Field(default_factory=utc_iso_now)
    expires_at: Optional[str] = None


class VerificationPolicy(BaseModel):
    name: str
    min_confidence: float = 0.80
    required_checks: List[str] = Field(default_factory=list)
    ttl_hours: int = 168  # 7 days
