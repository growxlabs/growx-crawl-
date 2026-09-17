"""
Internal Authentication, RBAC, and Audit Domain Models.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from growx_crawl.shared.ids import generate_id


class Role(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class UserStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"


class UserEntity(BaseModel):
    id: str = Field(default_factory=lambda: generate_id("usr"))
    email: str
    name: str
    role: Role = Role.VIEWER
    status: UserStatus = UserStatus.ACTIVE
    password_hash: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_login_at: Optional[str] = None


class AuditEventEntity(BaseModel):
    id: str = Field(default_factory=lambda: generate_id("aud"))
    actor_id: str
    action: str
    subject_type: str
    subject_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
