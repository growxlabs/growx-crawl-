"""
GrowX AI Fallback Orchestrator.
Coordinates transparent failover to secondary providers/models and records fallback telemetry.
"""

from typing import Any, Callable, Coroutine, List, Optional, Tuple
from growx_crawl.ai.models import AIResponse


class FallbackOption:
    def __init__(self, provider: str, model: str, quality_tier: str = "standard"):
        self.provider = provider
        self.model = model
        self.quality_tier = quality_tier


async def execute_with_fallback(
    chain: List[FallbackOption],
    invoker: Callable[[str, str, str], Coroutine[Any, Any, AIResponse]],
) -> Tuple[AIResponse, bool, Optional[str]]:
    """
    Tries each provider/model in the fallback chain in sequence.
    Returns (response, fallback_used, fallback_reason).
    """
    if not chain:
        raise ValueError("Fallback chain cannot be empty")

    primary = chain[0]
    errors: List[str] = []

    for index, option in enumerate(chain):
        try:
            resp = await invoker(option.provider, option.model, option.quality_tier)
            if index > 0:
                resp.fallback_used = True
                resp.fallback_reason = f"Primary {primary.provider}/{primary.model} failed: {errors[-1]}"
                return resp, True, resp.fallback_reason
            return resp, False, None
        except Exception as e:
            errors.append(f"{option.provider}/{option.model}: {e}")
            if index == len(chain) - 1:
                # All fallbacks exhausted
                raise e

    raise RuntimeError("Fallback execution completed without result or error")
