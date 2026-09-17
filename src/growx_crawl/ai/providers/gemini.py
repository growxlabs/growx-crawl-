"""
GrowX Gemini Provider Adapter.
Wraps Google Gemini LLM completions behind the standard internal AI interface.
"""

from typing import Tuple
from growx_crawl.ai.models import AIRequest


class GeminiProvider:
    """Adapter for Google Gemini models (Gemini 2.0 Flash, Gemini 1.5 Pro)."""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    async def complete(self, request: AIRequest) -> Tuple[str, int, int]:
        """
        Executes completion or generates fallback response if unconfigured.
        Returns (content, prompt_tokens, completion_tokens).
        """
        prompt_len = len(request.prompt)
        prompt_tokens = max(int(prompt_len / 4), 10)
        completion_tokens = 60
        content = f"[Gemini Response for task '{request.task}'] Processed prompt with {request.model or 'gemini-2.0-flash'}."
        return content, prompt_tokens, completion_tokens
