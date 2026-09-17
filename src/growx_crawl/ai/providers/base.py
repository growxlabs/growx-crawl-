"""
GrowX AI Provider Abstract Interface.
All model provider adapters (OpenAI, Gemini, Mock, Anthropic, etc.) must implement this contract.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple
from growx_crawl.ai.models import AIRequest, EmbeddingRequest


class BaseAIProvider(ABC):
    """Abstract base class for all AI Gateway provider adapters."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns the canonical provider name (e.g. 'openai', 'gemini', 'mock')."""
        pass

    @abstractmethod
    async def generate(self, request: AIRequest) -> Tuple[str, int, int]:
        """
        Executes raw text or structured prompt generation.
        Returns: (output_text, prompt_tokens, completion_tokens).
        """
        pass

    async def complete(self, request: AIRequest) -> Tuple[str, int, int]:
        """Backward-compatible alias for generate()."""
        return await self.generate(request)

    @abstractmethod
    async def embed(self, request: EmbeddingRequest) -> List[float]:
        """Generates a dense vector embedding for the input text."""
        pass

    @abstractmethod
    async def health(self) -> Dict[str, Any]:
        """Checks provider connectivity and authentication status."""
        pass
