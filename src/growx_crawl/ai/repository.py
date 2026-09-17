"""
GrowX AI Repository.
Provides dual-mode persistence (SQLite / In-Memory) for model runs, cost records, and evaluations.
"""

import json
import sqlite3
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from growx_crawl.ai.models import AIResponse
from growx_crawl.shared.time import utc_iso_now


class AIRepository(ABC):
    """Abstract interface for AI model runs and evaluation persistence."""

    @abstractmethod
    def save_run(self, response: AIResponse) -> None:
        pass

    @abstractmethod
    def get_run(self, run_id: str) -> Optional[AIResponse]:
        pass

    @abstractmethod
    def list_runs(self, task: Optional[str] = None, limit: int = 50) -> List[AIResponse]:
        pass

    @abstractmethod
    def save_evaluation(self, eval_data: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def list_evaluations(self, task: Optional[str] = None) -> List[Dict[str, Any]]:
        pass


class InMemoryAIRepository(AIRepository):
    """Fast in-memory implementation for test isolation and ephemeral execution."""

    def __init__(self):
        self._runs: Dict[str, AIResponse] = {}
        self._evals: List[Dict[str, Any]] = []

    def save_run(self, response: AIResponse) -> None:
        self._runs[response.run_id] = response

    def get_run(self, run_id: str) -> Optional[AIResponse]:
        return self._runs.get(run_id)

    def list_runs(self, task: Optional[str] = None, limit: int = 50) -> List[AIResponse]:
        runs = list(self._runs.values())
        if task:
            runs = [r for r in runs if r.task == task]
        return runs[-limit:]

    def save_evaluation(self, eval_data: Dict[str, Any]) -> None:
        self._evals.append(eval_data)

    def list_evaluations(self, task: Optional[str] = None) -> List[Dict[str, Any]]:
        if task:
            return [e for e in self._evals if e.get("task") == task]
        return list(self._evals)


class SqliteAIRepository(AIRepository):
    """Durable SQLite implementation backing local production runs."""

    def __init__(self, db_path: str = "growx_canonical.db"):
        self.db_path = db_path

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def save_run(self, response: AIResponse) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO model_runs (
                    id, task, provider, model, prompt_id, prompt_version,
                    quality_tier, input_hash, output_hash, status,
                    input_tokens, output_tokens, total_tokens, estimated_cost,
                    latency_ms, fallback_used, fallback_reason, cache_hit,
                    error_code, started_at, completed_at, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    response.run_id,
                    response.task,
                    response.provider,
                    response.model,
                    response.prompt_id,
                    response.prompt_version,
                    response.quality_tier,
                    response.fingerprint,
                    "",
                    response.status,
                    response.prompt_tokens,
                    response.completion_tokens,
                    response.total_tokens,
                    response.cost_usd,
                    response.latency_ms,
                    1 if response.fallback_used else 0,
                    response.fallback_reason,
                    1 if response.cached else 0,
                    response.error_code,
                    response.created_at,
                    response.created_at,
                    json.dumps(response.metadata_json),
                ),
            )
            conn.commit()

    def get_run(self, run_id: str) -> Optional[AIResponse]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM model_runs WHERE id = ?", (run_id,)).fetchone()
            if not row:
                return None
            return self._row_to_response(row)

    def list_runs(self, task: Optional[str] = None, limit: int = 50) -> List[AIResponse]:
        with self._get_conn() as conn:
            if task:
                rows = conn.execute(
                    "SELECT * FROM model_runs WHERE task = ? ORDER BY started_at DESC LIMIT ?",
                    (task, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM model_runs ORDER BY started_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [self._row_to_response(r) for r in rows]

    def save_evaluation(self, eval_data: Dict[str, Any]) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO ai_evaluations (
                    id, task, dataset_version, candidate_config, score_json, cost, latency_ms, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    eval_data.get("id", f"eval_{utc_iso_now()}"),
                    eval_data.get("task", ""),
                    eval_data.get("dataset_version", "v1"),
                    json.dumps(eval_data.get("candidate_config", {})),
                    json.dumps(eval_data.get("score_json", {})),
                    eval_data.get("cost", 0.0),
                    eval_data.get("latency_ms", 0),
                    eval_data.get("created_at", utc_iso_now()),
                ),
            )
            conn.commit()

    def list_evaluations(self, task: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            if task:
                rows = conn.execute(
                    "SELECT * FROM ai_evaluations WHERE task = ? ORDER BY created_at DESC", (task,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM ai_evaluations ORDER BY created_at DESC").fetchall()
            results = []
            for r in rows:
                results.append({
                    "id": r["id"],
                    "task": r["task"],
                    "dataset_version": r["dataset_version"],
                    "candidate_config": json.loads(r["candidate_config"]),
                    "score_json": json.loads(r["score_json"]),
                    "cost": r["cost"],
                    "latency_ms": r["latency_ms"],
                    "created_at": r["created_at"],
                })
            return results

    def _row_to_response(self, row: sqlite3.Row) -> AIResponse:
        return AIResponse(
            run_id=row["id"],
            content="",
            model=row["model"],
            provider=row["provider"],
            task=row["task"],
            prompt_id=row["prompt_id"] or "",
            prompt_version=row["prompt_version"],
            quality_tier=row["quality_tier"],
            prompt_tokens=row["input_tokens"],
            completion_tokens=row["output_tokens"],
            total_tokens=row["total_tokens"],
            cost_usd=row["estimated_cost"],
            latency_ms=row["latency_ms"],
            status=row["status"],
            fallback_used=bool(row["fallback_used"]),
            fallback_reason=row["fallback_reason"],
            cached=bool(row["cache_hit"]),
            fingerprint=row["input_hash"] or "",
            error_code=row["error_code"],
            created_at=row["started_at"],
            metadata_json=json.loads(row["metadata_json"] or "{}"),
        )


ai_repository = InMemoryAIRepository()
