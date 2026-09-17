"""
GrowX AI Enrichment Adapter.
Routes company attribute enrichment through canonical AI Gateway when enabled.
"""

from typing import Any, Dict
from growx_crawl.ai.gateway import ai_gateway
from growx_crawl.ai.models import StructuredAIRequest
from growx_crawl.models.lead import Company


class AIEnricher:
    """
    Optional AI Enrichment Interface adapter.
    Calls GrowX AI Gateway for company enrichment inference.
    """

    def __init__(self, enabled: bool = False):
        self.enabled = enabled

    async def enrich_company(self, company: Company) -> Dict[str, Any]:
        if not self.enabled:
            return {"status": "disabled", "inferred_data": {}}

        req = StructuredAIRequest(
            task="company_enrichment",
            prompt=f"Extract enrichment attributes for company {company.name} with domain {company.domain}",
            metadata_json={"company_id": getattr(company, "id", "")},
        )
        try:
            res = await ai_gateway.generate_structured(req)
            return {"status": "success", "inferred_data": res.structured_output or {}}
        except Exception as e:
            return {"status": "failed", "error": str(e), "inferred_data": {}}
