"""
GrowX Intelligence Signals Package.
"""

from growx_crawl.intelligence.signals.models import (
    SignalCandidateEntity,
    SignalCandidateStatus,
    SignalEntity,
    SignalType,
)
from growx_crawl.intelligence.signals.detectors import (
    SignalCandidateDetector,
    detect_signals_from_company,
)
from growx_crawl.intelligence.signals.repository import (
    BaseSignalRepository,
    SqliteSignalRepository,
)
from growx_crawl.intelligence.signals.scoring import (
    compute_signal_freshness,
    compute_signal_score,
)
from growx_crawl.intelligence.signals.service import SignalService, signal_service

__all__ = [
    "SignalEntity",
    "SignalCandidateEntity",
    "SignalType",
    "SignalCandidateStatus",
    "detect_signals_from_company",
    "SignalCandidateDetector",
    "BaseSignalRepository",
    "SqliteSignalRepository",
    "compute_signal_freshness",
    "compute_signal_score",
    "SignalService",
    "signal_service",
]
