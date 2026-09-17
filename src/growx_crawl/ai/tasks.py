"""
GrowX AI Task Registry.
Defines canonical task types, default tiers, cacheability policies, and guardrails.
"""

from enum import Enum
from typing import Dict, Optional
from pydantic import BaseModel


class AITask(str, Enum):
    COMPANY_ANALYSIS = "company_analysis"
    COMPETITOR_ANALYSIS = "competitor_analysis"
    ICP_GENERATION = "icp_generation"
    PROSPECT_RESEARCH = "prospect_research"
    PROSPECT_QUALIFICATION = "prospect_qualification"
    FACT_INTERPRETATION = "fact_interpretation"
    VERIFICATION_REASONING = "verification_reasoning"
    ENTITY_RESOLUTION_ASSIST = "entity_resolution_assist"
    EMAIL_PERSONALIZATION = "email_personalization"
    REPLY_CLASSIFICATION = "reply_classification"
    REPLY_DRAFTING = "reply_drafting"
    MEETING_BRIEF = "meeting_brief"
    SIGNAL_INTERPRETATION = "signal_interpretation"
    SUMMARY = "summary"
    EXTRACTION = "extraction"
    CLASSIFICATION = "classification"
    EMBEDDING = "embedding"
    # Backward compatibility aliases
    ICP_SYNTHESIS = "icp_synthesis"
    EMAIL_COPYWRITING = "email_copywriting"
    COMPANY_ENRICHMENT = "company_enrichment"
    DEEP_REASONING = "deep_reasoning"


class TaskDefinition(BaseModel):
    name: str
    description: str
    quality_tier: str = "standard"  # "fast", "standard", "high"
    cacheable: bool = False
    cache_ttl_seconds: int = 0
    max_output_tokens: int = 1000
    timeout_seconds: int = 30
    untrusted_input_delimiter: bool = False


