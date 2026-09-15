import csv
from pathlib import Path
from typing import Any, Dict, List
from growx_crawl.storage import LeadRepository


class CSVExporter:
    def __init__(self, db_path: str = None):
        self.lead_repo = LeadRepository(db_path)

    def export_job(self, job_id: str, output_path: str) -> str:
        leads = self.lead_repo.get_job_lead_candidates(job_id)
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            "company_name", "industry", "city", "state", "country", "website",
            "phone", "email", "instagram", "linkedin", "primary_contact",
            "lead_score", "priority", "collected_at"
        ]

        with open(out_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for item in leads:
                emails = item.get("emails", [])
                phones = item.get("phones", [])
                socials = item.get("social_profiles", [])
                contacts = item.get("contacts", [])

                writer.writerow({
                    "company_name": item.get("name", ""),
                    "industry": item.get("industry", ""),
                    "city": item.get("city", ""),
                    "state": item.get("state", ""),
                    "country": item.get("country", ""),
                    "website": item.get("website", ""),
                    "phone": phones[0]["phone"] if phones else "",
                    "email": emails[0]["email"] if emails else "",
                    "instagram": next((s["url"] for s in socials if s["platform"] == "instagram"), ""),
                    "linkedin": next((s["url"] for s in socials if s["platform"] == "linkedin"), ""),
                    "primary_contact": contacts[0]["name"] if contacts else "",
                    "lead_score": item.get("score", 0),
                    "priority": item.get("priority", "Low"),
                    "collected_at": item.get("created_at", ""),
                })

        return str(out_file)
