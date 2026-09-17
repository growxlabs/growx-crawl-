"""
GrowX ICP Refresh Engine.
Detects staleness, seller fact mutations, and market drift to trigger version refresh recommendations.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from growx_crawl.intelligence.icp.models import (
    ICPCompanyScoreEntity,
    ICPEntity,
    ICPVersionEntity,
    SellerSnapshotEntity,
)
from growx_crawl.shared.time import utc_iso_now


class ICPRefreshEngine:
    """Evaluates whether an ICP or scored prospects require refresh."""

    def __init__(self, default_max_age_days: int = 90):
        self.default_max_age_days = default_max_age_days

    def evaluate_icp_staleness(
        self,
        icp: ICPEntity,
        active_version: Optional[ICPVersionEntity],
        snapshot: Optional[SellerSnapshotEntity] = None,
        current_seller_data: Optional[Dict[str, Any]] = None,
        current_seller_facts: Optional[List[Any]] = None,
        max_age_days: Optional[int] = None,
    ) -> Tuple[bool, List[str]]:
        """
        Evaluates whether an active ICP version is stale or out of sync with seller reality.
        Returns (needs_refresh, reasons).
        """
        threshold = max_age_days if max_age_days is not None else self.default_max_age_days
        reasons: List[str] = []

        if not active_version:
            return True, ["No active ICP version found."]

        # 1. Temporal Age Check
        created_dt = None
        if active_version.created_at:
            try:
                # Handle ISO format strings
                iso_str = active_version.created_at.replace("Z", "+00:00")
                created_dt = datetime.fromisoformat(iso_str)
            except Exception:
                pass

        if created_dt:
            age_days = (datetime.now(timezone.utc) - created_dt).days
            if age_days > threshold:
                reasons.append(
                    f"Active version is {age_days} days old (exceeds threshold of {threshold} days)."
                )

        # 2. Seller Context & Fact Mutation Check
        if snapshot and current_seller_data:
            snap_data = snapshot.fact_snapshot_json.get("seller_data", {})
            
            # Industry / Category drift
            snap_ind = snap_data.get("industry") or snap_data.get("categories")
            curr_ind = current_seller_data.get("industry") or current_seller_data.get("categories")
            if snap_ind and curr_ind and snap_ind != curr_ind:
                reasons.append(
                    f"Seller industry/category changed from '{snap_ind}' to '{curr_ind}'."
                )

            # Products / Offerings drift
            snap_prods = set(snap_data.get("products") or snap_data.get("offerings") or [])
            curr_prods = set(current_seller_data.get("products") or current_seller_data.get("offerings") or [])
            if snap_prods and curr_prods and snap_prods != curr_prods:
                added = curr_prods - snap_prods
                removed = snap_prods - curr_prods
                if added:
                    reasons.append(f"Seller added new products/offerings: {list(added)}.")
                if removed:
                    reasons.append(f"Seller discontinued products/offerings: {list(removed)}.")

        # 3. Fact verification mutations
        if snapshot and current_seller_facts:
            snap_facts = snapshot.fact_snapshot_json.get("facts", [])
            if len(snap_facts) != len(current_seller_facts):
                reasons.append(
                    f"Seller verified facts count changed from {len(snap_facts)} to {len(current_seller_facts)}."
                )

        needs_refresh = len(reasons) > 0
        return needs_refresh, reasons

    def should_rescore_company(
        self,
        last_score: Optional[ICPCompanyScoreEntity],
        current_fingerprint: str,
    ) -> bool:
        """Determines if a prospect company must be rescored based on cache fingerprint."""
        if not last_score:
            return True
        return last_score.fingerprint != current_fingerprint
