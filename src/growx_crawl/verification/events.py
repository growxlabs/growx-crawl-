"""
GrowX Verification Events.
Emits asynchronous internal domain events during verification lifecycle.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from growx_crawl.shared.ids import generate_id
from growx_crawl.shared.time import utc_iso_now


class VerificationEvent(BaseModel):
    id: str
    event_type: str  # verification.started, verification.completed, verification.failed, email.verified, etc.
    subject_type: str
    subject_id: str
    status: str
    confidence: float
    timestamp: str = Field(default_factory=utc_iso_now)
    payload_json: Dict[str, Any] = Field(default_factory=dict)


class VerificationEventPublisher:
    """Publishes verification events to subscribers or event queues."""

    def __init__(self):
        self._history: List[VerificationEvent] = []

    def emit(
        self,
        event_type: str,
        subject_type: str,
        subject_id: str,
        status: str,
        confidence: float,
        payload: Optional[Dict[str, Any]] = None,
    ) -> VerificationEvent:
        event = VerificationEvent(
            id=generate_id("evt_"),
            event_type=event_type,
            subject_type=subject_type,
            subject_id=subject_id,
            status=status,
            confidence=confidence,
            payload_json=payload or {},
        )
        self._history.append(event)
        return event

    def list_events(self, subject_type: Optional[str] = None) -> List[VerificationEvent]:
        if subject_type:
            return [e for e in self._history if e.subject_type == subject_type]
        return list(self._history)


verification_events = VerificationEventPublisher()
