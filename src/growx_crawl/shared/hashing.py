"""
GrowX Platform Standard Hashing Primitives.
Provides deterministic SHA-256 and checksum utilities.
"""

import hashlib
import json
from typing import Any, Union


def sha256_text(text: str) -> str:
    """Computes hexadecimal SHA-256 hash of a string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    """Computes hexadecimal SHA-256 hash of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def deterministic_json_hash(payload: Any) -> str:
    """Computes SHA-256 hash of a JSON payload with sorted keys."""
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return sha256_text(serialized)
