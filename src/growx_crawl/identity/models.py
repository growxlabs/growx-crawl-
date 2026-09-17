from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class LocationEntity(BaseModel):
    id: str
    name: str
    normalized_name: str
    city: Optional[str] = None
    region: Optional[str] = None
    country_code: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_type: str = "office"
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class CompanyLocationEntity(BaseModel):
    company_id: str
    location_id: str
    relationship_type: str = "office"
    is_primary: bool = True
    confidence: float = 1.0
    first_seen_at: str = Field(default_factory=utc_now_iso)
    last_seen_at: str = Field(default_factory=utc_now_iso)
    last_verified_at: Optional[str] = None


class BrandEntity(BaseModel):
    id: str
    canonical_name: str
    normalized_name: str
    company_id: str
    primary_domain_id: Optional[str] = None
    first_seen_at: str = Field(default_factory=utc_now_iso)
    last_seen_at: str = Field(default_factory=utc_now_iso)
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class PersonAliasEntity(BaseModel):
    id: str
    person_id: str
    alias: str
    normalized_alias: str
    alias_type: str = "name_variant"
    source_id: Optional[str] = None
    confidence: float = 1.0
    first_seen_at: str = Field(default_factory=utc_now_iso)
    last_seen_at: str = Field(default_factory=utc_now_iso)


class CompanyRelationshipEntity(BaseModel):
    id: str
    from_company_id: str
    to_company_id: str
    relationship_type: str  # parent, subsidiary, brand_owner, acquired, partner, competitor_candidate
    confidence: float = 1.0
    source_id: Optional[str] = None
    first_seen_at: str = Field(default_factory=utc_now_iso)
    last_seen_at: str = Field(default_factory=utc_now_iso)
    last_verified_at: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class ExternalIdentityEntity(BaseModel):
    id: str
    entity_type: str  # company, person, location
    entity_id: str
    provider: str  # linkedin, crunchbase, opencorporates, google_maps
    external_id: str
    external_url: Optional[str] = None
    first_seen_at: str = Field(default_factory=utc_now_iso)
    last_seen_at: str = Field(default_factory=utc_now_iso)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class IdentityKeyEntity(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    key_type: str  # domain, external_id, registry_id
    key_value: str
    is_unique: bool = True
    created_at: str = Field(default_factory=utc_now_iso)
    last_verified_at: Optional[str] = None


class IdentityCandidateEntity(BaseModel):
    id: str
    entity_type: str
    candidate_payload_json: Dict[str, Any]
    candidate_key: str
    source_id: Optional[str] = None
    status: str = "pending"  # pending, resolved, rejected, needs_review
    created_at: str = Field(default_factory=utc_now_iso)
    resolved_at: Optional[str] = None
    resolved_entity_id: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class EntityMergeEntity(BaseModel):
    id: str
    entity_type: str
    source_entity_id: str  # merged & redirected ID
    target_entity_id: str  # surviving canonical ID
    reason: str
    method: str = "manual"
    confidence: float = 1.0
    created_at: str = Field(default_factory=utc_now_iso)
    created_by: str = "system"
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class IdentityEventEntity(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    event_type: str
    payload_json: Dict[str, Any] = Field(default_factory=dict)
    source_id: Optional[str] = None
    created_at: str = Field(default_factory=utc_now_iso)
    actor_type: str = "system"  # system, crawler, import, agent, human, migration
    actor_id: Optional[str] = None
