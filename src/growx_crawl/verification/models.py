"""
GrowX Verification Models.
Defines verification entities, statuses, reason codes, gate decisions, check records,
runs, and policy definitions.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from growx_crawl.shared.time import utc_iso_now


class SubjectType(str, Enum):
    COMPANY = "company"
    DOMAIN = "domain"
    COMPANY_DOMAIN = "company_domain"
    PERSON = "person"
    EMPLOYMENT = "employment"
    EMAIL = "email"
    FACT = "fact"


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    SUPPORTED = "supported"
    UNVERIFIED = "unverified"
    UNCERTAIN = "uncertain"
    CONFLICTING = "conflicting"
    STALE = "stale"
    INVALID = "invalid"
    UNREACHABLE = "unreachable"
    SUPPRESSED = "suppressed"
    # Legacy aliases
    RISKY = "risky"
    FAILED = "failed"


class GateDecision(str, Enum):
    ALLOW = "ALLOW"
    ALLOW_WITH_RISK = "ALLOW_WITH_RISK"
    REVERIFY = "REVERIFY"
    BLOCK = "BLOCK"


class FreshnessState(str, Enum):
    FRESH = "fresh"
    AGING = "aging"
    STALE = "stale"
    EXPIRED = "expired"


class DomainState(str, Enum):
    ACTIVE = "active"
    REDIRECTING = "redirecting"
    PARKED = "parked"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    UNREACHABLE = "unreachable"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


class EmploymentState(str, Enum):
    CURRENT_VERIFIED = "current_verified"
    CURRENT_SUPPORTED = "current_supported"
    UNCERTAIN = "uncertain"
    HISTORICAL = "historical"
    ENDED = "ended"
    CONFLICTING = "conflicting"
    STALE = "stale"


class EmailState(str, Enum):
    VERIFIED = "verified"
    LIKELY_VALID = "likely_valid"
    RISKY = "risky"
    CATCH_ALL = "catch_all"
    UNKNOWN = "unknown"
    INVALID = "invalid"
    SUPPRESSED = "suppressed"


class ReasonCode:
    OFFICIAL_DOMAIN_ACTIVE = "OFFICIAL_DOMAIN_ACTIVE"
    OFFICIAL_SITE_NAME_MATCH = "OFFICIAL_SITE_NAME_MATCH"
    MULTI_SOURCE_SUPPORT = "MULTI_SOURCE_SUPPORT"
    SOURCE_STALE = "SOURCE_STALE"
    DOMAIN_UNREACHABLE = "DOMAIN_UNREACHABLE"
    DOMAIN_COMPANY_CONFLICT = "DOMAIN_COMPANY_CONFLICT"
    EMPLOYMENT_STALE = "EMPLOYMENT_STALE"
    EMPLOYMENT_CONFIRMED = "EMPLOYMENT_CONFIRMED"
    EMAIL_SYNTAX_VALID = "EMAIL_SYNTAX_VALID"
    EMAIL_SYNTAX_INVALID = "EMAIL_SYNTAX_INVALID"
    EMAIL_MX_VALID = "EMAIL_MX_VALID"
    EMAIL_SMTP_POSITIVE = "EMAIL_SMTP_POSITIVE"
    EMAIL_CATCH_ALL = "EMAIL_CATCH_ALL"
    EMAIL_DOMAIN_MISMATCH = "EMAIL_DOMAIN_MISMATCH"
    FACT_SOURCE_CONFLICT = "FACT_SOURCE_CONFLICT"
    ROLE_ADDRESS_DETECTED = "ROLE_ADDRESS_DETECTED"
    FREE_EMAIL_PROVIDER = "FREE_EMAIL_PROVIDER"
    PARKING_PAGE_DETECTED = "PARKING_PAGE_DETECTED"
    NO_MX_RECORDS = "NO_MX_RECORDS"
    DNS_LOOKUP_SUCCESS = "DNS_LOOKUP_SUCCESS"
    HTTP_REACHABLE = "HTTP_REACHABLE"
    HIGH_FRESHNESS = "HIGH_FRESHNESS"
    EVIDENCE_PROVENANCE_CONFIRMED = "EVIDENCE_PROVENANCE_CONFIRMED"


class VerificationCheckEntity(BaseModel):
    id: str
    verification_run_id: str
    check_type: str
    status: str = "passed"  # passed, failed, warning, skipped
    score: float = 1.0
    reason_code: str
    evidence_ids: List[str] = Field(default_factory=list)
    duration_ms: int = 0
    created_at: str = Field(default_factory=utc_iso_now)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class VerificationRunEntity(BaseModel):
    id: str
    subject_type: str
    subject_id: str
    verification_type: str
    policy_id: str
    policy_version: str = "v1"
    status: VerificationStatus
    confidence: float
    started_at: str = Field(default_factory=utc_iso_now)
    completed_at: Optional[str] = None
    valid_until: Optional[str] = None
    error_code: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class VerificationStateEntity(BaseModel):
    subject_type: str
    subject_id: str
    verification_type: str
    latest_run_id: str
    status: VerificationStatus
    confidence: float
    last_verified_at: str = Field(default_factory=utc_iso_now)
    valid_until: Optional[str] = None
    updated_at: str = Field(default_factory=utc_iso_now)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class VerificationResultEntity(BaseModel):
    id: str
    subject_type: str
    subject_id: str
    verification_type: str = "standard"
    status: VerificationStatus
    confidence: float
    policy_name: str = "standard"
    policy_version: str = "v1"
    reason_codes: List[str] = Field(default_factory=list)
    checks: List[VerificationCheckEntity] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)
    verified_at: str = Field(default_factory=utc_iso_now)
    valid_until: Optional[str] = None
    expires_at: Optional[str] = None
    details_json: Dict[str, Any] = Field(default_factory=dict)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)

    # Backward compatibility properties
    @property
    def entity_type(self) -> str:
        return self.subject_type

    @property
    def entity_id(self) -> str:
        return self.subject_id


class VerificationPolicy(BaseModel):
    id: str
    name: str
    subject_type: str
    version: str = "v1"
    min_confidence: float = 0.80
    required_checks: List[str] = Field(default_factory=list)
    ttl_hours: int = 168  # 7 days
    config_json: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    created_at: str = Field(default_factory=utc_iso_now)
    updated_at: str = Field(default_factory=utc_iso_now)
