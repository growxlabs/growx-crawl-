"""
GrowX Gemini Provider Adapter.
Wraps Google Gemini LLM completions behind the standard BaseAIProvider interface.
"""

import os
from typing import Any, Dict, List, Optional, Tuple
import httpx
from growx_crawl.ai.errors import AIInvalidResponse, AIRateLimited, AITimeout, AIProviderUnavailable
from growx_crawl.ai.models import AIRequest, EmbeddingRequest
from growx_crawl.ai.providers.base import BaseAIProvider


class GeminiProvider(BaseAIProvider):
    """Adapter for Google Gemini models (Gemini 2.0 Flash, Gemini 1.5 Pro, Gemini 1.5 Flash)."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")

    @property
    def provider_name(self) -> str:
        return "gemini"

    async def generate(self, request: AIRequest) -> Tuple[str, int, int]:
        model = request.model or "gemini-2.0-flash"
        if not self.api_key:
            # Fallback mock mode when no API key is configured
            prompt_len = len(request.prompt)
            prompt_tokens = max(int(prompt_len / 4), 10)
            completion_tokens = 60
            content = f"[Gemini Response for task '{request.task}'] Processed prompt with {model}."
            return content, prompt_tokens, completion_tokens

        timeout_sec = request.timeout_seconds or 30.0
        # Google Generative Language API endpoint
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}

        contents = []
        if request.system_context:
            contents.append({"role": "user", "parts": [{"text": f"SYSTEM INSTRUCTIONS: {request.system_context}"}]})
        contents.append({"role": "user", "parts": [{"text": request.prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=timeout_sec) as client:
                res = await client.post(url, headers=headers, json=payload)
                if res.status_code == 429:
                    raise AIRateLimited(
                        "Gemini rate limit exceeded",
                        provider=self.provider_name,
                        task=request.task,
                        retry_after_seconds=1.0,
                    )
                elif res.status_code >= 500:
                    raise AIProviderUnavailable(
                        f"Gemini server error: {res.status_code}",
                        provider=self.provider_name,
                        task=request.task,
                    )
                elif res.status_code != 200:
                    raise AIInvalidResponse(
                        f"Gemini API error ({res.status_code}): {res.text[:200]}",
                        provider=self.provider_name,
                        task=request.task,
                    )

                data = res.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    raise AIInvalidResponse("Gemini returned no candidates", provider=self.provider_name, task=request.task)

                parts = candidates[0].get("content", {}).get("parts", [])
                content = parts[0].get("text", "") if parts else ""
                usage = data.get("usageMetadata", {})
                prompt_tokens = usage.get("promptTokenCount", int(len(request.prompt) / 4))
                completion_tokens = usage.get("candidatesTokenCount", int(len(content) / 4))
                return content, prompt_tokens, completion_tokens

        except httpx.TimeoutException:
            raise AITimeout(f"Gemini request timed out after {timeout_sec}s", provider=self.provider_name, task=request.task)
        except (AIRateLimited, AIProviderUnavailable, AIInvalidResponse, AITimeout):
            raise
        except Exception as e:
            raise AIProviderUnavailable(f"Gemini network error: {e}", provider=self.provider_name, task=request.task)

    async def embed(self, request: EmbeddingRequest) -> List[float]:
        return [0.03] * 768

    async def health(self) -> Dict[str, Any]:
        return {
            "provider": self.provider_name,
            "configured": bool(self.api_key),
            "status": "healthy" if self.api_key else "mock_fallback",
        }
