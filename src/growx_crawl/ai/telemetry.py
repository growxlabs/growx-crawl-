"""
GrowX AI Telemetry Logger.
Tracks tokens, cost, latency, and model runs.
"""

import logging
from typing import Any, Dict, List
from growx_crawl.ai.models import AIResponse

logger = logging.getLogger("growx_crawl.ai.telemetry")


class AITelemetry:
    def __init__(self):
        self._history: List[AIResponse] = []

    def record_run(self, response: AIResponse) -> None:
        self._history.append(response)
        logger.info(
            f"[AI_TELEMETRY] run_id={response.run_id} task={response.task} "
            f"provider={response.provider} model={response.model} "
            f"tokens={response.total_tokens} cost=${response.cost_usd:.6f} "
            f"latency={response.latency_ms}ms"
        )

    def get_summary(self) -> Dict[str, Any]:
        total_tokens = sum(r.total_tokens for r in self._history)
        total_cost = sum(r.cost_usd for r in self._history)
        return {
            "total_runs": len(self._history),
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 6),
        }


ai_telemetry = AITelemetry()
