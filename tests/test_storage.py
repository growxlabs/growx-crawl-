import tempfile
from growx_crawl.core.enums import JobStatus, TargetStatus
from growx_crawl.models import CrawlJob, CrawlTarget
from growx_crawl.storage import JobRepository, TargetRepository, init_db


def test_storage_lifecycle():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = f"{tmp_dir}/test_storage.db"
        init_db(db_path)

        job_repo = JobRepository(db_path)
        target_repo = TargetRepository(db_path)

        job = CrawlJob(query="test query", industry="Jewellery", location="Hyderabad")
        job_repo.create_job(job)

        fetched_job = job_repo.get_job(job.id)
        assert fetched_job is not None
        assert fetched_job.query == "test query"

        targets = [
            CrawlTarget(job_id=job.id, url="https://example1.com", domain="example1.com"),
            CrawlTarget(job_id=job.id, url="https://example2.com", domain="example2.com"),
        ]
        added = target_repo.add_targets(targets)
        assert added == 2

        pending = target_repo.get_pending_targets(job.id)
        assert len(pending) == 2

        target_repo.update_target_status(pending[0].id, TargetStatus.COMPLETED)
        remaining = target_repo.get_pending_targets(job.id)
        assert len(remaining) == 1
