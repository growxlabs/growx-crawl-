from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class FactPredicateEntity(BaseModel):
    predicate: str
    subject_type: str  # company, person, domain, location
    value_type: str  # string, integer, decimal, boolean, date, datetime, url, email, phone, enum, entity_ref, json
    cardinality: str = "one"  # one, many
    verification_policy: str = "standard"  # strict, standard, relaxed
    freshness_policy: str = "90d"  # 30d, 90d, 180d, 365d
    merge_policy: str = "latest_wins"  # latest_wins, highest_confidence, additive, conflict_on_disagree
    description: Optional[str] = None
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class FactEntity(BaseModel):
    id: str
    subject_type: str
    subject_id: str
    predicate: str
    value_type: str
    current_value_json: Dict[str, Any] = Field(default_factory=dict)
    status: str = "accepted"  # candidate, accepted, conflicting, stale, rejected, superseded, deleted
    confidence: float = 1.0
    verification_state: str = "unverified"  # unverified, source_supported, multi_source_supported, verified, disputed, stale
    first_seen_at: str = Field(default_factory=utc_now_iso)
    last_seen_at: str = Field(default_factory=utc_now_iso)
    last_verified_at: Optional[str] = None
    valid_from: str = Field(default_factory=utc_now_iso)
    valid_to: Optional[str] = None
    scope_type: str = "global"  # global, internal, account, project
    scope_id: str = "global"
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class FactValueEntity(BaseModel):
    id: str
    fact_id: str
    value_json: Dict[str, Any] = Field(default_factory=dict)
    value_type: str
    confidence: float = 1.0
    status: str = "accepted"  # accepted, superseded, conflicting, rejected
    valid_from: str = Field(default_factory=utc_now_iso)
    valid_to: Optional[str] = None
    first_seen_at: str = Field(default_factory=utc_now_iso)
    last_seen_at: str = Field(default_factory=utc_now_iso)
    last_verified_at: Optional[str] = None
    created_at: str = Field(default_factory=utc_now_iso)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class FactEvidenceEntity(BaseModel):
    fact_id: str
    observation_id: str
    support_type: str = "supports"  # supports, contradicts, supersedes, context
    weight: float = 1.0
    created_at: str = Field(default_factory=utc_now_iso)


class FactConflictEntity(BaseModel):
    id: str
    subject_type: str
    subject_id: str
    predicate: str
    status: str = "open"  # open, auto_resolved, human_resolved, deferred
    created_at: str = Field(default_factory=utc_now_iso)
    resolved_at: Optional[str] = None
    resolution_method: Optional[str] = None
    selected_fact_value_id: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class FactEventEntity(BaseModel):
    id: str
    fact_id: str
    event_type: str  # observation_created, fact_created, fact_updated, fact_conflict_opened, fact_superseded, fact_rejected, fact_verified
    payload_json: Dict[str, Any] = Field(default_factory=dict)
    actor_type: str = "system"  # system, crawler, import, model, human
    actor_id: Optional[str] = None
    created_at: str = Field(default_factory=utc_now_iso)
