import logging
from typing import Any, Callable, Dict, Optional, Set
from growx_crawl.identity.ids import generate_identity_id
from growx_crawl.identity.models import EntityMergeEntity

logger = logging.getLogger("growx_crawl.identity.merge")


def create_entity_merge(
    entity_type: str,
    source_entity_id: str,
    target_entity_id: str,
    reason: str,
    method: str = "manual",
    confidence: float = 1.0,
    created_by: str = "system",
    metadata: Optional[Dict[str, Any]] = None,
) -> EntityMergeEntity:
    """
    Constructs an EntityMergeEntity record linking source_entity_id to target_entity_id.
    """
    merge_id = generate_identity_id("mrg_")
    return EntityMergeEntity(
        id=merge_id,
        entity_type=entity_type,
        source_entity_id=source_entity_id,
        target_entity_id=target_entity_id,
        reason=reason,
        method=method,
        confidence=confidence,
        created_by=created_by,
        metadata_json=metadata or {},
    )


def resolve_canonical_id_chain(
    initial_id: str,
    get_target_fn: Callable[[str], Optional[str]],
    max_hops: int = 10,
) -> str:
    """
    Recursively follows entity merge redirects until reaching the surviving canonical ID.
    Includes cycle detection and hop limit guardrails.
    
    Args:
        initial_id: The entity ID to resolve.
        get_target_fn: Callable returning target_entity_id if the input ID was merged, or None.
        max_hops: Maximum redirect hops before stopping.
    """
    if not initial_id:
        return ""

    current_id = initial_id
    visited: Set[str] = {current_id}

    for _ in range(max_hops):
        next_target = get_target_fn(current_id)
        if not next_target or next_target == current_id:
            break
        if next_target in visited:
            logger.warning("Merge cycle detected for entity %s -> %s. Stopping resolution.", current_id, next_target)
            break
        visited.add(next_target)
        current_id = next_target

    return current_id
