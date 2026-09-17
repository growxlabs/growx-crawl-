"""
GrowX AI Prompt Version Registry (Adapter & Facade).
Maintains exact backward compatibility with existing tests and imports.
"""

from typing import Dict
from growx_crawl.ai.prompt_registry import prompt_registry, wrap_untrusted_input

PROMPT_REGISTRY: Dict[str, Dict[str, str]] = {
    "icp_synthesis": {
        "v1": "Synthesize the Ideal Customer Profile (ICP) based on: {context}",
    },
    "email_copywriting": {
        "v1": "Draft a personalized 3-sentence B2B outbound email for {lead_name} at {company_name}: {context}",
    },
    "company_enrichment": {
        "v1": "Extract industry, employee band, value proposition, and competitor set from: {content}",
    },
}


def get_prompt_template(task: str, version: str = "v1") -> str:
    """Retrieves prompt template string for task and version."""
    if task in PROMPT_REGISTRY and version in PROMPT_REGISTRY[task]:
        return PROMPT_REGISTRY[task][version]
    tpl = prompt_registry.get(task, version)
    return tpl.user_template


__all__ = ["PROMPT_REGISTRY", "get_prompt_template", "prompt_registry", "wrap_untrusted_input"]
