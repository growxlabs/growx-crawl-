"""
GrowX AI Gateway.
The single authoritative gateway for all AI / LLM invocations in the system.
Orchestrates task routing, prompt rendering, provider abstraction, retry, fallback,
circuit breaker health, structured validation, cache, token/cost telemetry, and persistence.
"""

import time
from typing import Any, Dict, List, Optional
from growx_crawl.ai.cache import ai_cache, compute_ai_fingerprint
from growx_crawl.ai.circuit_breaker import circuit_breaker
from growx_crawl.ai.cost import calculate_ai_cost, enforce_cost_guard, estimate_request_cost
from growx_crawl.ai.errors import AIConfigurationError, AISchemaValidationError
from growx_crawl.ai.fallback import FallbackOption, execute_with_fallback
from growx_crawl.ai.models import (
    AIRequest,
    AIResponse,
    ClassificationRequest,
    EmbeddingRequest,
    EmbeddingResponse,
    RunStatus,
    StructuredAIRequest,
    SummaryRequest,
)
from growx_crawl.ai.prompt_registry import prompt_registry
from growx_crawl.ai.providers.gemini import GeminiProvider
from growx_crawl.ai.providers.mock import MockAIProvider
from growx_crawl.ai.providers.openai import OpenAIProvider
from growx_crawl.ai.repository import ai_repository
from growx_crawl.ai.retry import execute_with_retry
from growx_crawl.ai.router import provider_router
from growx_crawl.ai.structured import parse_and_validate_structured
from growx_crawl.ai.tasks import get_task_definition
from growx_crawl.ai.telemetry import ai_telemetry
from growx_crawl.shared.ids import generate_id
from growx_crawl.shared.time import utc_iso_now


