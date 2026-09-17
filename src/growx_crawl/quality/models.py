"""
GrowX Data Quality Models.
Defines gate types, quality statuses, rule types, quality policies, evaluation decisions,
quarantine entities, and prospect snapshots.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from growx_crawl.shared.time import utc_iso_now


class GateType(str, Enum):
    CANONICAL_INGESTION = "canonical_ingestion"
    INTELLIGENCE_TRUST = "intelligence_trust"
    PROSPECT_ELIGIBILITY = "prospect_eligibility"
    PERSONALIZATION_ELIGIBILITY = "personalization_eligibility"
    OUTREACH_ELIGIBILITY = "outreach_eligibility"


class QualityStatus(str, Enum):
    PASS = "pass"
    LIMITED = "limited"
    REVERIFY = "reverify"
    QUARANTINE = "quarantine"
    BLOCKED = "blocked"
    REJECTED = "rejected"


class RuleType(str, Enum):
    REQUIRED = "required"
    HARD_BLOCK = "hard_block"
    SOFT_PENALTY = "soft_penalty"
    BOOST = "boost"
    FRESHNESS = "freshness"
    VERIFICATION = "verification"
    COMPLETENESS = "completeness"
    CONFLICT = "conflict"
    DUPLICATE = "duplicate"
    SCOPE = "scope"


class QualityRuleResult(BaseModel):
    rule_name: str
    rule_type: RuleType
    status: str  # "passed", "failed", "warning"
    score_delta: float = 0.0
    reason_code: str
    details: Dict[str, Any] = Field(default_factory=dict)


class QualityDecision(BaseModel):
    gate_type: GateType
    status: QualityStatus
    score: float  # 0.0 -> 1.0
    reasons: List[str] = Field(default_factory=list)
    required_actions: List[str] = Field(default_factory=list)
    valid_until: Optional[str] = None
    policy_id: str = ""
    policy_version: str = "v1"
    rule_results: List[QualityRuleResult] = Field(default_factory=list)
    details_json: Dict[str, Any] = Field(default_factory=dict)


class QualityPolicy(BaseModel):
    id: str
    name: str
    gate_type: GateType
    profile: str
    version: str = "v1"
    min_score: float = 0.70
    rules_config: Dict[str, Any] = Field(default_factory=dict)
    ttl_hours: int = 168  # 7 days default
    enabled: bool = True
    created_at: str = Field(default_factory=utc_iso_now)
    updated_at: str = Field(default_factory=utc_iso_now)


class QualityResultEntity(BaseModel):
    id: str
    subject_type: str
    subject_id: str
    gate_type: GateType
    profile: str
    status: QualityStatus
    score: float
    policy_id: str
    policy_version: str = "v1"
    evaluated_at: str = Field(default_factory=utc_iso_now)
    valid_until: Optional[str] = None
    reasons: List[str] = Field(default_factory=list)
    required_actions: List[str] = Field(default_factory=list)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class QualityStateEntity(BaseModel):
    subject_type: str
    subject_id: str
    gate_type: GateType
    latest_result_id: str
    status: QualityStatus
    score: float
    valid_until: Optional[str] = None
    updated_at: str = Field(default_factory=utc_iso_now)


class QuarantineEntity(BaseModel):
    id: str
    subject_type: str
    candidate_payload_json: Dict[str, Any]
    reason_codes: List[str] = Field(default_factory=list)
    source_id: Optional[str] = None
    status: str = "pending"  # "pending", "reprocessed", "accepted", "rejected"
    created_at: str = Field(default_factory=utc_iso_now)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class ProspectQualitySnapshot(BaseModel):
    prospect_id: str
    company_score: float = 0.0
    person_score: float = 0.0
    employment_score: float = 0.0
    email_score: float = 0.0
    personalization_score: float = 0.0
    outreach_score: float = 0.0
    overall_status: QualityStatus = QualityStatus.PASS
    reasons: List[str] = Field(default_factory=list)
    required_actions: List[str] = Field(default_factory=list)
    evaluated_at: str = Field(default_factory=utc_iso_now)
