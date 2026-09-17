"""
GrowX AI Cost Accounting & Profiles.
Maintains token pricing models, computes COGS per AI request, and enforces budget guards.
"""

from typing import Dict, Optional, Tuple
from growx_crawl.ai.errors import AIBudgetExceeded

# Pricing in USD per 1M tokens: (prompt_rate, completion_rate)
MODEL_RATES: Dict[str, Tuple[float, float]] = {
    # Gemini
    "gemini-1.5-pro": (1.25, 5.00),
    "gemini-1.5-flash": (0.075, 0.30),
    "gemini-2.0-flash": (0.10, 0.40),
    # OpenAI
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "text-embedding-3-small": (0.02, 0.00),
    # Testing mock
    "mock-model": (0.00, 0.00),
}

# Versioned cost profiles (effective date / rate overrides)
COST_PROFILES: Dict[str, Dict[str, Tuple[float, float]]] = {
    "2026-v1": MODEL_RATES,
    "default": MODEL_RATES,
}


def calculate_ai_cost(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    profile_version: str = "default",
) -> float:
    """Calculates estimated USD cost based on model rates and token counts."""
    rates_map = COST_PROFILES.get(profile_version, MODEL_RATES)
    rate = rates_map.get(model.lower(), (0.20, 0.80))
    prompt_cost = (max(0, prompt_tokens) / 1_000_000) * rate[0]
    completion_cost = (max(0, completion_tokens) / 1_000_000) * rate[1]
    return round(prompt_cost + completion_cost, 6)


def estimate_request_cost(
    model: str,
    estimated_input_chars: int,
    estimated_output_tokens: int = 500,
) -> float:
    """Fast pre-flight estimate of request cost based on character count."""
    est_prompt_tokens = max(10, int(estimated_input_chars / 4))
    return calculate_ai_cost(model, est_prompt_tokens, estimated_output_tokens)


def enforce_cost_guard(
    estimated_cost_usd: float,
    max_cost_limit_usd: float = 0.50,
    task: str = "",
) -> None:
    """Raises AIBudgetExceeded if the estimated cost exceeds the max threshold."""
    if estimated_cost_usd > max_cost_limit_usd:
        raise AIBudgetExceeded(
            f"Estimated request cost ${estimated_cost_usd:.4f} exceeds budget limit ${max_cost_limit_usd:.4f}",
            task=task,
            cost_usd=estimated_cost_usd,
        )
