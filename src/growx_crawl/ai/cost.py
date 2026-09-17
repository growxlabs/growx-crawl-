"""
GrowX AI Cost Accounting.
Maintains token pricing models and computes COGS per AI request.
"""

from typing import Dict, Tuple

# Pricing in USD per 1M tokens: (prompt_rate, completion_rate)
MODEL_RATES: Dict[str, Tuple[float, float]] = {
    # Gemini
    "gemini-1.5-pro": (1.25, 5.00),
    "gemini-1.5-flash": (0.075, 0.30),
    "gemini-2.0-flash": (0.10, 0.40),
    # OpenAI
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
}


def calculate_ai_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Calculates estimated USD cost based on token counts."""
    rate = MODEL_RATES.get(model.lower(), (0.20, 0.80))
    prompt_cost = (prompt_tokens / 1_000_000) * rate[0]
    completion_cost = (completion_tokens / 1_000_000) * rate[1]
    return round(prompt_cost + completion_cost, 6)
