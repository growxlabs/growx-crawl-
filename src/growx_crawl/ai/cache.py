"""
GrowX AI Cache & Fingerprint Engine.
Implements deterministic SHA-256 request fingerprinting and task-safe response caching.
"""

import time
from typing import Any, Dict, Optional
from growx_crawl.ai.models import AIRequest, AIResponse, RunStatus
from growx_crawl.shared.hashing import sha256_text as sha256_hash


def compute_ai_fingerprint(
    task: str,
    prompt: str,
    prompt_version: str,
    model: str,
    schema_name: str = "",
) -> str:
    """Computes stable SHA-256 fingerprint for idempotency and caching."""
    seed = f"{task}:{prompt_version}:{model}:{schema_name}:{prompt.strip()}"
    return sha256_hash(seed)


class AICache:
    """In-memory task-safe TTL cache for model outputs."""

    def __init__(self):
        # Key -> (expires_at, AIResponse)
        self._cache: Dict[str, tuple[float, AIResponse]] = {}

    def get(self, fingerprint: str) -> Optional[AIResponse]:
        item = self._cache.get(fingerprint)
        if not item:
            return None
        expires_at, cached_resp = item
        if time.time() > expires_at:
            del self._cache[fingerprint]
            return None

        # Return a copy marked as cached
        return AIResponse(
            run_id=cached_resp.run_id,
            content=cached_resp.content,
            structured_output=cached_resp.structured_output,
            model=cached_resp.model,
            provider=cached_resp.provider,
            task=cached_resp.task,
            prompt_id=cached_resp.prompt_id,
            prompt_version=cached_resp.prompt_version,
            quality_tier=cached_resp.quality_tier,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            cost_usd=0.0,
            latency_ms=1,
            status=RunStatus.CACHED.value,
            fallback_used=cached_resp.fallback_used,
            cached=True,
            fingerprint=fingerprint,
            created_at=cached_resp.created_at,
            metadata_json=cached_resp.metadata_json,
        )

    def set(self, fingerprint: str, response: AIResponse, ttl_seconds: int) -> None:
        if ttl_seconds <= 0:
            return
        expires_at = time.time() + ttl_seconds
        self._cache[fingerprint] = (expires_at, response)

    def clear(self) -> None:
        self._cache.clear()


ai_cache = AICache()
