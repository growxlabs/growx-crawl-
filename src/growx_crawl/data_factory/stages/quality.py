"""
GrowX Data Factory Stage 7: Quality Gates.
Applies DataQualityService gates (Canonical Ingestion and Prospect Eligibility)
ensuring that low-quality, conflicting, or unverified records do not enter search indexing.
"""

from typing import Any, Dict, List, Optional
from growx_crawl.data_factory.metrics import DataFactoryMetrics
from growx_crawl.quality import GateType, QualityStatus, quality_service


class QualityStage:
    """Evaluates multi-tier quality gates over factory candidates."""

    def __init__(self, service=None):
        self.quality_service = service or quality_service

    def execute(
        self,
        verified_items: List[Dict[str, Any]],
        metrics: DataFactoryMetrics,
    ) -> List[Dict[str, Any]]:
        quality_evaluated_items: List[Dict[str, Any]] = []

        for item in verified_items:
            cid = item["canonical_company_id"]
            domain = item["domain"]
            obs = item.get("observation", {})

            # 1. Gate 1: Canonical Ingestion check
            ingest_data = {
                "subject_type": "company",
                "subject_id": cid,
                "name": item["company_name"],
                "domain": domain,
                "source_url": obs.get("source_url"),
                "source": obs.get("source"),
            }
            try:
                ingest_dec = self.quality_service.evaluate(
                    subject_type="company",
                    subject_id=cid,
                    gate_type=GateType.CANONICAL_INGESTION,
                    data=ingest_data,
                )
                if ingest_dec.status == QualityStatus.QUARANTINE:
                    metrics.quarantined += 1
                    item["quality_status"] = QualityStatus.QUARANTINE.value
                    item["quality_trusted"] = False
                    quality_evaluated_items.append(item)
                    continue
            except Exception:
                pass

            # 2. Gate 3: Prospect Eligibility check
            prospect_data = {
                "id": cid,
                "name": item["company_name"],
                "domain": domain,
                "description": obs.get("description", ""),
                "verification_status": item.get("verification_status", "unverified"),
                "verification_confidence": item.get("verification_confidence", 0.5),
            }
            try:
                dec = self.quality_service.evaluate(
                    subject_type="prospect",
                    subject_id=cid,
                    gate_type=GateType.PROSPECT_ELIGIBILITY,
                    data=prospect_data,
                )

                item["quality_decision"] = dec
                item["quality_status"] = dec.status.value
                item["quality_score"] = dec.score
                item["quality_trusted"] = (dec.status == QualityStatus.PASS)

                if dec.status == QualityStatus.PASS:
                    metrics.quality_passes += 1
                elif dec.status in (QualityStatus.BLOCKED, QualityStatus.REJECTED):
                    metrics.quality_blocks += 1
            except Exception as e:
                metrics.errors += 1
                item["quality_status"] = QualityStatus.LIMITED.value
                item["quality_trusted"] = False

            quality_evaluated_items.append(item)

        return quality_evaluated_items
