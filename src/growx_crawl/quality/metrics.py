"""
GrowX Quality Metrics & Event Bus.
Tracks quality gate outcomes, pass rates, and failure reason distributions.
"""

import logging
from typing import Any, Dict, List
from growx_crawl.quality.models import GateType, QualityDecision, QualityStatus

logger = logging.getLogger("growx_crawl.quality.metrics")


class QualityEventBus:
    """Publishes internal quality state change events for telemetry and auditing."""

    def __init__(self):
        self._listeners: List[Any] = []

    def emit(self, event_name: str, subject_type: str, subject_id: str, gate: str, status: str, score: float) -> None:
        logger.info(
            f"[QUALITY_EVENT] event={event_name} subject={subject_type}:{subject_id} "
            f"gate={gate} status={status} score={score:.2f}"
        )


class QualityMetrics:
    """Prometheus-style metrics collector for Data Quality Gates."""

    def __init__(self):
        self.evaluations_total = 0
        self.pass_total = 0
        self.limited_total = 0
        self.reverify_total = 0
        self.blocked_total = 0
        self.quarantine_total = 0

        self.gate_metrics: Dict[str, Dict[str, int]] = {}
        self.reason_distribution: Dict[str, int] = {}

    def record_decision(self, gate: GateType, decision: QualityDecision) -> None:
        self.evaluations_total += 1
        g_name = gate.value

        if g_name not in self.gate_metrics:
            self.gate_metrics[g_name] = {"total": 0, "pass": 0, "limited": 0, "reverify": 0, "blocked": 0, "quarantine": 0}
        gm = self.gate_metrics[g_name]
        gm["total"] += 1

        st = decision.status
        if st == QualityStatus.PASS:
            self.pass_total += 1
            gm["pass"] += 1
        elif st == QualityStatus.LIMITED:
            self.limited_total += 1
            gm["limited"] += 1
        elif st == QualityStatus.REVERIFY:
            self.reverify_total += 1
            gm["reverify"] += 1
        elif st == QualityStatus.BLOCKED or st == QualityStatus.REJECTED:
            self.blocked_total += 1
            gm["blocked"] += 1
        elif st == QualityStatus.QUARANTINE:
            self.quarantine_total += 1
            gm["quarantine"] += 1

        for r in decision.reasons:
            self.reason_distribution[r] = self.reason_distribution.get(r, 0) + 1

    def get_summary(self) -> Dict[str, Any]:
        pass_rate = round(self.pass_total / self.evaluations_total, 3) if self.evaluations_total > 0 else 0.0
        return {
            "evaluations_total": self.evaluations_total,
            "pass_total": self.pass_total,
            "pass_rate": pass_rate,
            "limited_total": self.limited_total,
            "reverify_total": self.reverify_total,
            "blocked_total": self.blocked_total,
            "quarantine_total": self.quarantine_total,
            "gate_breakdown": self.gate_metrics,
            "top_reasons": dict(sorted(self.reason_distribution.items(), key=lambda i: i[1], reverse=True)[:10]),
        }


quality_events = QualityEventBus()
quality_metrics = QualityMetrics()
