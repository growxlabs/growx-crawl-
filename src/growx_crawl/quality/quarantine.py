"""
GrowX Quality Quarantine Manager.
Holds malformed, unevidenced, or conflicting raw observations for audit and repair instead of silent drops.
"""

from typing import Any, Dict, List, Optional
from growx_crawl.quality.models import QuarantineEntity
from growx_crawl.shared.ids import generate_id
from growx_crawl.shared.time import utc_iso_now


class QuarantineManager:
    """Manages creation and status updates of quarantined observation payloads."""

    def create_quarantine_record(
        self,
        subject_type: str,
        payload: Dict[str, Any],
        reasons: List[str],
        source_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> QuarantineEntity:
        return QuarantineEntity(
            id=generate_id("qrn_"),
            subject_type=subject_type,
            candidate_payload_json=payload,
            reason_codes=reasons,
            source_id=source_id,
            status="pending",
            created_at=utc_iso_now(),
            metadata_json=metadata or {},
        )


quarantine_manager = QuarantineManager()
