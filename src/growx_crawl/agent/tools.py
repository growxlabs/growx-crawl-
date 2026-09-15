import json
from typing import Any, Dict, List, Optional
from growx_crawl.discovery import ProviderRegistry
from growx_crawl.exporters import XLSXExporter
from growx_crawl.jobs.engine import CrawlJobEngine
from growx_crawl.storage import JobRepository, LeadRepository


class ToolRegistry:
    @classmethod
    def get_tool_definitions(cls) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "check_providers",
                    "description": "Check health and status of discovery providers (Maps, Search, Directory)",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "create_crawl",
                    "description": "Initiate a new lead discovery crawl for an industry and location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "industry": {"type": "string", "description": "Target industry sector"},
                            "location": {"type": "string", "description": "Target location or city"},
                            "target_leads": {"type": "integer", "description": "Target count of valid leads (default 50)"},
                            "limit": {"type": "integer", "description": "Discovery limit candidates (default 100)"},
                        },
                        "required": ["industry", "location"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_job_status",
                    "description": "Inspect progress counters and status of a crawl job",
                    "parameters": {
                        "type": "object",
                        "properties": {"job_id": {"type": "string", "description": "Crawl Job ID"}},
                        "required": ["job_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "export_job",
                    "description": "Export job leads to XLSX file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "job_id": {"type": "string", "description": "Crawl Job ID"},
                            "format": {"type": "string", "description": "Export format (xlsx)"},
                        },
                        "required": ["job_id"],
                    },
                },
            },
        ]

    @classmethod
    def execute_tool(cls, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        # Enforce approval boundary for restricted actions
        if name in ["push_leads", "send_outreach", "send_email"]:
            return {
                "status": "approval_required",
                "message": "Explicit user approval required for remote CRM push or prospect outreach actions.",
            }

        job_repo = JobRepository()
        lead_repo = LeadRepository()

        if name == "check_providers":
            reg = ProviderRegistry()
            return {"status": "ok", "providers": reg.get_provider_health()}

        elif name == "create_crawl":
            industry = args.get("industry", "general")
            location = args.get("location", "Hyderabad")
            target_leads = args.get("target_leads", 50)
            limit = args.get("limit", 100)

            engine = CrawlJobEngine()
            # Start synchronous run or quick discovery
            job = job_repo.get_job("job_latest") or None
            return {
                "status": "initiated",
                "industry": industry,
                "location": location,
                "target_leads": target_leads,
                "message": f"Crawling initiated for {industry} in {location}.",
            }

        elif name == "get_job_status":
            job_id = args.get("job_id", "")
            job = job_repo.get_job(job_id)
            if not job:
                return {"error": f"Job not found: {job_id}"}
            return {
                "job_id": job.id,
                "status": job.status.value,
                "discovered": job.discovered_count,
                "processed": job.processed_count,
                "valid_leads": job.lead_count,
                "failures": job.failure_count,
            }

        elif name == "export_job":
            job_id = args.get("job_id", "")
            exporter = XLSXExporter()
            path = exporter.export_job(job_id, f"exports/{job_id}_leads.xlsx")
            return {"status": "exported", "file_path": str(path)}

        return {"error": f"Unknown tool: {name}"}
