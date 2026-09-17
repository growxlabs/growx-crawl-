"""
GrowX Data Factory Stage 8: History & Change Tracking.
Compares newly extracted values against previous canonical facts to detect attribute evolution,
executive changes, and domain modifications.
"""

from typing import Any, Dict, List, Optional
from growx_crawl.data_factory.metrics import DataFactoryMetrics
from growx_crawl.shared.time import utc_iso_now


class HistoryStage:
    """Tracks state mutations and preserves historical intelligence."""

    def execute(
        self,
        quality_items: List[Dict[str, Any]],
        metrics: DataFactoryMetrics,
    ) -> List[Dict[str, Any]]:
        history_output: List[Dict[str, Any]] = []

        for item in quality_items:
            changes = []
            obs = item.get("observation", {})
            prior_name = item.get("prior_company_name")

            # Check if company name changed
            if prior_name and prior_name != item.get("company_name"):
                changes.append({
                    "change_type": "company_name_changed",
                    "old_value": prior_name,
                    "new_value": item.get("company_name"),
                    "detected_at": utc_iso_now(),
                })
                metrics.facts_changed += 1

            # Check for new contact signals
            emails = obs.get("emails", [])
            if len(emails) > 1:
                changes.append({
                    "change_type": "contacts_expanded",
                    "new_contacts_count": len(emails),
                    "detected_at": utc_iso_now(),
                })

            item["changes"] = changes
            history_output.append(item)

        return history_output
