import json
import tempfile
from pathlib import Path
from growx_crawl.integrations import GrowXLabsClient, GrowXLabsContactPayload, GrowXLabsLeadPayload, PayloadValidator
from growx_crawl.models import Company, LeadCandidate
from growx_crawl.storage import JobRepository, LeadRepository, init_db


def test_payload_validator():
    valid = GrowXLabsLeadPayload(
        external_reference="ref_1",
        company_name="Royal Jewellers",
        lead_score=85,
        priority="High",
        website="https://royal.com",
    )
    is_valid, errs = PayloadValidator.validate_lead(valid)
    assert is_valid is True
    assert len(errs) == 0

    invalid = GrowXLabsLeadPayload(
        external_reference="ref_2",
        company_name="",
        lead_score=150,
        priority="InvalidPriority",
    )
    is_valid, errs = PayloadValidator.validate_lead(invalid)
    assert is_valid is False
    assert len(errs) >= 2


def test_growxlabs_envelope_and_idempotency():
    client = GrowXLabsClient()
    lead1 = GrowXLabsLeadPayload(external_reference="cmp_1", company_name="Co A")
    lead2 = GrowXLabsLeadPayload(external_reference="cmp_2", company_name="Co B")

    env = client.build_envelope(job_id="job_123", batch_index=1, batch_count=1, leads=[lead1, lead2])
    assert env.schema_version == "1"
    assert env.source == "growx-crawl"
    assert env.idempotency_key.startswith("idemp_")
    assert len(env.leads) == 2


def test_unconfigured_client():
    client = GrowXLabsClient(base_url="", token="")
    assert client.is_configured() is False
    res = client.submit_batch(client.build_envelope("j1", 1, 1, []))
    assert res["success"] is False
    assert "not configured" in res["error"]


def test_approved_leads_only_filtering():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = f"{tmp_dir}/test_integration.db"
        init_db(db_path)

        job_repo = JobRepository(db_path)
        lead_repo = LeadRepository(db_path)

        from growx_crawl.models import CrawlJob
        job = CrawlJob(query="jewellery Hyderabad", industry="Jewellery", location="Hyderabad")
        job_repo.create_job(job)

        c1 = Company(job_id=job.id, name="Approved Jewellers", normalized_name="approved jewellers", domain="appr.com", website="https://appr.com", source_url="def", review_status="approved")
        c2 = Company(job_id=job.id, name="Pending Jewellers", normalized_name="pending jewellers", domain="pend.com", website="https://pend.com", source_url="def", review_status="pending")
        c3 = Company(job_id=job.id, name="Rejected Jewellers", normalized_name="rejected jewellers", domain="rej.com", website="https://rej.com", source_url="def", review_status="rejected")

        c1_id = lead_repo.save_company(c1)
        c2_id = lead_repo.save_company(c2)
        c3_id = lead_repo.save_company(c3)

        from growx_crawl.core.enums import PriorityLevel
        lead_repo.save_lead_candidate(LeadCandidate(company_id=c1_id, job_id=job.id, score=90, priority=PriorityLevel.HIGH))
        lead_repo.save_lead_candidate(LeadCandidate(company_id=c2_id, job_id=job.id, score=70, priority=PriorityLevel.MEDIUM))
        lead_repo.save_lead_candidate(LeadCandidate(company_id=c3_id, job_id=job.id, score=40, priority=PriorityLevel.LOW))

        eligible = lead_repo.get_push_eligible_leads(job.id)
        assert len(eligible) == 1
        assert eligible[0]["name"] == "Approved Jewellers"
