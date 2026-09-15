from typing import Any, Dict, Optional
import httpx
from growx_crawl.core.config import settings
from growx_crawl.storage import JobRepository, LeadRepository


class GrowXLabsClient:
    """
    Integration Client for pushing normalized leads to GrowXLabs internal API endpoint.
    Destination endpoint: https://growxlabs.tech/api/internal/lead-ingestion
    """

    def __init__(
        self,
        api_base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        db_path: Optional[str] = None,
    ):
        self.api_base_url = api_base_url or settings.growxlabs_api_base_url
        self.api_key = api_key or settings.growxlabs_api_key
        self.lead_repo = LeadRepository(db_path)
        self.job_repo = JobRepository(db_path)

    async def push_job_leads(self, job_id: str) -> Dict[str, Any]:
        job = self.job_repo.get_job(job_id)
        if not job:
            return {"status": "error", "message": f"Job not found: {job_id}"}

        leads = self.lead_repo.get_job_lead_candidates(job_id)
        if not leads:
            return {"status": "skipped", "message": f"No leads found for job: {job_id}"}

        if not self.api_key:
            return {
                "status": "unconfigured",
                "message": (
                    "GrowXLabs API Key not configured. Set GROWXLABS_API_KEY in .env "
                    "or pass via config to push leads to https://growxlabs.tech/api/internal/lead-ingestion"
                ),
                "payload_summary": f"{len(leads)} leads prepared for push to {self.api_base_url}",
            }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "GrowXCrawl-PushClient/1.0",
        }

        payload = {
            "job_id": job_id,
            "query": job.query,
            "industry": job.industry,
            "location": job.location,
            "leads": leads,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(self.api_base_url, json=payload, headers=headers)
                if resp.status_code in [200, 201]:
                    return {"status": "success", "message": f"Successfully pushed {len(leads)} leads to GrowXLabs CRM"}
                else:
                    return {
                        "status": "failed",
                        "message": f"GrowXLabs endpoint returned HTTP {resp.status_code}: {resp.text[:200]}",
                    }
        except Exception as e:
            return {"status": "error", "message": f"Connection error pushing leads to GrowXLabs: {str(e)}"}
