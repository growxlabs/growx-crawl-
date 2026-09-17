"""
GrowX Identity Relationships.
Owns inter-company structural relationships and employment bindings.
"""

from typing import Any, Dict, Optional
from growx_crawl.identity.ids import generate_identity_id
from growx_crawl.identity.models import CompanyRelationshipEntity

RELATIONSHIP_TYPES = {
    "parent",
    "subsidiary",
    "brand_owner",
    "acquired",
    "partner",
    "competitor_candidate",
}


def create_company_relationship(
    from_company_id: str,
    to_company_id: str,
    relationship_type: str,
    confidence: float = 1.0,
    source_id: Optional[str] = None,
    metadata_json: Optional[Dict[str, Any]] = None,
) -> CompanyRelationshipEntity:
    """Creates a standardized CompanyRelationshipEntity."""
    rel_type = relationship_type.lower().strip()
    return CompanyRelationshipEntity(
        id=generate_identity_id("rel_"),
        from_company_id=from_company_id,
        to_company_id=to_company_id,
        relationship_type=rel_type,
        confidence=confidence,
        source_id=source_id,
        metadata_json=metadata_json or {},
    )