STANDARD_TASKS: Dict[str, TaskDefinition] = {
    AITask.COMPANY_ANALYSIS.value: TaskDefinition(
        name=AITask.COMPANY_ANALYSIS.value,
        description="Structured extraction of company offerings, audience, pricing, and tech stack",
        quality_tier="standard",
        cacheable=True,
        cache_ttl_seconds=604800,
        max_output_tokens=1500,
        timeout_seconds=30,
        untrusted_input_delimiter=True,
    ),
    AITask.COMPETITOR_ANALYSIS.value: TaskDefinition(
        name=AITask.COMPETITOR_ANALYSIS.value,
        description="Identify key competitors and market differentiation",
        quality_tier="standard",
        cacheable=True,
        cache_ttl_seconds=604800,
        max_output_tokens=1000,
        timeout_seconds=25,
        untrusted_input_delimiter=True,
    ),
    AITask.ICP_GENERATION.value: TaskDefinition(
        name=AITask.ICP_GENERATION.value,
        description="Synthesize Ideal Customer Profile from company data",
        quality_tier="standard",
        cacheable=True,
        cache_ttl_seconds=604800,
        max_output_tokens=1200,
        timeout_seconds=25,
        untrusted_input_delimiter=False,
    ),
    AITask.PROSPECT_RESEARCH.value: TaskDefinition(
        name=AITask.PROSPECT_RESEARCH.value,
        description="Research individual prospect facts and hooks",
        quality_tier="standard",
        cacheable=True,
        cache_ttl_seconds=259200,
        max_output_tokens=1000,
        timeout_seconds=25,
        untrusted_input_delimiter=True,
    ),
    AITask.PROSPECT_QUALIFICATION.value: TaskDefinition(
        name=AITask.PROSPECT_QUALIFICATION.value,
        description="Evaluate prospect fit against ICP criteria",
        quality_tier="fast",
        cacheable=True,
        cache_ttl_seconds=259200,
        max_output_tokens=600,
        timeout_seconds=15,
        untrusted_input_delimiter=False,
    ),
    AITask.FACT_INTERPRETATION.value: TaskDefinition(
        name=AITask.FACT_INTERPRETATION.value,
        description="Interpret raw unstructured page text into candidate facts",
        quality_tier="standard",
        cacheable=True,
        cache_ttl_seconds=604800,
        max_output_tokens=1000,
        timeout_seconds=25,
        untrusted_input_delimiter=True,
    ),
    AITask.VERIFICATION_REASONING.value: TaskDefinition(
        name=AITask.VERIFICATION_REASONING.value,
        description="High-stakes reasoning on ambiguous verification evidence",
        quality_tier="high",
        cacheable=False,
        cache_ttl_seconds=0,
        max_output_tokens=1000,
        timeout_seconds=30,
        untrusted_input_delimiter=True,
    ),
    AITask.ENTITY_RESOLUTION_ASSIST.value: TaskDefinition(
        name=AITask.ENTITY_RESOLUTION_ASSIST.value,
        description="Disambiguate difficult entity merge candidates",
        quality_tier="high",
        cacheable=False,
        cache_ttl_seconds=0,
        max_output_tokens=800,
        timeout_seconds=25,
        untrusted_input_delimiter=False,
    ),
    AITask.EMAIL_PERSONALIZATION.value: TaskDefinition(
        name=AITask.EMAIL_PERSONALIZATION.value,
        description="Craft personalized multi-channel sales outreach sequence",
        quality_tier="standard",
        cacheable=False,
        cache_ttl_seconds=0,
        max_output_tokens=1200,
        timeout_seconds=25,
        untrusted_input_delimiter=True,
    ),
    AITask.REPLY_CLASSIFICATION.value: TaskDefinition(
        name=AITask.REPLY_CLASSIFICATION.value,
        description="Classify incoming prospect email reply intent",
        quality_tier="fast",
        cacheable=False,
        cache_ttl_seconds=0,
        max_output_tokens=300,
        timeout_seconds=10,
        untrusted_input_delimiter=True,
    ),
    AITask.REPLY_DRAFTING.value: TaskDefinition(
        name=AITask.REPLY_DRAFTING.value,
        description="Draft context-aware response to prospect reply",
        quality_tier="standard",
        cacheable=False,
        cache_ttl_seconds=0,
        max_output_tokens=800,
        timeout_seconds=20,
        untrusted_input_delimiter=True,
    ),
    AITask.MEETING_BRIEF.value: TaskDefinition(
        name=AITask.MEETING_BRIEF.value,
        description="Generate structured pre-meeting intelligence dossier",
        quality_tier="standard",
        cacheable=False,
        cache_ttl_seconds=0,
        max_output_tokens=1500,
        timeout_seconds=30,
        untrusted_input_delimiter=False,
    ),
    AITask.SIGNAL_INTERPRETATION.value: TaskDefinition(
        name=AITask.SIGNAL_INTERPRETATION.value,
        description="Evaluate hiring, funding, or technology signals",
        quality_tier="standard",
        cacheable=True,
        cache_ttl_seconds=86400,
        max_output_tokens=800,
        timeout_seconds=20,
        untrusted_input_delimiter=True,
    ),
    AITask.SUMMARY.value: TaskDefinition(
        name=AITask.SUMMARY.value,
        description="Fast summarization of document or web content",
        quality_tier="fast",
        cacheable=True,
        cache_ttl_seconds=604800,
        max_output_tokens=600,
        timeout_seconds=15,
        untrusted_input_delimiter=True,
    ),
    AITask.EXTRACTION.value: TaskDefinition(
        name=AITask.EXTRACTION.value,
        description="Structured attribute extraction from text",
        quality_tier="fast",
        cacheable=True,
        cache_ttl_seconds=604800,
        max_output_tokens=800,
        timeout_seconds=15,
        untrusted_input_delimiter=True,
    ),
    AITask.CLASSIFICATION.value: TaskDefinition(
        name=AITask.CLASSIFICATION.value,
        description="Fast category classification",
        quality_tier="fast",
        cacheable=True,
        cache_ttl_seconds=604800,
        max_output_tokens=200,
        timeout_seconds=10,
        untrusted_input_delimiter=True,
    ),
    AITask.EMBEDDING.value: TaskDefinition(
        name=AITask.EMBEDDING.value,
        description="Generate semantic vector embedding",
        quality_tier="fast",
        cacheable=True,
        cache_ttl_seconds=2592000,
        max_output_tokens=0,
        timeout_seconds=10,
        untrusted_input_delimiter=False,
    ),
    # Aliases
    AITask.ICP_SYNTHESIS.value: TaskDefinition(
        name=AITask.ICP_SYNTHESIS.value,
        description="Legacy alias for icp_generation",
        quality_tier="standard",
        cacheable=True,
        cache_ttl_seconds=604800,
        max_output_tokens=1200,
    ),
    AITask.EMAIL_COPYWRITING.value: TaskDefinition(
        name=AITask.EMAIL_COPYWRITING.value,
        description="Legacy alias for email_personalization",
        quality_tier="standard",
        cacheable=False,
    ),
    AITask.COMPANY_ENRICHMENT.value: TaskDefinition(
        name=AITask.COMPANY_ENRICHMENT.value,
        description="Legacy alias for company_analysis",
        quality_tier="standard",
        cacheable=True,
        cache_ttl_seconds=604800,
    ),
    AITask.DEEP_REASONING.value: TaskDefinition(
        name=AITask.DEEP_REASONING.value,
        description="Legacy alias for verification_reasoning",
        quality_tier="high",
        cacheable=False,
    ),
}


def get_task_definition(task: str) -> TaskDefinition:
    """Retrieves metadata definition for a task, with fallback default."""
    normalized = (task or "").strip().lower()
    if normalized in STANDARD_TASKS:
        return STANDARD_TASKS[normalized]
    return TaskDefinition(
        name=normalized or "unknown_task",
        description="Unregistered dynamic task",
        quality_tier="standard",
        cacheable=False,
        max_output_tokens=1000,
        timeout_seconds=30,
    )
