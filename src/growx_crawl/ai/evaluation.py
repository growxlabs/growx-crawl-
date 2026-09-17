"""
GrowX AI Evaluation Harness.
Provides repeatable benchmark evaluation of model/provider/prompt configurations across core tasks.
"""

import time
from typing import Any, Dict, List, Optional
from growx_crawl.ai.models import StructuredAIRequest
from growx_crawl.ai.repository import ai_repository
from growx_crawl.shared.ids import generate_id
from growx_crawl.shared.time import utc_iso_now


class AIEvaluationHarness:
    """Evaluates task accuracy, schema validity, cost, and latency against golden benchmarks."""

    def __init__(self, gateway=None):
        self._gateway = gateway

    @property
    def gateway(self):
        if self._gateway is None:
            from growx_crawl.ai.gateway import ai_gateway
            self._gateway = ai_gateway
        return self._gateway

    async def evaluate_task(
        self,
        task: str,
        benchmark_cases: List[Dict[str, Any]],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        prompt_version: str = "v1",
    ) -> Dict[str, Any]:
        """Runs evaluation over benchmark test cases and scores performance."""
        eval_id = generate_id("eval_")
        total_cases = len(benchmark_cases)
        schema_valid_count = 0
        total_latency_ms = 0
        total_cost_usd = 0.0
        case_results = []

        start_all = time.time()

        for case in benchmark_cases:
            schema_cls = case.get("schema_class")
            input_vars = case.get("input_vars", {})
            required_fields = case.get("required_fields", [])

            req = StructuredAIRequest(
                task=task,
                prompt=case.get("prompt", ""),
                input_data=input_vars,
                schema_class=schema_cls,
                prompt_version=prompt_version,
                provider=provider,
                model=model,
            )

            try:
                resp = await self.gateway.generate_structured(req)
                total_latency_ms += resp.latency_ms
                total_cost_usd += resp.cost_usd

                # Check schema validation & required fields
                data = resp.structured_output or {}
                has_all_fields = all(f in data for f in required_fields)
                is_valid = bool(data) and has_all_fields

                if is_valid:
                    schema_valid_count += 1

                case_results.append({
                    "case_id": case.get("id", "case"),
                    "status": resp.status,
                    "valid": is_valid,
                    "cost_usd": resp.cost_usd,
                    "latency_ms": resp.latency_ms,
                    "missing_fields": [f for f in required_fields if f not in data],
                })
            except Exception as e:
                case_results.append({
                    "case_id": case.get("id", "case"),
                    "status": "error",
                    "valid": False,
                    "error": str(e),
                })

        duration_sec = time.time() - start_all
        validity_rate = round(schema_valid_count / total_cases, 3) if total_cases > 0 else 0.0
        avg_latency = round(total_latency_ms / total_cases, 1) if total_cases > 0 else 0.0

        scores = {
            "validity_rate": validity_rate,
            "success_count": schema_valid_count,
            "total_cases": total_cases,
            "avg_latency_ms": avg_latency,
            "total_cost_usd": round(total_cost_usd, 6),
            "benchmark_duration_sec": round(duration_sec, 2),
        }

        eval_record = {
            "id": eval_id,
            "task": task,
            "dataset_version": prompt_version,
            "candidate_config": {"provider": provider or "default", "model": model or "default"},
            "score_json": scores,
            "cost": round(total_cost_usd, 6),
            "latency_ms": int(total_latency_ms),
            "created_at": utc_iso_now(),
        }

        ai_repository.save_evaluation(eval_record)
        return {
            "eval_id": eval_id,
            "task": task,
            "scores": scores,
            "case_results": case_results,
        }


ai_evaluation_harness = AIEvaluationHarness()
