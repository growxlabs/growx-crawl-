import tempfile
from growx_crawl.core.enums import MatchDecision
from growx_crawl.dedupe import DeduplicationEngine
from growx_crawl.models import Company, CrawlJob, Email, Phone
from growx_crawl.storage import JobRepository, LeadRepository, init_db


def test_deduplication_same_domain():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = f"{tmp_dir}/test_dedupe.db"
        init_db(db_path)
        job_repo = JobRepository(db_path)
        repo = LeadRepository(db_path)
        engine = DeduplicationEngine(repo)

        job = CrawlJob(id="job1", query="test")
        job_repo.create_job(job)

        c1 = Company(
            job_id="job1",
            name="Royal Jewellers",
            normalized_name="royal jewellers",
            domain="royaljewellers.com",
            website="https://royaljewellers.com",
            source_url="https://royaljewellers.com",
            emails=[Email(company_id="", email="info@royaljewellers.com", normalized_email="info@royaljewellers.com", source_url="")],
        )
        repo.save_company(c1)

        c2 = Company(
            job_id="job1",
            name="Royal Jewellers Pvt Ltd",
            normalized_name="royal jewellers",
            domain="royaljewellers.com",
            website="https://royaljewellers.com/contact",
            source_url="https://royaljewellers.com/contact",
        )

        is_dup, rec, canonical_id = engine.evaluate(c2)
        assert is_dup is True
        assert rec is not None
        assert rec.canonical_company_id == c1.id
        assert rec.decision == MatchDecision.AUTO_MERGED
        assert "same_domain" in rec.match_signals
