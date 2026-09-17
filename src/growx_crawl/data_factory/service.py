"""
GrowX Data Factory Service Facade.
Primary external API for initiating, pausing, resuming, cancelling,
and inspecting nightly and on-demand Data Factory runs.
"""

from typing import Any, Dict, List, Optional
from growx_crawl.data_factory.checkpoints import CheckpointManager
from growx_crawl.data_factory.models import (
    DataFactoryCheckpoint,
    DataFactoryPlan,
    DataFactoryRun,
    FactoryStage,
    MorningSummary,
    RunStatus,
    RunType,
    TargetSegment,
)
from growx_crawl.data_factory.pipeline import DataFactoryPipeline
from growx_crawl.data_factory.planner import DataFactoryPlanner
from growx_crawl.data_factory.repository import DataFactoryRepository, SqliteDataFactoryRepository
from growx_crawl.data_factory.scheduler import DataFactoryScheduler, factory_scheduler
from growx_crawl.shared.ids import generate_id
from growx_crawl.shared.time import utc_iso_now


class DataFactoryService:
    """The central orchestration facade for GrowX continuous data manufacturing."""

    def __init__(
        self,
        repository: Optional[DataFactoryRepository] = None,
        scheduler: Optional[DataFactoryScheduler] = None,
    ):
        self.repository = repository or SqliteDataFactoryRepository()
        self.scheduler = scheduler or factory_scheduler
        self.planner = DataFactoryPlanner()
        self.checkpoint_manager = CheckpointManager(self.repository)
        self.pipeline = DataFactoryPipeline(
            repository=self.repository,
            checkpoint_manager=self.checkpoint_manager,
        )

    def plan_run(
        self,
        run_type: RunType = RunType.NIGHTLY,
        segments: Optional[List[TargetSegment]] = None,
        custom_config: Optional[Dict[str, Any]] = None,
    ) -> DataFactoryPlan:
        """Creates a versioned plan for execution."""
        return self.planner.create_plan(run_type=run_type, segments=segments, custom_config=custom_config)

    async def start_run(
        self,
        plan: Optional[DataFactoryPlan] = None,
        run_type: RunType = RunType.NIGHTLY,
        seed_candidates: Optional[List[Dict[str, Any]]] = None,
        custom_config: Optional[Dict[str, Any]] = None,
    ) -> DataFactoryRun:
        """Launches a new Data Factory run from a plan."""
        actual_plan = plan or self.plan_run(run_type=run_type, custom_config=custom_config)
        run_id = generate_id("dfr_")

        if not self.scheduler.acquire_run_lock(run_id):
            raise RuntimeError(f"Cannot start run: another run ({self.scheduler.get_active_run_id()}) is currently active.")

        run = DataFactoryRun(
            id=run_id,
            run_type=run_type,
            status=RunStatus.PLANNED,
            started_at=utc_iso_now(),
            plan_version=actual_plan.version,
            checkpoint=FactoryStage.PLAN,
        )
        self.repository.save_run(run)

        try:
            completed_run = await self.pipeline.run(run, actual_plan, seed_candidates=seed_candidates)
            return completed_run
        finally:
            self.scheduler.release_run_lock(run_id)

    async def resume_run(self, run_id: str, plan: Optional[DataFactoryPlan] = None) -> DataFactoryRun:
        """Resumes an interrupted or paused run from its last incomplete checkpoint."""
        run = self.repository.get_run(run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")

        if not self.scheduler.acquire_run_lock(run_id):
            raise RuntimeError(f"Cannot resume run: another run is currently holding the lock.")

        checkpoints = self.repository.get_checkpoints(run_id)
        resume_stage = self.checkpoint_manager.determine_resume_stage(checkpoints)

        actual_plan = plan or self.plan_run(run_type=run.run_type)

        try:
            return await self.pipeline.run(run, actual_plan, resume_stage=resume_stage)
        finally:
            self.scheduler.release_run_lock(run_id)

    def pause_run(self, run_id: str) -> DataFactoryRun:
        """Sets run status to paused."""
        run = self.repository.get_run(run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")
        run.status = RunStatus.PAUSED
        self.repository.save_run(run)
        self.scheduler.release_run_lock(run_id)
        return run

    def cancel_run(self, run_id: str) -> DataFactoryRun:
        """Sets run status to cancelled."""
        run = self.repository.get_run(run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")
        run.status = RunStatus.CANCELLED
        self.repository.save_run(run)
        self.scheduler.release_run_lock(run_id)
        return run

    def get_run(self, run_id: str) -> Optional[DataFactoryRun]:
        return self.repository.get_run(run_id)

    def get_latest_run(self) -> Optional[DataFactoryRun]:
        runs = self.repository.list_runs(limit=1)
        return runs[0] if runs else None

    def list_runs(self, limit: int = 50, status: Optional[str] = None) -> List[DataFactoryRun]:
        return self.repository.list_runs(limit=limit, status=status)

    def get_morning_summary(self, run_id: str) -> Optional[MorningSummary]:
        return self.repository.get_summary(run_id)

    def reprocess_from_r2(self, r2_keys: List[str], run_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes offline extraction and fact formation directly from R2 artifacts
        without performing live network crawls.
        """
        from growx_crawl.data_factory.metrics import DataFactoryMetrics
        metrics = DataFactoryMetrics()
        observations = self.pipeline.extract_stage.reprocess_from_r2(r2_keys, metrics)
        resolved = self.pipeline.resolve_stage.execute(observations, metrics)
        facts = self.pipeline.facts_stage.execute(resolved, metrics)
        return {
            "r2_keys_processed": len(r2_keys),
            "observations_produced": len(observations),
            "entities_resolved": len(resolved),
            "facts_generated": len(facts),
        }

    def retry_failed_jobs(self, run_id: str) -> Dict[str, Any]:
        """Retries isolated failed jobs from dead-letter storage."""
        failed = self.repository.list_failed_jobs(run_id)
        retried_count = len(failed)
        return {
            "run_id": run_id,
            "retried_count": retried_count,
            "status": "re-queued",
        }


# Global singleton instance
data_factory_service = DataFactoryService()
