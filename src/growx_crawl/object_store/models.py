from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ObjectType(str, Enum):
    RAW_HTML = "raw_html"
    RENDERED_HTML = "rendered_html"
    MARKDOWN = "markdown"
    JSON_SNAPSHOT = "json_snapshot"
    SCREENSHOT = "screenshot"
    PDF = "pdf"
    IMPORT_CSV = "import_csv"
    IMPORT_XLSX = "import_xlsx"
    EXPORT_CSV = "export_csv"
    EXPORT_XLSX = "export_xlsx"
    EXPORT_JSON = "export_json"
    PARQUET = "parquet"
    MODEL_ARTIFACT = "model_artifact"
    OTHER = "other"


class BucketName:
    RAW = "growx-raw"
    PRIVATE = "growx-private"
    EXPORTS = "growx-exports"
    ALL_BUCKETS = [RAW, PRIVATE, EXPORTS]


class ObjectStat(BaseModel):
    bucket: str
    key: str
    size_bytes: int
    content_type: str = "application/octet-stream"
    content_encoding: Optional[str] = None
    content_hash: str  # SHA-256
    last_modified: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ObjectRefEntity(BaseModel):
    id: str
    object_type: str
    bucket: str
    object_key: str
    provider: str  # "local" or "r2"
    content_type: str
    content_encoding: Optional[str] = None
    content_hash: str
    size_bytes: int
    source_url: Optional[str] = None
    company_id: Optional[str] = None
    domain_id: Optional[str] = None
    crawl_run_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
