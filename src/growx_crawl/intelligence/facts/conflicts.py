import logging
from typing import Any, Dict, Optional
from growx_crawl.identity.ids import generate_identity_id
from growx_crawl.intelligence.facts.models import FactConflictEntity

logger = logging.getLogger("growx_crawl.intelligence.facts.conflicts")


def create_fact_conflict(
    subject_type: str,
    subject_id: str,
    predicate: str,
    status: str = "open",
    metadata: Optional[Dict[str, Any]] = None,
) -> FactConflictEntity:
    """
    Constructs a FactConflictEntity to preserve open data disagreements
    without silently dropping or overriding evidence.
    """
    conflict_id = generate_identity_id("cfl_")
    conflict = FactConflictEntity(
        id=conflict_id,
        subject_type=subject_type,
        subject_id=subject_id,
        predicate=predicate,
        status=status,
        metadata_json=metadata or {},
    )
    logger.info("Opened fact conflict: %s on %s:%s for predicate '%s'", conflict_id, subject_type, subject_id, predicate)
    return conflict
