"""
GrowX Data Factory Crawl Prioritizer.
Assigns priority tiers (P0 -> P4) to discovery, crawl, and refresh items
ensuring high-value GTM targets execute first before quota exhaustion.
"""

from typing import Any, Dict, List
from growx_crawl.data_factory.models import PriorityTier


class CrawlPrioritizer:
    """Classifies and orders work items by strategic value and freshness urgency."""

    PRIORITY_WEIGHTS = {
        PriorityTier.P0: 0,
        PriorityTier.P1: 1,
        PriorityTier.P2: 2,
        PriorityTier.P3: 3,
        PriorityTier.P4: 4,
    }

    @classmethod
    def determine_priority(cls, item: Dict[str, Any]) -> PriorityTier:
        # P0: Active GTM campaign target or urgent manual flag
        if item.get("is_active_campaign") or item.get("urgent") or item.get("priority") == "P0":
            return PriorityTier.P0

        # P1: High-fit ICP candidate or known high-value stale record
        if item.get("is_high_fit") or item.get("is_stale_customer") or item.get("priority") == "P1":
            return PriorityTier.P1

        # P2: Fresh discovery from active target segment
        if item.get("is_new_discovery") or item.get("segment") or item.get("priority") == "P2":
            return PriorityTier.P2

        # P3: Routine background refresh
        if item.get("is_background_refresh") or item.get("priority") == "P3":
            return PriorityTier.P3

        # P4: Fallback / low-value archive
        return PriorityTier.P4

    @classmethod
    def prioritize_items(cls, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sorts a collection of candidate items by PriorityTier ascending (P0 first)."""
        def sort_key(item: Dict[str, Any]) -> int:
            p = cls.determine_priority(item)
            return cls.PRIORITY_WEIGHTS.get(p, 5)

        return sorted(items, key=sort_key)
