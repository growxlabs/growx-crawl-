import asyncio
from pathlib import Path
import tempfile
from growx_crawl.jobs import CrawlJobEngine

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_job_engine_with_seed_file():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = f"{tmp_dir}/test_engine.db"
        engine = CrawlJobEngine(db_path)
        seed_file = str(FIXTURE_DIR / "sample_seed.csv")

        job = asyncio.run(
            engine.start_job(
                query="jewellery stores Hyderabad",
                seed_file=seed_file,
                limit=5,
                workers=2,
            )
        )

        assert job.id is not None
        assert job.discovered_count >= 3
        assert job.status.value in ["completed", "paused"]
