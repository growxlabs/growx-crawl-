"""
GrowX Quality Fingerprint Engine.
Computes deterministic SHA-256 state fingerprints for evaluation idempotency and caching.
"""

from typing import Any, Dict
from growx_crawl.shared.hashing import deterministic_json_hash, sha256_text


def compute_quality_fingerprint(
    subject_type: str,
    subject_id: str,
    gate_type: str,
    policy_version: str,
    data: Dict[str, Any],
) -> str:
    """Computes a SHA-256 fingerprint representing the exact input state of an evaluation."""
    data_hash = deterministic_json_hash(data)
    combined = f"{subject_type}:{subject_id}:{gate_type}:{policy_version}:{data_hash}"
    return sha256_text(combined)
