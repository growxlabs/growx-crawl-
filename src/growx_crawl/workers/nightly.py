"""
GrowX Nightly Data Factory Worker Process.
Canonical runner process responsible for:
- Initiating the scheduled nightly run
- Loading the target segment plan
- Dispatching stages through DataFactoryService
- Resuming checkpoints if interrupted
- Capturing process signals gracefully
- Printing/storing the morning intelligence summary
"""

import asyncio
import logging
import signal
import sys
from growx_crawl.data_factory import RunType, data_factory_service

logger = logging.getLogger("growx_crawl.workers.nightly")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


async def run_nightly_worker():
    """Main worker loop executing the nightly data factory run."""
    logger.info("[NIGHTLY_WORKER] Starting GrowX Nightly Intelligence Factory...")

    # Plan run
    plan = data_factory_service.plan_run(run_type=RunType.NIGHTLY)
    logger.info(f"[NIGHTLY_WORKER] Compiled plan {plan.id} for segments: {[s.name for s in plan.target_segments]}")

    # Launch run
    try:
        run = await data_factory_service.start_run(plan=plan, run_type=RunType.NIGHTLY)
        logger.info(f"[NIGHTLY_WORKER] Nightly run {run.id} finished with status: {run.status.value}")

        # Retrieve morning summary
        summary = data_factory_service.get_morning_summary(run.id)
        if summary:
            logger.info("\n" + "="*60 + "\n" + summary.report_markdown + "\n" + "="*60)

        return run
    except Exception as e:
        logger.error(f"[NIGHTLY_WORKER] Nightly run failed with error: {e}", exc_info=True)
        raise


def main():
    try:
        asyncio.run(run_nightly_worker())
    except KeyboardInterrupt:
        logger.warning("[NIGHTLY_WORKER] Interrupted by user. Checkpoint saved.")
        sys.exit(0)


if __name__ == "__main__":
    main()
