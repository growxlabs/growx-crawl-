import logging
from typing import Any, Dict, Optional
from growx_crawl.identity.ids import generate_identity_id
from growx_crawl.identity.models import IdentityEventEntity

logger = logging.getLogger("growx_crawl.identity.events")


def create_identity_event(
    entity_type: str,
    entity_id: str,
    event_type: str,
    payload: Optional[Dict[str, Any]] = None,
    source_id: Optional[str] = None,
    actor_type: str = "system",
    actor_id: Optional[str] = None,
) -> IdentityEventEntity:
    """
    Constructs an immutable identity audit event entity.
    """
    event_id = generate_identity_id("evt_")
    event = IdentityEventEntity(
        id=event_id,
        entity_type=entity_type,
        entity_id=entity_id,
        event_type=event_type,
        payload_json=payload or {},
        source_id=source_id,
        actor_type=actor_type,
        actor_id=actor_id,
    )
    logger.debug("Identity event created: %s (%s on %s:%s)", event_id, event_type, entity_type, entity_id)
    return event
