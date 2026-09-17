"""
GrowX Data Factory Stage Pipeline Orchestrator.
Sequentially executes the 9 pipeline stages, checks quotas, records stage checkpoints,
captures failed jobs in dead-letter storage, and generates the final morning intelligence report.
"""

from typing import Any, Dict, List, Optional
from growx_crawl.data_factory.checkpoints import CheckpointManager
from growx_crawl.data_factory.metrics import DataFactoryMetrics
from growx_crawl.data_factory.models import (
    DataFactoryPlan,
    DataFactoryRun,
    FactoryStage,
    FailedJob,
    RunStatus,
)
from growx_crawl.data_factory.quotas import BudgetGuard
from growx_crawl.data_factory.repository import DataFactoryRepository, SqliteDataFactoryRepository
from growx_crawl.data_factory.stages import (
    CrawlStage,
    DiscoverStage,
    ExtractStage,
    FactsStage,
    HistoryStage,
    IndexStage,
    QualityStage,
    ResolveStage,
    VerifyStage,
)
from growx_crawl.events.broadcaster import CrawlEventBroadcaster
from growx_crawl.events.models import CrawlEvent
from growx_crawl.shared.ids import generate_id
from growx_crawl.shared.time import utc_iso_now


class DataFactoryPipeline:
    """Orchestrates end-to-end execution across all 9 data factory stages."""

    def __init__(
        self,
        repository: Optional[DataFactoryRepository] = None,
        checkpoint_manager: Optional[CheckpointManager] = None,
    ):
        self.repository = repository or SqliteDataFactoryRepository()
        self.checkpoint_manager = checkpoint_manager or CheckpointManager(self.repository)

        self.discover_stage = DiscoverStage()
        self.crawl_stage = CrawlStage()
        self.extract_stage = ExtractStage()
        self.resolve_stage = ResolveStage()
        self.facts_stage = FactsStage()
        self.verify_stage = VerifyStage()
        self.quality_stage = QualityStage()
        self.history_stage = HistoryStage()
        self.index_stage = IndexStage()

    def _emit_event(self, run_id: str, stage: str, data: Dict[str, Any]) -> None:
        """Publishes pipeline progress event to SSE broadcaster."""
        try:
            evt = CrawlEvent(
                job_id=run_id,
                stage=f"factory.{stage}",
                data=data,
            )
            CrawlEventBroadcaster.publish(evt)
        except Exception:
            pass

    async def run(
        self,
        run: DataFactoryRun,
        plan: DataFactoryPlan,
        seed_candidates: Optional[List[Dict[str, Any]]] = None,
        resume_stage: Optional[FactoryStage] = None,
    ) -> DataFactoryRun:
        budget_guard = BudgetGuard(plan)
        metrics = DataFactoryMetrics()

        run.status = RunStatus.RUNNING
        self.repository.save_run(run)
        self._emit_event(run.id, "started", {"plan_id": plan.id, "run_type": run.run_type.value})

        crawled_items: List[Dict[str, Any]] = []
        observations: List[Dict[str, Any]] = []
        resolved_items: List[Dict[str, Any]] = []
        fact_items: List[Dict[str, Any]] = []
        verified_items: List[Dict[str, Any]] = []
        quality_items: List[Dict[str, Any]] = []
        history_items: List[Dict[str, Any]] = []

        # Determine stages to run
        skip_discovery = resume_stage and resume_stage not in (FactoryStage.PLAN, FactoryStage.DISCOVERY)
        skip_crawl = resume_stage and resume_stage not in (FactoryStage.PLAN, FactoryStage.DISCOVERY, FactoryStage.CRAWL)

        # ── 1. DISCOVERY STAGE ──
        if not skip_discovery:
            self._emit_event(run.id, "stage.started", {"stage": "discovery"})
            candidates = self.discover_stage.execute(plan, metrics, seed_candidates=seed_candidates)
            run.checkpoint = FactoryStage.DISCOVERY
            self.checkpoint_manager.create_checkpoint(
                run_id=run.id,
                stage=FactoryStage.DISCOVERY,
                status="completed",
                processed_count=len(candidates),
            )
            self._emit_event(run.id, "stage.completed", {"stage": "discovery", "discovered": len(candidates)})
        else:
            candidates = seed_candidates or []

        # ── 2. CRAWL STAGE ──
        if not skip_crawl:
            self._emit_event(run.id, "stage.started", {"stage": "crawl"})
            crawled_items = await self.crawl_stage.execute(candidates, plan, budget_guard, metrics)
            run.checkpoint = FactoryStage.CRAWL
            self.checkpoint_manager.create_checkpoint(
                run_id=run.id,
                stage=FactoryStage.CRAWL,
                status="completed",
                processed_count=len(crawled_items),
            )
            self._emit_event(run.id, "stage.completed", {"stage": "crawl", "crawled": len(crawled_items)})
        else:
            crawled_items = [
                {"domain": c.get("domain"), "company_name": c.get("company_name"), "raw_html": c.get("raw_html", "")}
                for c in candidates
            ]

        # ── 3. EXTRACT STAGE ──
        self._emit_event(run.id, "stage.started", {"stage": "extract"})
        observations = self.extract_stage.execute(crawled_items, metrics)
        run.checkpoint = FactoryStage.EXTRACT
        self.checkpoint_manager.create_checkpoint(
            run_id=run.id,
            stage=FactoryStage.EXTRACT,
            status="completed",
            processed_count=len(observations),
        )

        # ── 4. RESOLVE STAGE ──
        self._emit_event(run.id, "stage.started", {"stage": "resolve"})
        resolved_items = self.resolve_stage.execute(observations, metrics)
        run.checkpoint = FactoryStage.RESOLVE
        self.checkpoint_manager.create_checkpoint(
            run_id=run.id,
            stage=FactoryStage.RESOLVE,
            status="completed",
            processed_count=len(resolved_items),
        )

        # ── 5. FACTS STAGE ──
        self._emit_event(run.id, "stage.started", {"stage": "facts"})
        fact_items = self.facts_stage.execute(resolved_items, metrics)
        run.checkpoint = FactoryStage.FACTS
        self.checkpoint_manager.create_checkpoint(
            run_id=run.id,
            stage=FactoryStage.FACTS,
            status="completed",
            processed_count=len(fact_items),
        )

        # ── 6. VERIFY STAGE ──
        self._emit_event(run.id, "stage.started", {"stage": "verify"})
        verified_items = await self.verify_stage.execute(fact_items, budget_guard, metrics)
        run.checkpoint = FactoryStage.VERIFY
        self.checkpoint_manager.create_checkpoint(
            run_id=run.id,
            stage=FactoryStage.VERIFY,
            status="completed",
            processed_count=len(verified_items),
        )

        # ── 7. QUALITY STAGE ──
        self._emit_event(run.id, "stage.started", {"stage": "quality"})
        quality_items = self.quality_stage.execute(verified_items, metrics)
        run.checkpoint = FactoryStage.QUALITY
        self.checkpoint_manager.create_checkpoint(
            run_id=run.id,
            stage=FactoryStage.QUALITY,
            status="completed",
            processed_count=len(quality_items),
        )

        # ── 8. HISTORY STAGE ──
        self._emit_event(run.id, "stage.started", {"stage": "history"})
        history_items = self.history_stage.execute(quality_items, metrics)
        run.checkpoint = FactoryStage.HISTORY
        self.checkpoint_manager.create_checkpoint(
            run_id=run.id,
            stage=FactoryStage.HISTORY,
            status="completed",
            processed_count=len(history_items),
        )

        # ── 9. INDEX STAGE ──
        self._emit_event(run.id, "stage.started", {"stage": "index"})
        indexed_items = self.index_stage.execute(history_items, metrics)
        run.checkpoint = FactoryStage.COMPLETE
        self.checkpoint_manager.create_checkpoint(
            run_id=run.id,
            stage=FactoryStage.INDEX,
            status="completed",
            processed_count=len(indexed_items),
        )

        # ── RUN FINALIZATION ──
        metrics.estimated_cost = budget_guard.total_cost
        run.completed_at = utc_iso_now()
        run.status = RunStatus.COMPLETED if metrics.errors == 0 else RunStatus.COMPLETED_WITH_ERRORS
        run.discovery_count = metrics.new_domains + metrics.known_domains
        run.crawl_count = metrics.pages_fetched_http + metrics.pages_fetched_browser
        run.entity_count = metrics.companies_created + metrics.companies_updated
        run.verification_count = metrics.verifications_executed + metrics.verifications_reused
        run.quality_pass_count = metrics.quality_passes
        run.error_count = metrics.errors
        run.estimated_cost = budget_guard.total_cost
        run.metadata_json = metrics.get_summary()

        self.repository.save_run(run)

        # Generate & save morning report
        summary = metrics.generate_morning_report(
            run_id=run.id,
            started_at=run.started_at,
            completed_at=run.completed_at,
        )
        self.repository.save_summary(summary)

        self._emit_event(run.id, "completed", {
            "status": run.status.value,
            "entities": run.entity_count,
            "cost": run.estimated_cost,
        })

        return run
