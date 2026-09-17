"""
GrowX Platform Standard Cross-Domain Type Primitives.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class BaseRecord(BaseModel):
    """Base class for all domain transfer objects with standard serialization."""

    model_config = {"extra": "ignore", "populate_by_name": True}


class EntityReference(BaseModel):
    """Reference pointer to a canonical entity."""
    canonical_id: str
    entity_type: str  # company, person, domain, etc.
    label: Optional[str] = None


class MetadataPayload(BaseModel):
    """Arbitrary key-value metadata container."""
    data: Dict[str, Any] = Field(default_factory=dict)
