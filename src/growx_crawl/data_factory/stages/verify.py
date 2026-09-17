"""
GrowX Data Factory Stage 6: Verification.
Applies stored-data-first verification: reuses valid, non-stale verifications
and triggers fresh network verification only when needed or budget allows.
"""

from typing import Any, Dict, List, Optional
from growx_crawl.data_factory.metrics import DataFactoryMetrics
from growx_crawl.data_factory.quotas import BudgetGuard
from growx_crawl.verification import verification_service
from growx_crawl.verification.models import VerificationStatus


class VerifyStage:
    """Verifies companies and domains with stored-first deduplication."""

    def __init__(self, service=None):
        self.verification_service = service or verification_service

    async def execute(
        self,
        fact_items: List[Dict[str, Any]],
        budget_guard: BudgetGuard,
        metrics: DataFactoryMetrics,
    ) -> List[Dict[str, Any]]:
        verified_items: List[Dict[str, Any]] = []

        for item in fact_items:
            cid = item.get("canonical_company_id", "")
            domain = item.get("domain", "")

            # 1. Stored-data-first: Check if already verified and fresh
            state = None
            if hasattr(self.verification_service, "get_current_state"):
                try:
                    state = self.verification_service.get_current_state("company", cid, "company")
                except Exception:
                    state = None
            elif hasattr(self.verification_service, "repository") and hasattr(self.verification_service.repository, "get_state"):
                try:
                    state = self.verification_service.repository.get_state("company", cid, "company")
                except Exception:
                    state = None

            if state:
                status_val = state.status.value if hasattr(state.status, "value") else str(state.status)
                if status_val in ("verified", "supported") and state.confidence >= 0.80:
                    metrics.verifications_reused += 1
                    item["verification_status"] = status_val
                    item["verification_confidence"] = state.confidence
                    verified_items.append(item)
                    continue

            # 2. Check budget before live verification
            if not budget_guard.can_spend_verification(0.005):
                item["verification_status"] = "unverified"
                item["verification_confidence"] = 0.50
                verified_items.append(item)
                continue

            # 3. Execute live verification
            try:
                import inspect
                sig = inspect.signature(self.verification_service.verify_company)
                if "company_data" in sig.parameters:
                    run = await self.verification_service.verify_company(
                        company_id=cid,
                        company_data={"domain": domain, "company_name": item.get("company_name", domain)},
                    )
                else:
                    run = await self.verification_service.verify_company(
                        company_id=cid,
                        domain=domain,
                        company_name=item.get("company_name", domain),
                    )
                budget_guard.record_verification_spend(0.005)
                metrics.verifications_executed += 1
                status_val = run.status.value if hasattr(run.status, "value") else str(run.status)
                item["verification_status"] = status_val
                item["verification_confidence"] = run.confidence
            except Exception:
                metrics.errors += 1
                item["verification_status"] = "unverified"
                item["verification_confidence"] = 0.40

            verified_items.append(item)

        return verified_items
