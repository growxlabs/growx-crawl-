"""
GrowX Data Factory Checkpoint Manager.
Tracks stage-level execution state, cursors, and progress to ensure interrupted
or paused runs can resume cleanly without repeating completed work.
"""

from typing import Any, Dict, List, Optional
from growx_crawl.data_factory.models import DataFactoryCheckpoint, FactoryStage
from growx_crawl.shared.time import utc_iso_now


STAGE_ORDER: List[FactoryStage] = [
    FactoryStage.DISCOVERY,
    FactoryStage.CRAWL,
    FactoryStage.EXTRACT,
    FactoryStage.RESOLVE,
    FactoryStage.FACTS,
    FactoryStage.VERIFY,
    FactoryStage.QUALITY,
    FactoryStage.HISTORY,
    FactoryStage.INDEX,
    FactoryStage.COMPLETE,
]


class CheckpointManager:
    """Manages stage checkpointing and resume point calculation."""

    def __init__(self, repository=None):
        self.repository = repository

    def create_checkpoint(
        self,
        run_id: str,
        stage: FactoryStage,
        cursor: Optional[str] = None,
        status: str = "completed",
        processed_count: int = 0,
        failed_count: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DataFactoryCheckpoint:
        cp = DataFactoryCheckpoint(
            run_id=run_id,
            stage=stage,
            cursor=cursor,
            status=status,
            processed_count=processed_count,
            failed_count=failed_count,
            updated_at=utc_iso_now(),
            metadata_json=metadata or {},
        )
        if self.repository:
            self.repository.save_checkpoint(cp)
        return cp

    def determine_resume_stage(
        self,
        checkpoints: List[DataFactoryCheckpoint],
    ) -> FactoryStage:
        """Calculates the earliest incomplete stage to resume execution."""
        completed_stages = {
            cp.stage for cp in checkpoints if cp.status == "completed"
        }

        for stage in STAGE_ORDER:
            if stage not in completed_stages and stage != FactoryStage.COMPLETE:
                return stage

        return FactoryStage.COMPLETE
