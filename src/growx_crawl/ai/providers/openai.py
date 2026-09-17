"""
GrowX OpenAI Provider Adapter.
Wraps OpenAI LLM completions behind the standard BaseAIProvider interface.
"""

import os
from typing import Any, Dict, List, Optional, Tuple
import httpx
from growx_crawl.ai.errors import AIInvalidResponse, AIRateLimited, AITimeout, AIProviderUnavailable
from growx_crawl.ai.models import AIRequest, EmbeddingRequest
from growx_crawl.ai.providers.base import BaseAIProvider


class OpenAIProvider(BaseAIProvider):
    """Adapter for OpenAI models (GPT-4o, GPT-4o-mini, text-embedding-3-small)."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")

    @property
    def provider_name(self) -> str:
        return "openai"

    async def generate(self, request: AIRequest) -> Tuple[str, int, int]:
        model = request.model or "gpt-4o-mini"
        if not self.api_key:
            # Fallback mock mode when no API key is configured
            prompt_len = len(request.prompt)
            prompt_tokens = max(int(prompt_len / 4), 10)
            completion_tokens = 50
            content = f"[OpenAI Response for task '{request.task}'] Processed prompt with {model}."
            return content, prompt_tokens, completion_tokens

        timeout_sec = request.timeout_seconds or 30.0
        endpoint = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if request.system_context:
            messages.append({"role": "system", "content": request.system_context})
        messages.append({"role": "user", "content": request.prompt})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }

        try:
            async with httpx.AsyncClient(timeout=timeout_sec) as client:
                res = await client.post(endpoint, headers=headers, json=payload)
                if res.status_code == 429:
                    retry_after = res.headers.get("retry-after")
                    retry_sec = float(retry_after) if retry_after else 1.0
                    raise AIRateLimited(
                        "OpenAI rate limit exceeded",
                        provider=self.provider_name,
                        task=request.task,
                        retry_after_seconds=retry_sec,
                    )
                elif res.status_code >= 500:
                    raise AIProviderUnavailable(
                        f"OpenAI server error: {res.status_code}",
                        provider=self.provider_name,
                        task=request.task,
                    )
                elif res.status_code != 200:
                    raise AIInvalidResponse(
                        f"OpenAI API error ({res.status_code}): {res.text[:200]}",
                        provider=self.provider_name,
                        task=request.task,
                    )

                data = res.json()
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", int(len(request.prompt) / 4))
                completion_tokens = usage.get("completion_tokens", int(len(content) / 4))
                return content, prompt_tokens, completion_tokens

        except httpx.TimeoutException:
            raise AITimeout(f"OpenAI request timed out after {timeout_sec}s", provider=self.provider_name, task=request.task)
        except (AIRateLimited, AIProviderUnavailable, AIInvalidResponse, AITimeout):
            raise
        except Exception as e:
            raise AIProviderUnavailable(f"OpenAI network error: {e}", provider=self.provider_name, task=request.task)

    async def embed(self, request: EmbeddingRequest) -> List[float]:
        if not self.api_key:
            return [0.05] * 1536

        endpoint = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": request.model or "text-embedding-3-small",
            "input": request.input_text,
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(endpoint, headers=headers, json=payload)
                if res.status_code == 200:
                    return res.json()["data"][0]["embedding"]
                raise AIInvalidResponse(f"OpenAI embedding failed: {res.status_code}", provider=self.provider_name)
        except Exception as e:
            raise AIProviderUnavailable(f"OpenAI embedding error: {e}", provider=self.provider_name)

    async def health(self) -> Dict[str, Any]:
        return {
            "provider": self.provider_name,
            "configured": bool(self.api_key),
            "status": "healthy" if self.api_key else "mock_fallback",
        }