class AIGateway:
    """Central AI boundary for the GrowX Platform."""

    def __init__(self):
        self.openai_provider = OpenAIProvider()
        self.gemini_provider = GeminiProvider()
        self.mock_provider = MockAIProvider()

    def _get_provider(self, provider_name: str):
        p = provider_name.lower()
        if p == "openai":
            return self.openai_provider
        elif p == "gemini":
            return self.gemini_provider
        elif p == "mock":
            return self.mock_provider
        raise AIConfigurationError(f"Unknown AI provider: '{provider_name}'")

    async def complete(self, request: AIRequest) -> AIResponse:
        """
        Backward-compatible execution entrypoint.
        Maintains exact parity with tests calling ai_gateway.complete(req).
        """
        return await self.generate(request)

    async def generate(self, request: AIRequest) -> AIResponse:
        """Executes canonical text prompt generation across providers with retries and fallbacks."""
        task_def = get_task_definition(request.task)

        # 1. Prompt rendering & injection defense
        prompt_text = request.prompt
        system_text = request.system_context
        prompt_ver = request.prompt_version or "v1"

        if request.input_data or not prompt_text:
            rendered = prompt_registry.render(
                task=request.task,
                version=prompt_ver,
                variables=request.input_data or {},
                wrap_untrusted=task_def.untrusted_input_delimiter,
            )
            prompt_text = prompt_text or rendered["prompt"]
            if not system_text:
                system_text = rendered["system"]
            prompt_ver = rendered["version"]

        # 2. Context & cost pre-flight guards
        est_cost = estimate_request_cost(request.model or "gemini-2.0-flash", len(prompt_text))
        enforce_cost_guard(est_cost, max_cost_limit_usd=1.00, task=request.task)

        # 3. Fingerprint & cache lookup
        schema_name = getattr(request, "schema_class", None).__name__ if hasattr(request, "schema_class") and request.schema_class else ""
        fingerprint = compute_ai_fingerprint(
            task=request.task,
            prompt=prompt_text,
            prompt_version=prompt_ver,
            model=request.model or "auto",
            schema_name=schema_name,
        )

        if task_def.cacheable and task_def.cache_ttl_seconds > 0:
            cached_res = ai_cache.get(fingerprint)
            if cached_res:
                ai_telemetry.record_run(cached_res)
                return cached_res

        # 4. Resolve fallback chain
        fallback_chain = provider_router.get_fallback_chain(
            task=request.task,
            requested_provider=request.provider,
            requested_model=request.model,
            requested_tier=request.quality_tier or task_def.quality_tier,
        )

        # 5. Invoker closure for execute_with_fallback
        async def _invoke_option(prov_name: str, mod_name: str, tier: str) -> AIResponse:
            provider = self._get_provider(prov_name)
            circuit_breaker.check_permission(prov_name)

            sub_request = AIRequest(
                task=request.task,
                prompt=prompt_text,
                system_context=system_text,
                prompt_id=request.prompt_id or request.task,
                prompt_version=prompt_ver,
                quality_tier=tier,
                provider=prov_name,
                model=mod_name,
                temperature=request.temperature,
                max_tokens=request.max_tokens or task_def.max_output_tokens,
                timeout_seconds=request.timeout_seconds or task_def.timeout_seconds,
                scope=request.scope,
                account_id=request.account_id,
                job_id=request.job_id,
                trace_id=request.trace_id,
                metadata_json=request.metadata_json,
            )

            async def _run():
                start_time = time.time()
                content, p_tokens, c_tokens = await provider.generate(sub_request)
                lat_ms = int((time.time() - start_time) * 1000)
                tot_tokens = p_tokens + c_tokens
                cost = calculate_ai_cost(mod_name, p_tokens, c_tokens)

                return AIResponse(
                    run_id=generate_id("ai_"),
                    content=content,
                    model=mod_name,
                    provider=prov_name,
                    task=request.task,
                    prompt_id=sub_request.prompt_id,
                    prompt_version=prompt_ver,
                    quality_tier=tier,
                    prompt_tokens=p_tokens,
                    completion_tokens=c_tokens,
                    total_tokens=tot_tokens,
                    cost_usd=cost,
                    latency_ms=lat_ms,
                    status=RunStatus.SUCCESS.value,
                    fingerprint=fingerprint,
                    created_at=utc_iso_now(),
                    metadata_json=request.metadata_json,
                )

            try:
                res = await execute_with_retry(_run, max_retries=2, task=request.task)
                circuit_breaker.record_success(prov_name)
                return res
            except Exception as e:
                circuit_breaker.record_failure(prov_name)
                raise e

        # Execute across fallback options
        response, fallback_used, fallback_reason = await execute_with_fallback(fallback_chain, _invoke_option)

        # 6. Record run telemetry and persistence
        ai_telemetry.record_run(response)
        ai_repository.save_run(response)

        # 7. Store in cache if enabled
        if task_def.cacheable and task_def.cache_ttl_seconds > 0:
            ai_cache.set(fingerprint, response, task_def.cache_ttl_seconds)

        return response

    async def generate_structured(self, request: StructuredAIRequest) -> AIResponse:
        """Executes completion, parses JSON output, repairs if necessary, and validates against Pydantic schema."""
        # Augment prompt with schema instructions if not already present
        if request.schema_class and "JSON" not in request.prompt:
            schema_fields = list(request.schema_class.model_fields.keys())
            request.prompt = f"{request.prompt}\n\nReturn strictly valid JSON with keys: {schema_fields}"

        response = await self.generate(request)

        # Parse & Validate structured data
        try:
            dict_data, _ = parse_and_validate_structured(
                response.content,
                schema_class=request.schema_class,
                task=request.task,
            )
            response.structured_output = dict_data
        except AISchemaValidationError as e:
            # Check if repair retry is allowed
            if request.repair_attempts > 0:
                repair_prompt = (
                    f"The previous output failed JSON/schema validation: {e.message}\n"
                    f"Fix and return ONLY the valid JSON:\n{response.content}"
                )
                repair_req = AIRequest(
                    task=request.task,
                    prompt=repair_prompt,
                    quality_tier=request.quality_tier,
                    temperature=0.1,
                )
                repair_res = await self.generate(repair_req)
                dict_data, _ = parse_and_validate_structured(
                    repair_res.content,
                    schema_class=request.schema_class,
                    task=request.task,
                )
                response.structured_output = dict_data
            else:
                response.status = RunStatus.FAILED.value
                response.error_code = "SCHEMA_VALIDATION_ERROR"
                ai_repository.save_run(response)
                raise e

        return response

    async def classify(self, request: ClassificationRequest) -> AIResponse:
        """Executes classification prompt against specified categories."""
        cats_str = ", ".join(request.categories) if request.categories else "GENERAL"
        augmented_prompt = f"{request.prompt}\nCategories: [{cats_str}]. Respond with selected category."
        sub_req = AIRequest(
            task=request.task or "classification",
            prompt=augmented_prompt,
            temperature=0.1,
            max_tokens=200,
        )
        return await self.generate(sub_req)

    async def summarize(self, request: SummaryRequest) -> AIResponse:
        """Executes text summarization with word count constraint."""
        prompt = f"Summarize the following text in under {request.max_words} words:\n\n{request.text}"
        sub_req = AIRequest(
            task=request.task or "summary",
            prompt=prompt,
            temperature=0.3,
            max_tokens=request.max_words * 3,
        )
        return await self.generate(sub_req)

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generates dense vector embedding through selected provider."""
        start_time = time.time()
        provider = self._get_provider(request.provider)
        embedding_vec = await provider.embed(request)
        lat_ms = int((time.time() - start_time) * 1000)
        tokens = max(int(len(request.input_text) / 4), 1)
        cost = calculate_ai_cost(request.model, tokens, 0)

        return EmbeddingResponse(
            run_id=generate_id("ai_"),
            embedding=embedding_vec,
            dimensions=len(embedding_vec),
            tokens=tokens,
            cost_usd=cost,
            latency_ms=lat_ms,
            provider=request.provider,
            model=request.model,
        )


ai_gateway = AIGateway()
