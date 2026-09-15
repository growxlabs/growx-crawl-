from pathlib import Path
import tempfile
from growx_crawl.core.enums import PriorityLevel
from growx_crawl.exporters import CSVExporter, JSONExporter, XLSXExporter
from growx_crawl.models import Company, CrawlJob, Email, LeadCandidate
from growx_crawl.storage import JobRepository, LeadRepository, init_db


def test_exporters():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = f"{tmp_dir}/test_exporters.db"
        init_db(db_path)

        job_repo = JobRepository(db_path)
        lead_repo = LeadRepository(db_path)

        job = CrawlJob(query="jewellery stores Hyderabad", industry="Jewellery", location="Hyderabad")
        job_repo.create_job(job)

        company = Company(
            job_id=job.id,
            name="Royal Jewellers",
            normalized_name="royal jewellers",
            domain="royaljewellers.com",
            website="https://royaljewellers.com",
            industry="Jewellery",
            city="Hyderabad",
            source_url="https://royaljewellers.com",
            emails=[Email(company_id="", email="info@royaljewellers.com", normalized_email="info@royaljewellers.com", source_url="")],
        )
        c_id = lead_repo.save_company(company)

        lead_cand = LeadCandidate(
            company_id=c_id,
            job_id=job.id,
            score=85,
            priority=PriorityLevel.HIGH,
            score_reasons=["+ Website available", "+ Public email found"],
        )
        lead_repo.save_lead_candidate(lead_cand)

        with tempfile.TemporaryDirectory() as out_dir:
            xlsx_path = Path(out_dir) / "leads.xlsx"
            csv_path = Path(out_dir) / "leads.csv"
            json_path = Path(out_dir) / "leads.json"

            xlsx_exporter = XLSXExporter(db_path)
            res_xlsx = xlsx_exporter.export_job(job.id, str(xlsx_path))
            assert Path(res_xlsx).exists()

            csv_exporter = CSVExporter(db_path)
            res_csv = csv_exporter.export_job(job.id, str(csv_path))
            assert Path(res_csv).exists()

            json_exporter = JSONExporter(db_path)
            res_json = json_exporter.export_job(job.id, str(json_path))
            assert Path(res_json).exists()
