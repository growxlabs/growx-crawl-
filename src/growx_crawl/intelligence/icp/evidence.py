"""
GrowX ICP Evidence Linker.
Attaches evidence references from seller facts and competitor intelligence to ICP criteria.
"""

from typing import Optional
from growx_crawl.intelligence.icp.models import ICPEvidenceEntity
from growx_crawl.shared.ids import generate_id
from growx_crawl.shared.time import utc_iso_now


class ICPEvidenceLinker:
    """Creates verifiable bindings between ICP criteria and underlying intelligence sources."""

    @staticmethod
    def create_criterion_evidence(
        icp_version_id: str,
        criterion_id: str,
        source_type: str = "seller_fact",
        fact_id: Optional[str] = None,
        source_id: Optional[str] = None,
        confidence: float = 1.0,
    ) -> ICPEvidenceEntity:
        return ICPEvidenceEntity(
            id=generate_id("iev_"),
            icp_version_id=icp_version_id,
            criterion_id=criterion_id,
            source_type=source_type,
            source_id=source_id,
            fact_id=fact_id,
            confidence=confidence,
            created_at=utc_iso_now(),
        )

    @classmethod
    def link_seller_fact(
        cls,
        icp_version_id: str,
        criterion_id: str,
        fact_id: str,
        confidence: float = 1.0,
    ) -> ICPEvidenceEntity:
        """Helper to create evidence linked directly to a seller fact."""
        return cls.create_criterion_evidence(
            icp_version_id=icp_version_id,
            criterion_id=criterion_id,
            source_type="seller_fact",
            fact_id=fact_id,
            confidence=confidence,
        )

