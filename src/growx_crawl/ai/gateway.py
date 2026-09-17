"""
GrowX AI Gateway.
The single authoritative gateway for all AI / LLM invocations in the system.
Enforces model routing, prompt versioning, token telemetry, cost accounting, and latency metrics.
"""

import time
from typing import Optional
from growx_crawl.ai.cost import calculate_ai_cost
from growx_crawl.ai.models import AIRequest, AIResponse
from growx_crawl.ai.providers.gemini import GeminiProvider
from growx_crawl.ai.providers.openai import OpenAIProvider
from growx_crawl.ai.router import route_request
from growx_crawl.ai.telemetry import ai_telemetry
from growx_crawl.shared.ids import generate_id


class AIGateway:
    """Central AI boundary for the GrowX Platform."""

    def __init__(self):
        self.openai_provider = OpenAIProvider()
        self.gemini_provider = GeminiProvider()

    async def complete(self, request: AIRequest) -> AIResponse:
        start_time = time.time()
        provider, model = route_request(request.task, request.provider or "", request.model or "")

        # Execute through provider
        if provider == "openai":
            content, prompt_tokens, completion_tokens = await self.openai_provider.complete(request)
        else:
            content, prompt_tokens, completion_tokens = await self.gemini_provider.complete(request)

        latency_ms = int((time.time() - start_time) * 1000)
        total_tokens = prompt_tokens + completion_tokens
        cost = calculate_ai_cost(model, prompt_tokens, completion_tokens)

        response = AIResponse(
            run_id=generate_id("ai_"),
            content=content,
            model=model,
            provider=provider,
            task=request.task,
            prompt_version=request.prompt_version,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=cost,
            latency_ms=latency_ms,
        )

        ai_telemetry.record_run(response)
        return response


ai_gateway = AIGateway()
