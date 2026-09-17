"""
GrowX AI Router.
Resolves optimal provider, model, and fallback chain based on task requirements,
quality tier, circuit breaker health, and explicit caller preferences.
"""

import os
from typing import List, Optional, Tuple
from growx_crawl.ai.circuit_breaker import CircuitState, circuit_breaker
from growx_crawl.ai.fallback import FallbackOption
from growx_crawl.ai.models import QualityTier
from growx_crawl.ai.tasks import get_task_definition

# Quality Tier -> (Primary, Fallback)
TIER_ROUTING = {
    QualityTier.FAST.value: {
        "primary": ("gemini", "gemini-1.5-flash"),
        "fallback": ("openai", "gpt-4o-mini"),
    },
    QualityTier.STANDARD.value: {
        "primary": ("gemini", "gemini-2.0-flash"),
        "fallback": ("openai", "gpt-4o-mini"),
    },
    QualityTier.HIGH.value: {
        "primary": ("openai", "gpt-4o"),
        "fallback": ("gemini", "gemini-1.5-pro"),
    },
}

# Legacy task-to-model map for exact backward compatibility
TASK_MODEL_MAP = {
    "icp_synthesis": ("gemini", "gemini-2.0-flash"),
    "email_copywriting": ("gemini", "gemini-2.0-flash"),
    "company_enrichment": ("gemini", "gemini-1.5-flash"),
    "deep_reasoning": ("openai", "gpt-4o"),
}


class ProviderRouter:
    """Intelligent multi-factor AI routing engine."""

    def resolve_tier(self, task: str, requested_tier: Optional[str] = None) -> str:
        if requested_tier:
            return requested_tier.lower()
        task_def = get_task_definition(task)
        return task_def.quality_tier

    def get_fallback_chain(
        self,
        task: str,
        requested_provider: Optional[str] = None,
        requested_model: Optional[str] = None,
        requested_tier: Optional[str] = None,
    ) -> List[FallbackOption]:
        # 1. Check if mock provider is forced globally via env
        env_provider = os.environ.get("GROWX_AI_PROVIDER", "").lower()
        if env_provider == "mock" or requested_provider == "mock":
            return [FallbackOption("mock", requested_model or "mock-model", "fast")]

        tier = self.resolve_tier(task, requested_tier)
        tier_cfg = TIER_ROUTING.get(tier, TIER_ROUTING[QualityTier.STANDARD.value])

        chain: List[FallbackOption] = []

        # If caller explicitly provided provider and/or model
        if requested_provider and requested_model:
            chain.append(FallbackOption(requested_provider.lower(), requested_model.lower(), tier))
        elif requested_provider:
            # Match model to requested provider for this tier
            prim_prov, prim_mod = tier_cfg["primary"]
            fall_prov, fall_mod = tier_cfg["fallback"]
            if requested_provider.lower() == prim_prov:
                chain.append(FallbackOption(prim_prov, prim_mod, tier))
                chain.append(FallbackOption(fall_prov, fall_mod, tier))
            else:
                chain.append(FallbackOption(fall_prov, fall_mod, tier))
                chain.append(FallbackOption(prim_prov, prim_mod, tier))
        else:
            # Check circuit breaker on primary
            prim_prov, prim_mod = tier_cfg["primary"]
            fall_prov, fall_mod = tier_cfg["fallback"]

            prim_state = circuit_breaker.get_state(prim_prov)
            if prim_state == CircuitState.OPEN:
                # Primary circuit open, invert preference
                chain.append(FallbackOption(fall_prov, fall_mod, tier))
                chain.append(FallbackOption(prim_prov, prim_mod, tier))
            else:
                chain.append(FallbackOption(prim_prov, prim_mod, tier))
                chain.append(FallbackOption(fall_prov, fall_mod, tier))

        # Always append mock as ultimate safety fallback if enabled
        if os.environ.get("GROWX_AI_MOCK_FALLBACK", "true").lower() == "true":
            chain.append(FallbackOption("mock", "mock-model", "fast"))

        return chain


provider_router = ProviderRouter()


def route_request(task: str, requested_provider: str = "", requested_model: str = "") -> Tuple[str, str]:
    """
    Backward-compatible entrypoint returning (provider, model).
    Guarantees exact parity with previous router tests.
    """
    if requested_provider and requested_model:
        return requested_provider.lower(), requested_model.lower()

    if task in TASK_MODEL_MAP:
        default_provider, default_model = TASK_MODEL_MAP[task]
    else:
        tier = provider_router.resolve_tier(task)
        cfg = TIER_ROUTING.get(tier, TIER_ROUTING[QualityTier.STANDARD.value])
        default_provider, default_model = cfg["primary"]

    provider = requested_provider.lower() if requested_provider else default_provider
    model = requested_model.lower() if requested_model else default_model
    return provider, model
