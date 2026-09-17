"""
GrowX Intelligence History Package.
"""

from growx_crawl.intelligence.history.change_detector import detect_value_change
from growx_crawl.intelligence.history.service import HistoryService, history_service

__all__ = [
    "detect_value_change",
    "HistoryService",
    "history_service",
]
