"""
GrowX AI Gateway Models.
Defines execution requests, responses, and model run audit telemetry.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from growx_crawl.shared.time import utc_iso_now


class AIRequest(BaseModel):
    task: str  # e.g. "icp_synthesis", "email_copywriting", "company_enrichment"
    prompt: str
    prompt_version: str = "v1"
    model: Optional[str] = None
    provider: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class AIResponse(BaseModel):
    run_id: str
    content: str
    model: str
    provider: str
    task: str
    prompt_version: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    created_at: str = Field(default_factory=utc_iso_now)
