from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ObservationEntity(BaseModel):
    id: str
    subject_type: str
    subject_id: str
    predicate: str
    raw_value: Optional[str] = None
    normalized_value_json: Dict[str, Any] = Field(default_factory=dict)
    value_type: str
    source_id: Optional[str] = None
    object_ref_id: Optional[str] = None
    observed_at: str = Field(default_factory=utc_now_iso)
    extractor_name: str
    extractor_version: str = "v1.0"
    model_run_id: Optional[str] = None
    confidence: float = 1.0
    created_at: str = Field(default_factory=utc_now_iso)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class ObservationRejectionEntity(BaseModel):
    id: str
    payload_json: Dict[str, Any] = Field(default_factory=dict)
    reason_code: str  # unknown_predicate, invalid_type, missing_subject, invalid_entity_ref, normalization_failed, unsupported_unit, invalid_date
    source_id: Optional[str] = None
    created_at: str = Field(default_factory=utc_now_iso)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
