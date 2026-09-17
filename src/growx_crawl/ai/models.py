"""
GrowX AI Gateway Models.
Defines execution requests, structured requests, responses, quality tiers, and run telemetry.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field
from growx_crawl.shared.time import utc_iso_now


class QualityTier(str, Enum):
    FAST = "fast"
    STANDARD = "standard"
    HIGH = "high"


class RunStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    FALLBACK = "fallback"
    CACHED = "cached"


class AIRequest(BaseModel):
    task: str
    prompt: str = ""
    input_data: Optional[Dict[str, Any]] = None
    system_context: str = ""
    prompt_id: str = ""
    prompt_version: str = "v1"
    quality_tier: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout_seconds: Optional[float] = None
    scope: str = "global_public"  # "global_public", "internal_growx", "private_account"
    account_id: Optional[str] = None
    job_id: Optional[str] = None
    trace_id: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class StructuredAIRequest(AIRequest):
    schema_class: Optional[Type[BaseModel]] = None
    output_schema_json: Optional[Dict[str, Any]] = None
    repair_attempts: int = 1


class ClassificationRequest(AIRequest):
    categories: List[str] = Field(default_factory=list)


class SummaryRequest(AIRequest):
    text: str = ""
    max_words: int = 100


class EmbeddingRequest(BaseModel):
    input_text: str
    model: str = "text-embedding-3-small"
    provider: str = "openai"
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class EmbeddingResponse(BaseModel):
    run_id: str
    embedding: List[float]
    dimensions: int
    tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    provider: str = "openai"
    model: str = "text-embedding-3-small"
    created_at: str = Field(default_factory=utc_iso_now)


class AIResponse(BaseModel):
    run_id: str
    content: str
    structured_output: Optional[Dict[str, Any]] = None
    model: str
    provider: str
    task: str
    prompt_id: str = ""
    prompt_version: str = "v1"
    quality_tier: str = "standard"
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    status: str = RunStatus.SUCCESS.value
    fallback_used: bool = False
    fallback_reason: Optional[str] = None
    cached: bool = False
    fingerprint: str = ""
    error_code: Optional[str] = None
    created_at: str = Field(default_factory=utc_iso_now)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
