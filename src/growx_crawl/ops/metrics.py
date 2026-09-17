"""
Production Metrics Collector for GrowX.
Tracks API latency, queue depth, throughput, and error rates.
"""

from collections import defaultdict
from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional


class MetricsCollector:
    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.latencies: List[float] = []
        self.jobs_completed = 0
        self.jobs_failed = 0
        self.started_at = datetime.now(timezone.utc).isoformat()

    def record_request(self, duration_ms: float, is_error: bool = False):
        self.request_count += 1
        if is_error:
            self.error_count += 1
        self.latencies.append(duration_ms)
        # Keep window of last 1,000 latencies
        if len(self.latencies) > 1000:
            self.latencies.pop(0)

    def record_job_completion(self, success: bool = True):
        if success:
            self.jobs_completed += 1
        else:
            self.jobs_failed += 1

    def get_summary(self) -> Dict[str, Any]:
        from growx_crawl.jobs.queue import job_queue_service

        sorted_lat = sorted(self.latencies) if self.latencies else [0.0]
        n = len(sorted_lat)
        p50 = sorted_lat[int(n * 0.50)] if n else 0.0
        p95 = sorted_lat[int(n * 0.95)] if n else 0.0
        p99 = sorted_lat[int(n * 0.99)] if n else 0.0

        queue_depth = job_queue_service.get_queue_depth()
        workers = job_queue_service.list_workers()
        active_workers = len([w for w in workers if w.status.value == "active"])

        return {
            "uptime_started_at": self.started_at,
            "api": {
                "total_requests": self.request_count,
                "error_requests": self.error_count,
                "error_rate": round(self.error_count / max(1, self.request_count), 4),
                "latency_p50_ms": round(p50, 2),
                "latency_p95_ms": round(p95, 2),
                "latency_p99_ms": round(p99, 2),
            },
            "queue": {
                "depth": queue_depth,
                "total_completed": self.jobs_completed,
                "total_failed": self.jobs_failed,
            },
            "workers": {
                "total_registered": len(workers),
                "active_workers": active_workers,
                "offline_workers": len(workers) - active_workers,
            },
        }


metrics_collector = MetricsCollector()

__all__ = ["MetricsCollector", "metrics_collector"]
