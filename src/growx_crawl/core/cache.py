import time
from typing import Any, Dict, Optional, Tuple


class ResponseCache:
    """
    In-memory response cache with configurable Time-To-Live (TTL).
    """

    def __init__(self, default_ttl_seconds: int = 3600):
        self.default_ttl = default_ttl_seconds
        self._cache: Dict[str, Tuple[float, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        if key not in self._cache:
            return None
        expires_at, value = self._cache[key]
        if time.time() > expires_at:
            del self._cache[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        expires_at = time.time() + ttl
        self._cache[key] = (expires_at, value)

    def clear(self) -> None:
        self._cache.clear()

    def size(self) -> int:
        now = time.time()
        # Clean expired keys
        expired = [k for k, (exp, _) in self._cache.items() if now > exp]
        for k in expired:
            del self._cache[k]
        return len(self._cache)


cache = ResponseCache(default_ttl_seconds=3600)
