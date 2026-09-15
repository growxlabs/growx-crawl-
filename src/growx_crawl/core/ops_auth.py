import hashlib
import hmac
import os
import secrets
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import Header, HTTPException, Request, status

# Strict Ops Administrator Lockdown
AUTHORIZED_OPS_EMAIL = "sai@growxlabs.tech"

# Ops Secret Passkey (can be set via env or defaults for initial launch)
OPS_SECRET_KEY = os.getenv("GROWX_OPS_KEY", "gx_ops_master_2026")
SESSION_SECRET = os.getenv("GROWX_SESSION_SECRET", secrets.token_hex(32))
SESSION_EXPIRY_SECONDS = 86400  # 24 Hours


class OpsAuthManager:
    """
    High-Security Operations & Administrative Authentication Manager.
    Enforces that ONLY sai@growxlabs.tech can authenticate and receive admin privileges.
    """

    def __init__(self):
        # Active sessions: token -> session dict
        self._sessions: Dict[str, Dict[str, Any]] = {}
        # Ring buffer for live system logs: max 300 entries
        self._logs: List[Dict[str, Any]] = []
        # Security audit logs
        self._security_audit: List[Dict[str, Any]] = []
        self._record_log("SYSTEM", "OpsAuthManager initialized. Single-admin policy active for sai@growxlabs.tech.")

    def _record_log(self, level: str, message: str, meta: Optional[Dict[str, Any]] = None):
        entry = {
            "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S.%f")[:-3],
            "iso": datetime.now(timezone.utc).isoformat(),
            "level": level.upper(),
            "message": message,
            "meta": meta or {},
        }
        self._logs.append(entry)
        if len(self._logs) > 300:
            self._logs.pop(0)

    def record_audit(self, event: str, email: str, client_ip: str, success: bool, reason: Optional[str] = None):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "email": email,
            "client_ip": client_ip,
            "authorized": success,
            "reason": reason,
        }
        self._security_audit.append(entry)
        if len(self._security_audit) > 200:
            self._security_audit.pop(0)

        log_level = "SECURITY" if success else "CRITICAL"
        self._record_log(
            log_level,
            f"Auth attempt for '{email}' from {client_ip}: {'AUTHORIZED' if success else 'BLOCKED'} ({reason or 'OK'})",
        )

    def authenticate(self, email: str, passkey: str, client_ip: str = "127.0.0.1") -> Dict[str, Any]:
        """
        Authenticates an administrator.
        STRICT REQUIREMENT: Email must match 'sai@growxlabs.tech'.
        Any other email receives an immediate 403 Forbidden.
        """
        cleaned_email = email.strip().lower()

        # 1. Identity Check
        if cleaned_email != AUTHORIZED_OPS_EMAIL.lower():
            self.record_audit("LOGIN_REJECTED", cleaned_email, client_ip, False, "Unauthorized email identity")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access Denied: '{cleaned_email}' is not authorized. Ops portal is strictly reserved for {AUTHORIZED_OPS_EMAIL}.",
            )

        # 2. Passkey Check (Timing-safe comparison)
        if not hmac.compare_digest(passkey.strip(), OPS_SECRET_KEY):
            self.record_audit("LOGIN_REJECTED", cleaned_email, client_ip, False, "Invalid Ops security passkey")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Ops security passkey provided.",
            )

        # 3. Issue Cryptographically Secure Session
        session_id = secrets.token_hex(24)
        signature = hmac.new(SESSION_SECRET.encode(), session_id.encode(), hashlib.sha256).hexdigest()
        token = f"gx_ops_session_{session_id}_{signature[:16]}"
        now = time.time()

        session_data = {
            "token": token,
            "email": AUTHORIZED_OPS_EMAIL,
            "role": "super_admin",
            "created_at": now,
            "expires_at": now + SESSION_EXPIRY_SECONDS,
            "client_ip": client_ip,
        }
        self._sessions[token] = session_data

        self.record_audit("LOGIN_SUCCESS", AUTHORIZED_OPS_EMAIL, client_ip, True, "Session established")
        return {
            "status": "success",
            "token": token,
            "email": AUTHORIZED_OPS_EMAIL,
            "role": "super_admin",
            "expires_in": SESSION_EXPIRY_SECONDS,
            "message": f"Welcome, {AUTHORIZED_OPS_EMAIL}. Sovereign Ops Command Session active.",
        }

    def verify_session(self, token: str) -> Dict[str, Any]:
        """
        Validates the Ops session token and verifies identity.
        """
        if not token or not token.startswith("gx_ops_session_"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid Ops session token. Please authenticate.",
            )

        session = self._sessions.get(token)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Ops session expired or invalidated. Please log in again.",
            )

        # Check expiration
        if time.time() > session["expires_at"]:
            self._sessions.pop(token, None)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Ops session timed out. Please re-authenticate.",
            )

        # Double check email authorization
        if session.get("email") != AUTHORIZED_OPS_EMAIL:
            self._sessions.pop(token, None)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Security violation: Session email does not match authorized administrator.",
            )

        return session

    def terminate_session(self, token: str):
        if token in self._sessions:
            email = self._sessions[token].get("email", "unknown")
            self._sessions.pop(token, None)
            self._record_log("SECURITY", f"Ops session for {email} closed by user request.")

    def get_logs(self, limit: int = 100, level: Optional[str] = None) -> List[Dict[str, Any]]:
        logs = self._logs
        if level:
            level_upper = level.upper()
            logs = [l for l in logs if l["level"] == level_upper]
        return logs[-limit:]

    def get_audit_trail(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._security_audit[-limit:]


# Global singleton
ops_auth_manager = OpsAuthManager()


async def get_current_ops_admin(
    authorization: Optional[str] = Header(None),
    x_ops_token: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """
    FastAPI dependency ensuring request is executed strictly by authenticated sai@growxlabs.tech.
    """
    token: Optional[str] = None
    if x_ops_token:
        token = x_ops_token.strip()
    elif authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1].strip()
        else:
            token = authorization.strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ops authorization required. Please provide a valid session token.",
        )

    return ops_auth_manager.verify_session(token)
