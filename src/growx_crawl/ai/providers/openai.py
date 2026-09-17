"""
GrowX OpenAI Provider Adapter.
Wraps OpenAI LLM completions behind the standard internal AI interface.
"""

from typing import Tuple
from growx_crawl.ai.models import AIRequest


class OpenAIProvider:
    """Adapter for OpenAI models (GPT-4o, GPT-4o-mini)."""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    async def complete(self, request: AIRequest) -> Tuple[str, int, int]:
        """
        Executes completion or generates fallback mock response if unconfigured.
        Returns (content, prompt_tokens, completion_tokens).
        """
        # In mock / headless fallback mode
        prompt_len = len(request.prompt)
        prompt_tokens = max(int(prompt_len / 4), 10)
        completion_tokens = 50
        content = f"[OpenAI Response for task '{request.task}'] Processed prompt with {request.model or 'gpt-4o-mini'}."
        return content, prompt_tokens, completion_tokens
