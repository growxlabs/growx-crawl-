import json
from pathlib import Path
from typing import Any, Dict, List
from growx_crawl.storage import LeadRepository


class JSONExporter:
    def __init__(self, db_path: str = None):
        self.lead_repo = LeadRepository(db_path)

    def export_job(self, job_id: str, output_path: str, format_type: str = "json") -> str:
        leads = self.lead_repo.get_job_lead_candidates(job_id)
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)

        if format_type.lower() == "jsonl":
            with open(out_file, "w", encoding="utf-8") as f:
                for item in leads:
                    f.write(json.dumps(item) + "\n")
        else:
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(leads, f, indent=2)

        return str(out_file)
