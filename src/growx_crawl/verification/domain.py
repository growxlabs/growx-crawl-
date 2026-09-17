"""
GrowX Domain Verification.
Validates DNS host reachability and registrable domain status.
"""

import asyncio
from typing import Any, Dict
from growx_crawl.normalization.domain import normalize_domain
from growx_crawl.shared.ids import generate_id
from growx_crawl.verification.models import VerificationResultEntity, VerificationStatus


async def verify_domain(domain_str: str) -> VerificationResultEntity:
    """Verifies that a domain resolves via DNS."""
    clean = normalize_domain(domain_str)
    if not clean:
        return VerificationResultEntity(
            id=generate_id("ver_"),
            entity_type="domain",
            entity_id=domain_str,
            status=VerificationStatus.FAILED,
            confidence=0.0,
            details_json={"error": "Empty or malformed domain"},
        )

    loop = asyncio.get_running_loop()
    try:
        await loop.getaddrinfo(clean, 80)
        return VerificationResultEntity(
            id=generate_id("ver_"),
            entity_type="domain",
            entity_id=clean,
            status=VerificationStatus.VERIFIED,
            confidence=1.0,
            details_json={"resolved_host": clean},
        )
    except Exception as e:
        return VerificationResultEntity(
            id=generate_id("ver_"),
            entity_type="domain",
            entity_id=clean,
            status=VerificationStatus.UNVERIFIED,
            confidence=0.2,
            details_json={"dns_error": str(e)},
        )
