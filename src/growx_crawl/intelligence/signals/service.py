"""
GrowX Signal Service.
Owns buying signal detection, storage, and retrieval.
"""

from typing import Any, Dict, List
from growx_crawl.intelligence.signals.detectors import detect_signals_from_company
from growx_crawl.intelligence.signals.models import SignalEntity


class SignalService:
    """Service boundary for detecting and retrieving signals."""

    def detect_signals(self, entity_id: str, data: Dict[str, Any]) -> List[SignalEntity]:
        return detect_signals_from_company(entity_id, data)


signal_service = SignalService()
