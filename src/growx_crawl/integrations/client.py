import hashlib
import os
from typing import Any, Dict, List, Optional
import httpx

from growx_crawl.integrations.dto import GrowXLabsIngestionEnvelope, GrowXLabsLeadPayload


class GrowXLabsClient:
    def __init__(self, base_url: Optional[str] = None, token: Optional[str] = None):
        self.base_url = (base_url or os.getenv("GROWXLABS_API_BASE_URL", "")).rstrip("/")
        self.token = token or os.getenv("GROWXLABS_INGESTION_TOKEN", "")

    def is_configured(self) -> bool:
        return bool(self.base_url and self.token)

    def generate_idempotency_key(self, job_id: str, batch_index: int, leads: List[GrowXLabsLeadPayload]) -> str:
        lead_ids = "".join(sorted([l.external_reference for l in leads]))
        raw_hash = f"{job_id}:{batch_index}:{lead_ids}".encode("utf-8")
        return f"idemp_{hashlib.sha256(raw_hash).hexdigest()[:16]}"

    def build_envelope(
        self, job_id: str, batch_index: int, batch_count: int, leads: List[GrowXLabsLeadPayload]
    ) -> GrowXLabsIngestionEnvelope:
        idemp_key = self.generate_idempotency_key(job_id, batch_index, leads)
        return GrowXLabsIngestionEnvelope(
            schema_version="1",
            source="growx-crawl",
            crawl_job_id=job_id,
            batch_index=batch_index,
            batch_count=batch_count,
            idempotency_key=idemp_key,
            leads=leads,
        )

    def submit_batch(self, envelope: GrowXLabsIngestionEnvelope) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "success": False,
                "error": "GrowXLabs integration is not configured. Set GROWXLABS_API_BASE_URL and GROWXLABS_INGESTION_TOKEN.",
            }

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "X-Idempotency-Key": envelope.idempotency_key,
        }

        url = f"{self.base_url}/api/v1/leads/ingest"

        try:
            with httpx.Client(timeout=30.0) as http:
                response = http.post(url, json=envelope.model_dump(), headers=headers)
                response.raise_for_status()
                return {"success": True, "status_code": response.status_code, "data": response.json()}
        except httpx.HTTPStatusError as e:
            return {"success": False, "status_code": e.response.status_code, "error": f"HTTP error: {e.response.text}"}
        except Exception as e:
            return {"success": False, "error": f"Connection error: {str(e)}"}
