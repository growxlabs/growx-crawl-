"""
GrowX Identity Aliases.
Owns alias resolution and normalization for companies and individuals.
"""

from typing import List, Optional
from growx_crawl.identity.ids import generate_identity_id
from growx_crawl.identity.models import PersonAliasEntity
from growx_crawl.normalization.person import normalize_person_name


def create_person_alias(
    person_id: str,
    alias: str,
    alias_type: str = "name_variant",
    source_id: Optional[str] = None,
    confidence: float = 1.0,
) -> PersonAliasEntity:
    """Creates a standardized PersonAliasEntity with canonical ID and normalized form."""
    norm_alias = normalize_person_name(alias)
    return PersonAliasEntity(
        id=generate_identity_id("alt_"),
        person_id=person_id,
        alias=alias.strip(),
        normalized_alias=norm_alias,
        alias_type=alias_type,
        source_id=source_id,
        confidence=confidence,
    )
