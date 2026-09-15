from typing import Any, Dict
from growx_crawl.models.lead import Company


class AIEnricher:
    """
    Optional AI Enrichment Interface adapter.
    Disabled by default to ensure no AI hallucination on raw facts.
    """

    def __init__(self, enabled: bool = False):
        self.enabled = enabled

    async def enrich_company(self, company: Company) -> Dict[str, Any]:
        if not self.enabled:
            return {"status": "disabled", "inferred_data": {}}

        # Stub adapter for LLM inference...
        return {"status": "success", "inferred_data": {}}
