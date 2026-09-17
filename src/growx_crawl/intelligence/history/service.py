"""
GrowX Fact History Service.
Provides audit and change querying for canonical facts over time.
"""

from typing import Any, Dict, List, Optional
from growx_crawl.intelligence.history.change_detector import detect_value_change


class HistoryService:
    """Service boundary for retrieving fact history, diffing changes, and timeline queries."""

    def diff_fact_values(
        self,
        old_value: Any,
        new_value: Any,
        predicate: str,
    ) -> Optional[Dict[str, Any]]:
        return detect_value_change(old_value, new_value, predicate)


history_service = HistoryService()
