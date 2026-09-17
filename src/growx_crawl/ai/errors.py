"""
GrowX AI Gateway Standard Errors.
Provides normalized error hierarchy so domain callers never catch provider-specific exceptions.
"""

from typing import Optional


class AIError(Exception):
    """Base exception for all AI Gateway operations."""

    def __init__(self, message: str, provider: str = "", task: str = "", retryable: bool = False):
        super().__init__(message)
        self.message = message
        self.provider = provider
        self.task = task
        self.retryable = retryable


class AITimeout(AIError):
    """Raised when an AI provider call times out."""

    def __init__(self, message: str = "AI request timed out", provider: str = "", task: str = ""):
        super().__init__(message, provider=provider, task=task, retryable=True)


class AIRateLimited(AIError):
    """Raised when an AI provider responds with HTTP 429 rate limit exceeded."""

    def __init__(
        self,
        message: str = "AI provider rate limit exceeded",
        provider: str = "",
        task: str = "",
        retry_after_seconds: Optional[float] = None,
    ):
        super().__init__(message, provider=provider, task=task, retryable=True)
        self.retry_after_seconds = retry_after_seconds


class AIProviderUnavailable(AIError):
    """Raised when provider cannot be contacted or returns 5xx server errors."""

    def __init__(self, message: str = "AI provider is unavailable", provider: str = "", task: str = ""):
        super().__init__(message, provider=provider, task=task, retryable=True)


class AICircuitBreakerOpen(AIError):
    """Raised when request is blocked because the provider circuit breaker is OPEN."""

    def __init__(self, provider: str, reset_in_seconds: float = 0.0):
        super().__init__(
            f"Circuit breaker is OPEN for provider '{provider}'. Requests blocked for {reset_in_seconds:.1f}s",
            provider=provider,
            retryable=False,
        )
        self.reset_in_seconds = reset_in_seconds


class AIInvalidResponse(AIError):
    """Raised when provider returns an empty, corrupted, or unparsable response."""

    def __init__(self, message: str = "Invalid response from AI provider", provider: str = "", task: str = ""):
        super().__init__(message, provider=provider, task=task, retryable=False)


class AISchemaValidationError(AIError):
    """Raised when structured AI output fails schema validation and cannot be repaired."""

    def __init__(
        self,
        message: str = "AI output failed structured schema validation",
        raw_output: str = "",
        schema_name: str = "",
        task: str = "",
    ):
        super().__init__(message, task=task, retryable=False)
        self.raw_output = raw_output
        self.schema_name = schema_name


class AIBudgetExceeded(AIError):
    """Raised when request estimated cost or token usage exceeds configured budget guards."""

    def __init__(self, message: str = "AI budget threshold exceeded", task: str = "", cost_usd: float = 0.0):
        super().__init__(message, task=task, retryable=False)
        self.cost_usd = cost_usd


class AIConfigurationError(AIError):
    """Raised when requested model, task, or provider configuration is invalid."""

    def __init__(self, message: str):
        super().__init__(message, retryable=False)
