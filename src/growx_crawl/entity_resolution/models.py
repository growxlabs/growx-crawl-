"""
GrowX Entity Resolution Models.
Defines candidate pairs, match explanations, decisions, and blocking keys.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from growx_crawl.shared.time import utc_iso_now


class ResolutionDecision(str, Enum):
    AUTO_MERGED = "auto_merged"
    REVIEW_REQUIRED = "review_required"
    NO_MATCH = "no_match"
    MERGED_MANUAL = "merged_manual"
    REJECTED_MANUAL = "rejected_manual"


class MatchSignal(BaseModel):
    name: str
    weight: float
    score: float
    description: str


class MatchExplanation(BaseModel):
    summary: str
    signals: List[MatchSignal] = Field(default_factory=list)
    confidence: float = 0.0
    recommended_decision: ResolutionDecision = ResolutionDecision.NO_MATCH


class ResolutionCandidate(BaseModel):
    id: str
    entity_type: str  # company, person
    source_entity_id: str
    target_entity_id: str
    confidence: float
    decision: ResolutionDecision
    signals: List[str] = Field(default_factory=list)
    explanation: Optional[MatchExplanation] = None
    status: str = "pending"  # pending, approved, rejected
    created_at: str = Field(default_factory=utc_iso_now)
    resolved_at: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class BlockingKey(BaseModel):
    key_type: str
    key_value: str
    entity_id: str
    entity_type: str
