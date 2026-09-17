"""
GrowX AI Telemetry & Observability.
Tracks tokens, cost, latency, task breakdown, and Prometheus-style metrics.
"""

import logging
from typing import Any, Dict, List, Optional
from growx_crawl.ai.models import AIResponse, RunStatus

logger = logging.getLogger("growx_crawl.ai.telemetry")


class AITelemetry:
    """Central metrics and telemetry engine for GrowX AI Gateway."""

    def __init__(self):
        self._history: List[AIResponse] = []
        self._task_metrics: Dict[str, Dict[str, Any]] = {}
        self._provider_metrics: Dict[str, Dict[str, Any]] = {}

    def record_run(self, response: AIResponse) -> None:
        self._history.append(response)

        # 1. Update task-level metrics
        task = response.task or "unknown"
        if task not in self._task_metrics:
            self._task_metrics[task] = {
                "runs": 0,
                "tokens": 0,
                "cost_usd": 0.0,
                "success": 0,
                "failures": 0,
                "fallbacks": 0,
                "cache_hits": 0,
            }
        tm = self._task_metrics[task]
        tm["runs"] += 1
        tm["tokens"] += response.total_tokens
        tm["cost_usd"] = round(tm["cost_usd"] + response.cost_usd, 6)
        if response.status == RunStatus.SUCCESS.value:
            tm["success"] += 1
        elif response.status == RunStatus.FAILED.value:
            tm["failures"] += 1
        if response.fallback_used:
            tm["fallbacks"] += 1
        if response.cached:
            tm["cache_hits"] += 1

        # 2. Update provider-level metrics
        prov = response.provider or "unknown"
        if prov not in self._provider_metrics:
            self._provider_metrics[prov] = {
                "calls": 0,
                "errors": 0,
                "total_latency_ms": 0,
            }
        pm = self._provider_metrics[prov]
        pm["calls"] += 1
        pm["total_latency_ms"] += response.latency_ms
        if response.status == RunStatus.FAILED.value:
            pm["errors"] += 1

        logger.info(
            f"[AI_TELEMETRY] run_id={response.run_id} task={response.task} "
            f"provider={response.provider} model={response.model} "
            f"tokens={response.total_tokens} cost=${response.cost_usd:.6f} "
            f"latency={response.latency_ms}ms status={response.status} "
            f"cached={response.cached} fallback={response.fallback_used}"
        )

    def get_summary(self) -> Dict[str, Any]:
        total_tokens = sum(r.total_tokens for r in self._history)
        total_cost = sum(r.cost_usd for r in self._history)
        fallbacks = sum(1 for r in self._history if r.fallback_used)
        cached_runs = sum(1 for r in self._history if r.cached)
        return {
            "total_runs": len(self._history),
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 6),
            "fallback_runs": fallbacks,
            "cached_runs": cached_runs,
        }

    def get_task_summary(self, task: str) -> Dict[str, Any]:
        return self._task_metrics.get(task, {
            "runs": 0,
            "tokens": 0,
            "cost_usd": 0.0,
            "success": 0,
            "failures": 0,
            "fallbacks": 0,
            "cache_hits": 0,
        })

    def get_provider_health_summary(self) -> Dict[str, Any]:
        result = {}
        for prov, m in self._provider_metrics.items():
            calls = m["calls"]
            errs = m["errors"]
            err_rate = round(errs / calls, 3) if calls > 0 else 0.0
            avg_lat = round(m["total_latency_ms"] / calls, 1) if calls > 0 else 0.0
            result[prov] = {
                "total_calls": calls,
                "error_rate": err_rate,
                "avg_latency_ms": avg_lat,
            }
        return result


ai_telemetry = AITelemetry()
