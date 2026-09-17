"""
GrowX Data Factory Refresh Planner.
Identifies stale companies, domains, employments, and facts based on TTL policies,
scheduling targeted lightweight updates rather than wasteful full-site re-crawls.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from growx_crawl.data_factory.models import CrawlMode, PriorityTier
from growx_crawl.shared.time import parse_iso, utc_now


class RefreshPlanner:
    """Calculates entity staleness and compiles targeted refresh candidates."""

    DEFAULT_TTL_DAYS = {
        "domain": 30,
        "company": 60,
        "employment": 90,
        "facts": 120,
    }

    @classmethod
    def is_stale(
        cls,
        timestamp_iso: Optional[str],
        ttl_days: int = 30,
    ) -> bool:
        if not timestamp_iso:
            return True
        dt = parse_iso(timestamp_iso)
        if not dt:
            return True
        age_days = (utc_now() - dt).total_seconds() / 86400.0
        return age_days >= ttl_days

    @classmethod
    def identify_refresh_candidates(
        cls,
        entities: List[Dict[str, Any]],
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        """
        Evaluates a batch of entity metadata records and selects candidates
        requiring targeted refresh based on last_crawled_at and last_verified_at.
        """
        candidates: List[Dict[str, Any]] = []

        for ent in entities:
            domain = ent.get("domain") or ent.get("normalized_domain")
            if not domain:
                continue

            last_crawled = ent.get("last_crawled_at")
            last_verified = ent.get("last_verified_at")

            needs_crawl = cls.is_stale(last_crawled, ttl_days=cls.DEFAULT_TTL_DAYS["domain"])
            needs_verification = cls.is_stale(last_verified, ttl_days=cls.DEFAULT_TTL_DAYS["company"])

            if needs_crawl or needs_verification:
                candidates.append({
                    "domain": domain,
                    "company_id": ent.get("id"),
                    "company_name": ent.get("canonical_name") or ent.get("name"),
                    "needs_crawl": needs_crawl,
                    "needs_verification": needs_verification,
                    "crawl_mode": CrawlMode.REFRESH,
                    "priority": PriorityTier.P1 if ent.get("is_high_fit") else PriorityTier.P3,
                    "is_background_refresh": True,
                })

            if len(candidates) >= limit:
                break

        return candidates
