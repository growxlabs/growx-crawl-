import hashlib
import logging
from typing import Any, Dict, List, Optional
from growx_crawl.identity.ids import generate_identity_id
from growx_crawl.intelligence.evidence.models import EvidenceEntity
from growx_crawl.intelligence.evidence.repository import BaseEvidenceRepository, SqliteEvidenceRepository

logger = logging.getLogger("growx_crawl.intelligence.evidence.service")


class EvidenceService:
    """
    Manages supporting evidence metadata for observations, binding them to
    Cloudflare R2 object storage artifacts and minimal relevant text snippets.
    """

    def __init__(self, repo: Optional[BaseEvidenceRepository] = None):
        self.repo = repo or SqliteEvidenceRepository()

    def attach_evidence(
        self,
        observation_id: str,
        evidence_type: str = "html_fragment",
        source_id: Optional[str] = None,
        object_ref_id: Optional[str] = None,
        source_url: Optional[str] = None,
        selector: Optional[str] = None,
        quoted_text: Optional[str] = None,
        text_start: Optional[int] = None,
        text_end: Optional[int] = None,
        page_number: Optional[int] = None,
        content_hash: Optional[str] = None,
        captured_at: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EvidenceEntity:
        """
        Attaches evidence to an observation.
        Ensures snippets stored in Postgres/SQLite remain minimal (Section 12),
        relying on R2 object_ref_id for complete bodies (Section 11).
        """
        snippet = quoted_text
        if snippet and len(snippet) > 500:
            snippet = snippet[:497] + "..."

        if not content_hash and snippet:
            content_hash = hashlib.sha256(snippet.encode("utf-8")).hexdigest()

        evidence_id = generate_identity_id("evi_")
        evi = EvidenceEntity(
            id=evidence_id,
            observation_id=observation_id,
            source_id=source_id,
            object_ref_id=object_ref_id,
            evidence_type=evidence_type,
            source_url=source_url,
            selector=selector,
            text_start=text_start,
            text_end=text_end,
            page_number=page_number,
            quoted_text=snippet,
            content_hash=content_hash,
            captured_at=captured_at or EvidenceEntity.model_fields["captured_at"].default_factory(),
            metadata_json=metadata or {},
        )
        saved = self.repo.create(evi)
        logger.debug("Evidence attached: %s to observation %s (type: %s)", evidence_id, observation_id, evidence_type)
        return saved

    def list_by_observation(self, observation_id: str) -> List[EvidenceEntity]:
        return self.repo.list_by_observation(observation_id)


evidence_service = EvidenceService()
