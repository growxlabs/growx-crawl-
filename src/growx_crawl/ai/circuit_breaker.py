"""
GrowX AI Circuit Breaker.
Tracks provider health, opens circuit on consecutive transient failures, and prevents cascading outages.
"""

import time
from enum import Enum
from typing import Dict
from growx_crawl.ai.errors import AICircuitBreakerOpen


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Per-provider circuit breaker state machine."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout_seconds: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self._states: Dict[str, CircuitState] = {}
        self._failure_counts: Dict[str, int] = {}
        self._last_state_change: Dict[str, float] = {}

    def get_state(self, provider: str) -> CircuitState:
        state = self._states.get(provider, CircuitState.CLOSED)
        if state == CircuitState.OPEN:
            elapsed = time.time() - self._last_state_change.get(provider, 0.0)
            if elapsed >= self.recovery_timeout_seconds:
                self._states[provider] = CircuitState.HALF_OPEN
                return CircuitState.HALF_OPEN
        return state

    def check_permission(self, provider: str) -> None:
        """Verifies if request to provider is allowed; raises AICircuitBreakerOpen if blocked."""
        state = self.get_state(provider)
        if state == CircuitState.OPEN:
            elapsed = time.time() - self._last_state_change.get(provider, 0.0)
            remaining = max(0.0, self.recovery_timeout_seconds - elapsed)
            raise AICircuitBreakerOpen(provider=provider, reset_in_seconds=remaining)

    def record_success(self, provider: str) -> None:
        self._failure_counts[provider] = 0
        self._states[provider] = CircuitState.CLOSED

    def record_failure(self, provider: str) -> None:
        count = self._failure_counts.get(provider, 0) + 1
        self._failure_counts[provider] = count
        if count >= self.failure_threshold:
            self._states[provider] = CircuitState.OPEN
            self._last_state_change[provider] = time.time()

    def reset(self, provider: str) -> None:
        self._failure_counts[provider] = 0
        self._states[provider] = CircuitState.CLOSED


circuit_breaker = CircuitBreaker()
