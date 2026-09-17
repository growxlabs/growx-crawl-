"""
GrowX Mock AI Provider.
Provides deterministic, zero-cost, offline responses for unit tests, CI pipelines, and local development.
"""

import json
from typing import Any, Dict, List, Optional, Tuple
from growx_crawl.ai.errors import AIRateLimited, AITimeout, AIProviderUnavailable
from growx_crawl.ai.models import AIRequest, EmbeddingRequest
from growx_crawl.ai.providers.base import BaseAIProvider


class MockAIProvider(BaseAIProvider):
    """Deterministic offline mock provider with error simulation support."""

    def __init__(self):
        self.error_to_simulate: Optional[str] = None
        self.simulated_failures_remaining: int = 0

    @property
    def provider_name(self) -> str:
        return "mock"

    def set_error_simulation(self, error_type: Optional[str], count: int = 1) -> None:
        """Configures mock to simulate transient or permanent errors for testing."""
        self.error_to_simulate = error_type
        self.simulated_failures_remaining = count

    async def generate(self, request: AIRequest) -> Tuple[str, int, int]:
        # Handle error simulation
        if self.error_to_simulate and self.simulated_failures_remaining > 0:
            self.simulated_failures_remaining -= 1
            err = self.error_to_simulate
            if self.simulated_failures_remaining == 0:
                self.error_to_simulate = None

            if err == "timeout":
                raise AITimeout("Simulated timeout", provider="mock", task=request.task)
            elif err == "rate_limit":
                raise AIRateLimited("Simulated 429 rate limit", provider="mock", task=request.task, retry_after_seconds=0.05)
            elif err == "500":
                raise AIProviderUnavailable("Simulated 500 server error", provider="mock", task=request.task)
            elif err == "invalid_json":
                return "This is clearly not json {broken", 20, 10

        prompt_tokens = max(int(len(request.prompt) / 4), 10)
        completion_tokens = 50

        # Deterministic responses based on task
        task = request.task
        if task in ("company_analysis", "company_enrichment"):
            content = json.dumps({
                "company_name": "Acme Corp",
                "tagline": "AI-Powered B2B Growth Engine",
                "summary": "Acme Corp builds modern data infrastructure for enterprise sales teams.",
                "primary_offer": "Enterprise Autonomous Sales Pipeline",
                "value_proposition": "10x outbound pipeline with verified contacts",
                "target_audience": ["B2B SaaS", "Fintech", "HealthTech"],
                "features": ["Autonomous Crawling", "Email Verification", "AI Personalization"],
                "pricing_model": "Subscription SaaS",
                "tech_stack": ["Python", "FastAPI", "Postgres"],
                "recent_announcements": ["Series A Funding Raised"],
            })
            completion_tokens = 120
        elif task in ("email_personalization", "email_copywriting"):
            content = json.dumps({
                "email_subject": "quick question re Acme Corp",
                "email_body": "Saw your recent expansion — very impressive. Most growth leaders tell us outbound bounce rates hurt domain reputation. We fixed this at GrowX. Open to a 3-minute custom pipeline teardown?",
                "email_followup_1": "Following up on my note below regarding Acme Corp pipeline automation.",
                "email_followup_2": "Assuming outbound automation is not a priority right now. Wishing you continued momentum.",
                "linkedin_note": "Loved seeing Acme Corp's recent momentum. Let's connect!",
                "twitter_dm": "Put together a quick outbound pipeline teardown for Acme Corp. Mind if I send it over?",
            })
            completion_tokens = 110
        elif task in ("icp_generation", "icp_synthesis"):
            content = json.dumps({
                "target_industries": ["B2B SaaS", "Cloud Software", "Fintech"],
                "company_size": ["11-50 employees", "51-200 employees"],
                "target_roles": ["VP of Sales", "Head of Growth", "CRO"],
                "pain_points": ["High bounce rates", "Manual prospect research", "Low reply rates"],
                "trigger_events": ["Series A funding", "New VP of Sales hire"],
            })
            completion_tokens = 90
        elif task == "verification_reasoning":
            content = json.dumps({
                "assessment": "genuine_and_current",
                "confidence": 0.92,
                "reasoning": "Consistent domain records, official email matching company domain, and active LinkedIn presence.",
                "recommendation": "ALLOW",
            })
            completion_tokens = 60
        elif task == "reply_classification":
            content = json.dumps({
                "intent": "INTERESTED",
                "confidence": 0.95,
                "sentiment": "positive",
                "requires_human_attention": True,
            })
            completion_tokens = 40
        else:
            content = f"[Mock AI Response for task '{request.task}'] Processed prompt with {request.model or 'mock-model'}."

        return content, prompt_tokens, completion_tokens

    async def embed(self, request: EmbeddingRequest) -> List[float]:
        # Return deterministic mock 8-dim embedding vector
        return [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]

    async def health(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "provider": "mock",
            "mode": "deterministic_offline",
        }
