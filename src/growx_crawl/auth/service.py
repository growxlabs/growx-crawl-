"""
Internal Authentication, Role Management, and Audit Trail Service.
"""

import base64
from datetime import datetime, timezone
import hashlib
import hmac
import json
import logging
import sqlite3
from typing import Any, Dict, List, Optional

from growx_crawl.auth.models import AuditEventEntity, Role, UserEntity, UserStatus
from growx_crawl.config.environments import get_active_config
from growx_crawl.shared.ids import generate_id
from growx_crawl.storage.db import get_db
from growx_crawl.storage.sqlite.canonical import init_sqlite_canonical_tables

logger = logging.getLogger("growx_crawl.auth.service")


class InternalAuthService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        with get_db(self.db_path) as conn:
            init_sqlite_canonical_tables(conn)
        self._ensure_default_users()

    def hash_password(self, password: str, salt: Optional[str] = None) -> str:
        s = salt or "growx_salt_secure_2026"
        h = hashlib.sha256(f"{s}:{password}".encode("utf-8")).hexdigest()
        return f"{s}${h}"

    def verify_password(self, password: str, hashed: str) -> bool:
        if "$" not in hashed:
            return False
        s, h = hashed.split("$", 1)
        expected = hashlib.sha256(f"{s}:{password}".encode("utf-8")).hexdigest()
        return hmac.compare_digest(expected, h)

    def create_token(self, user: UserEntity, expires_in_seconds: int = 86400) -> str:
        cfg = get_active_config()
        secret = cfg.auth.jwt_secret.encode("utf-8")
        now = int(datetime.now(timezone.utc).timestamp())
        payload = {
            "sub": user.id,
            "email": user.email,
            "role": user.role.value,
            "name": user.name,
            "iat": now,
            "exp": now + expires_in_seconds,
        }
        raw_payload = json.dumps(payload, sort_keys=True).encode("utf-8")
        sig = hmac.new(secret, raw_payload, hashlib.sha256).hexdigest()
        token_data = {
            "p": base64.urlsafe_b64encode(raw_payload).decode("utf-8"),
            "s": sig,
        }
        return base64.urlsafe_b64encode(json.dumps(token_data).encode("utf-8")).decode("utf-8")

    def decode_token(self, token_str: str) -> Optional[Dict[str, Any]]:
        try:
            cfg = get_active_config()
            secret = cfg.auth.jwt_secret.encode("utf-8")
            raw_token = base64.urlsafe_b64decode(token_str.encode("utf-8")).decode("utf-8")
            data = json.loads(raw_token)
            raw_payload = base64.urlsafe_b64decode(data["p"].encode("utf-8"))
            expected_sig = hmac.new(secret, raw_payload, hashlib.sha256).hexdigest()

            if not hmac.compare_digest(expected_sig, data["s"]):
                return None

            payload = json.loads(raw_payload.decode("utf-8"))
            now = int(datetime.now(timezone.utc).timestamp())
            if payload.get("exp", 0) < now:
                return None  # Expired

            return payload
        except Exception:
            return None

    def register_user(
        self,
        email: str,
        name: str,
        password: str,
        role: Role = Role.VIEWER,
    ) -> UserEntity:
        hashed = self.hash_password(password)
        user = UserEntity(
            email=email.strip().lower(),
            name=name.strip(),
            role=role,
            status=UserStatus.ACTIVE,
            password_hash=hashed,
        )
        with get_db(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO users (id, email, name, role, status, password_hash, created_at, last_login_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user.id,
                    user.email,
                    user.name,
                    user.role.value,
                    user.status.value,
                    user.password_hash,
                    user.created_at,
                    user.last_login_at,
                ),
            )
        logger.info(f"[AUTH] Registered user {user.email} with role {user.role.value}")
        return user

    def authenticate(self, email: str, password: str) -> Optional[UserEntity]:
        user = self.get_user_by_email(email)
        if not user or user.status != UserStatus.ACTIVE:
            return None
        if not self.verify_password(password, user.password_hash):
            return None

        now_str = datetime.now(timezone.utc).isoformat()
        with get_db(self.db_path) as conn:
            conn.execute("UPDATE users SET last_login_at = ? WHERE id = ?", (now_str, user.id))
        user.last_login_at = now_str
        return user

    def get_user_by_id(self, user_id: str) -> Optional[UserEntity]:
        with get_db(self.db_path) as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return self._row_to_user(row) if row else None

    def get_user_by_email(self, email: str) -> Optional[UserEntity]:
        with get_db(self.db_path) as conn:
            row = conn.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
            return self._row_to_user(row) if row else None

    def list_users(self) -> List[UserEntity]:
        with get_db(self.db_path) as conn:
            rows = conn.execute("SELECT * FROM users ORDER BY created_at ASC").fetchall()
            return [self._row_to_user(r) for r in rows]

    # Audit Events
    def log_audit(
        self,
        actor_id: str,
        action: str,
        subject_type: str,
        subject_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditEventEntity:
        event = AuditEventEntity(
            actor_id=actor_id,
            action=action,
            subject_type=subject_type,
            subject_id=subject_id,
            metadata_json=metadata or {},
        )
        with get_db(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO audit_events (id, actor_id, action, subject_type, subject_id, timestamp, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.id,
                    event.actor_id,
                    event.action,
                    event.subject_type,
                    event.subject_id,
                    event.timestamp,
                    json.dumps(event.metadata_json),
                ),
            )
        return event

    def list_audit_events(
        self,
        actor_id: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 50,
    ) -> List[AuditEventEntity]:
        with get_db(self.db_path) as conn:
            clauses = []
            params = []
            if actor_id:
                clauses.append("actor_id = ?")
                params.append(actor_id)
            if action:
                clauses.append("action = ?")
                params.append(action)

            where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
            params.append(limit)
            rows = conn.execute(
                f"SELECT * FROM audit_events {where} ORDER BY timestamp DESC LIMIT ?",
                tuple(params),
            ).fetchall()
            return [
                AuditEventEntity(
                    id=r["id"],
                    actor_id=r["actor_id"],
                    action=r["action"],
                    subject_type=r["subject_type"],
                    subject_id=r["subject_id"],
                    timestamp=r["timestamp"],
                    metadata_json=json.loads(r["metadata_json"] or "{}"),
                )
                for r in rows
            ]

    def _ensure_default_users(self):
        """Seeds default internal admin and operator users if users table is empty."""
        try:
            with get_db(self.db_path) as conn:
                count = conn.execute("SELECT COUNT(*) FROM users;").fetchone()[0]
                if count == 0:
                    self.register_user(
                        email="admin@growxlabs.tech",
                        name="GrowX Admin",
                        password="admin_internal_password",
                        role=Role.ADMIN,
                    )
                    self.register_user(
                        email="operator@growxlabs.tech",
                        name="GrowX Operator",
                        password="operator_internal_password",
                        role=Role.OPERATOR,
                    )
                    logger.info("[AUTH] Seeded default internal admin and operator accounts.")
        except Exception as e:
            logger.debug(f"[AUTH] Default user seeding skipped: {e}")

    def _row_to_user(self, r: sqlite3.Row) -> UserEntity:
        return UserEntity(
            id=r["id"],
            email=r["email"],
            name=r["name"],
            role=Role(r["role"]),
            status=UserStatus(r["status"]),
            password_hash=r["password_hash"],
            created_at=r["created_at"],
            last_login_at=r["last_login_at"],
        )


auth_service = InternalAuthService()

__all__ = ["InternalAuthService", "auth_service"]
