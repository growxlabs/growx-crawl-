"""
GrowX Intelligence Signals Models.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from growx_crawl.shared.time import utc_iso_now


class SignalEntity(BaseModel):
    id: str
    entity_id: str  # canonical company or person ID
    signal_type: str  # hiring_growth, tech_stack_change, funding_raised, new_product_launch
    title: str
    description: str
    confidence: float = 1.0
    detected_at: str = Field(default_factory=utc_iso_now)
    source_observation_id: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
