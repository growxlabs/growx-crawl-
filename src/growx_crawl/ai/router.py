"""
GrowX AI Router.
Resolves optimal provider and model based on task requirements and fallback priority.
"""

from typing import Tuple

TASK_MODEL_MAP = {
    "icp_synthesis": ("gemini", "gemini-2.0-flash"),
    "email_copywriting": ("gemini", "gemini-2.0-flash"),
    "company_enrichment": ("gemini", "gemini-1.5-flash"),
    "deep_reasoning": ("openai", "gpt-4o"),
}


def route_request(task: str, requested_provider: str = "", requested_model: str = "") -> Tuple[str, str]:
    """Returns (provider, model)."""
    if requested_provider and requested_model:
        return requested_provider.lower(), requested_model.lower()

    default_provider, default_model = TASK_MODEL_MAP.get(task, ("gemini", "gemini-2.0-flash"))
    provider = requested_provider.lower() if requested_provider else default_provider
    model = requested_model.lower() if requested_model else default_model
    return provider, model
