"""
GrowX Signal Service.
Owns buying signal detection, signal candidate management, and retrieval.
"""

import logging
from typing import Any, Dict, List, Optional

from growx_crawl.intelligence.history.models import TimelineEventEntity
from growx_crawl.intelligence.signals.detectors import (
    SignalCandidateDetector,
    detect_signals_from_company,
)
from growx_crawl.intelligence.signals.models import (
    SignalCandidateEntity,
    SignalEntity,
)
from growx_crawl.intelligence.signals.policies import get_signal_expiry_date
from growx_crawl.intelligence.signals.repository import (
    BaseSignalRepository,
    SqliteSignalRepository,
)
from growx_crawl.intelligence.signals.scoring import compute_signal_score
from growx_crawl.shared.time import utc_iso_now

logger = logging.getLogger("growx_crawl.intelligence.signals.service")


class SignalService:
    """Service boundary for detecting, storing, and retrieving signals."""

    def __init__(
        self,
        repository: Optional[BaseSignalRepository] = None,
        candidate_detector: Optional[SignalCandidateDetector] = None,
    ):
        self.repository = repository or SqliteSignalRepository()
        self.candidate_detector = candidate_detector or SignalCandidateDetector()

    def detect_signals(self, entity_id: str, data: Dict[str, Any]) -> List[SignalEntity]:
        """Legacy: detect signals from company data."""
        return detect_signals_from_company(entity_id, data)

    def detect_signal_candidates(
        self,
        entity_id: str,
        timeline_events: List[TimelineEventEntity],
        entity_type: str = "company",
    ) -> List[SignalCandidateEntity]:
        """Detect and persist signal candidates from timeline events."""
        candidates = self.candidate_detector.detect_from_timeline_events(
            entity_id=entity_id,
            events=timeline_events,
            entity_type=entity_type,
        )

        persisted: List[SignalCandidateEntity] = []
        for candidate in candidates:
            # Set expiry date based on signal type
            candidate.expires_at = get_signal_expiry_date(
                candidate.signal_type, candidate.detected_at
            )
            self.repository.create_candidate(candidate)
            persisted.append(candidate)

        return persisted

    def list_candidates(
        self,
        entity_id: str,
        status: Optional[str] = None,
        signal_type: Optional[str] = None,
    ) -> List[SignalCandidateEntity]:
        """List signal candidates for an entity."""
        return self.repository.list_candidates(entity_id, status, signal_type)

    def get_active_signals(self, entity_id: str) -> List[Dict[str, Any]]:
        """Get non-expired, supported+ signals with computed scores."""
        candidates = self.repository.list_candidates(entity_id)
        active = []
        for c in candidates:
            if c.status in ("expired", "rejected"):
                continue
            score = compute_signal_score(c)
            if score["freshness"] <= 0:
                continue
            active.append({
                "id": c.id,
                "signal_type": c.signal_type,
                "status": c.status,
                "occurred_at": c.occurred_at,
                "detected_at": c.detected_at,
                "expires_at": c.expires_at,
                **score,
            })
        return active

    def expire_stale_signals(self) -> int:
        """Expire signal candidates past their expiry date."""
        now = utc_iso_now()
        return self.repository.expire_candidates(now)


signal_service = SignalService()
