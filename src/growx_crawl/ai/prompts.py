"""
GrowX AI Prompt Version Registry.
"""

from typing import Dict

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
    task_prompts = PROMPT_REGISTRY.get(task, {})
    return task_prompts.get(version, "{context}")
