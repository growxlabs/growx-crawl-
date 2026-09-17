from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class EvidenceEntity(BaseModel):
    id: str
    observation_id: str
    source_id: Optional[str] = None
    object_ref_id: Optional[str] = None
    evidence_type: str  # html_fragment, markdown_fragment, json_path, pdf_page, screenshot, search_result, structured_metadata, api_response, uploaded_row, manual
    source_url: Optional[str] = None
    selector: Optional[str] = None
    text_start: Optional[int] = None
    text_end: Optional[int] = None
    page_number: Optional[int] = None
    quoted_text: Optional[str] = None
    content_hash: Optional[str] = None
    captured_at: str = Field(default_factory=utc_now_iso)
    created_at: str = Field(default_factory=utc_now_iso)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
