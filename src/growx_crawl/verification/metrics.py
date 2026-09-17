"""
GrowX Verification Metrics.
Tracks verification volume, outcomes, rates, precision, and latency telemetry.
"""

from typing import Any, Dict
from growx_crawl.verification.models import VerificationResultEntity, VerificationStatus


class VerificationMetricsTracker:
    def __init__(self):
        self.runs_total: int = 0
        self.verified_total: int = 0
        self.supported_total: int = 0
        self.uncertain_total: int = 0
        self.stale_total: int = 0
        self.invalid_total: int = 0
        self.conflicts_total: int = 0
        self.by_subject: Dict[str, Dict[str, int]] = {}

    def record_result(self, result: VerificationResultEntity) -> None:
        self.runs_total += 1
        st = result.status

        if st == VerificationStatus.VERIFIED:
            self.verified_total += 1
        elif st == VerificationStatus.SUPPORTED:
            self.supported_total += 1
        elif st == VerificationStatus.UNCERTAIN:
            self.uncertain_total += 1
        elif st == VerificationStatus.STALE:
            self.stale_total += 1
        elif st in (VerificationStatus.INVALID, VerificationStatus.FAILED):
            self.invalid_total += 1
        elif st == VerificationStatus.CONFLICTING:
            self.conflicts_total += 1

        subj = result.subject_type
        if subj not in self.by_subject:
            self.by_subject[subj] = {"total": 0, "verified": 0, "stale": 0, "invalid": 0}
        self.by_subject[subj]["total"] += 1
        if st == VerificationStatus.VERIFIED:
            self.by_subject[subj]["verified"] += 1
        elif st == VerificationStatus.STALE:
            self.by_subject[subj]["stale"] += 1
        elif st in (VerificationStatus.INVALID, VerificationStatus.FAILED):
            self.by_subject[subj]["invalid"] += 1

    def get_summary(self) -> Dict[str, Any]:
        verified_rate = (self.verified_total / self.runs_total) if self.runs_total else 0.0
        stale_rate = (self.stale_total / self.runs_total) if self.runs_total else 0.0
        invalid_rate = (self.invalid_total / self.runs_total) if self.runs_total else 0.0

        return {
            "runs_total": self.runs_total,
            "verified_total": self.verified_total,
            "supported_total": self.supported_total,
            "uncertain_total": self.uncertain_total,
            "stale_total": self.stale_total,
            "invalid_total": self.invalid_total,
            "conflicts_total": self.conflicts_total,
            "verified_rate": round(verified_rate, 3),
            "stale_rate": round(stale_rate, 3),
            "invalid_rate": round(invalid_rate, 3),
            "by_subject": self.by_subject,
        }


verification_metrics = VerificationMetricsTracker()
