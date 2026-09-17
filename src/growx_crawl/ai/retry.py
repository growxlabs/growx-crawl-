"""
GrowX AI Retry Policy.
Implements bounded exponential backoff with jitter for transient provider failures.
"""

import asyncio
import logging
import random
from typing import Any, Callable, Coroutine, Optional
from growx_crawl.ai.errors import AIError, AIRateLimited, AITimeout, AIProviderUnavailable

logger = logging.getLogger("growx_crawl.ai.retry")


def is_retryable_error(exc: Exception) -> bool:
    """Evaluates whether an exception is transient and safe to retry."""
    if isinstance(exc, (AITimeout, AIRateLimited, AIProviderUnavailable)):
        return True
    if isinstance(exc, AIError) and exc.retryable:
        return True
    return False


async def execute_with_retry(
    coro_fn: Callable[[], Coroutine[Any, Any, Any]],
    max_retries: int = 2,
    initial_delay: float = 0.2,
    backoff_factor: float = 2.0,
    max_delay: float = 5.0,
    task: str = "",
) -> Any:
    """
    Executes an async callable with bounded exponential backoff on transient errors.
    Non-retryable errors are re-raised immediately without burning additional attempts.
    """
    last_error: Optional[Exception] = None

    for attempt in range(max_retries + 1):
        try:
            return await coro_fn()
        except Exception as e:
            last_error = e
            if attempt == max_retries or not is_retryable_error(e):
                logger.warning(f"[AI_RETRY] Fatal or non-retryable error on attempt {attempt+1}/{max_retries+1}: {e}")
                raise e

            # Compute backoff with jitter
            if isinstance(e, AIRateLimited) and e.retry_after_seconds:
                delay = min(e.retry_after_seconds, max_delay)
            else:
                base_delay = initial_delay * (backoff_factor ** attempt)
                jitter = random.uniform(0.05, 0.2)
                delay = min(base_delay + jitter, max_delay)

            logger.info(
                f"[AI_RETRY] Transient failure on task '{task}' (attempt {attempt+1}): {e}. Retrying in {delay:.2f}s..."
            )
            await asyncio.sleep(delay)

    if last_error:
        raise last_error
