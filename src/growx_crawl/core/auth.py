import hashlib
import secrets
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import Header, HTTPException, status

from growx_crawl.storage.db import get_db

# Default tier limits
TIER_LIMITS = {
    "starter": {"rpm": 60, "monthly_quota": 10000},
    "growth": {"rpm": 300, "monthly_quota": 100000},
    "enterprise": {"rpm": 1200, "monthly_quota": 1000000},
}


class APIKeyManager:
    """
    Database-backed API Key Management & Token Bucket Rate Limiter with Admin Approval Flow.
    """

    def __init__(self):
        # Per-key sliding rate-limit tracking: key_id -> list of request timestamps
        self._rate_limits: Dict[str, List[float]] = {}
        self._bootstrap_default_key()

    @staticmethod
    def hash_key(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def _bootstrap_default_key(self):
        """Ensure a default active enterprise master key exists for sandbox & dev."""
        sandbox_token = "gx_live_sandbox_master_key"
        key_hash = self.hash_key(sandbox_token)
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            with get_db() as conn:
                existing = conn.execute("SELECT id FROM api_keys WHERE key_hash = ?", (key_hash,)).fetchone()
                if not existing:
                    conn.execute(
                        """
                        INSERT INTO api_keys (
                            id, key_hash, prefix, name, email, status, tier,
                            rate_limit_rpm, monthly_quota, requests_used,
                            created_at, approved_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                        """,
                        (
                            "key_sandbox_default",
                            key_hash,
                            "gx_live_sandbox...",
                            "GrowX Sandbox Master",
                            "admin@growxlabs.com",
                            "active",
                            "enterprise",
                            1200,
                            1000000,
                            now_iso,
                            now_iso,
                        ),
                    )
        except Exception:
            pass

    def request_key(self, name: str, email: str, tier: str = "starter") -> Dict[str, Any]:
        """User registers for an API key; placed into 'pending' status awaiting approval."""
        tier = tier.lower() if tier.lower() in TIER_LIMITS else "starter"
        limits = TIER_LIMITS[tier]
        key_id = f"key_{secrets.token_hex(8)}"
        temp_placeholder_hash = self.hash_key(f"pending_{key_id}")
        now_iso = datetime.now(timezone.utc).isoformat()

        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO api_keys (
                    id, key_hash, prefix, name, email, status, tier,
                    rate_limit_rpm, monthly_quota, requests_used, created_at
                ) VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?, 0, ?)
                """,
                (
                    key_id,
                    temp_placeholder_hash,
                    "gx_pending...",
                    name,
                    email,
                    tier,
                    limits["rpm"],
                    limits["monthly_quota"],
                    now_iso,
                ),
            )

        return {
            "id": key_id,
            "status": "pending",
            "name": name,
            "tier": tier,
            "rate_limit_rpm": limits["rpm"],
            "monthly_quota": limits["monthly_quota"],
            "message": "API key request submitted. Awaiting administrator approval.",
        }

    def list_keys(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """List API keys with optional status filter ('pending', 'active', 'revoked')."""
        query = "SELECT id, prefix, name, email, status, tier, rate_limit_rpm, monthly_quota, requests_used, created_at, approved_at, last_used_at FROM api_keys"
        params = []
        if status_filter:
            query += " WHERE status = ?"
            params.append(status_filter)
        query += " ORDER BY created_at DESC"

        with get_db() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def approve_key(self, key_id: str) -> Dict[str, Any]:
        """Admin approves a pending API key, generates secret token, and returns token once."""
        raw_secret = f"gx_live_{secrets.token_hex(24)}"
        key_hash = self.hash_key(raw_secret)
        prefix = f"{raw_secret[:12]}..."
        now_iso = datetime.now(timezone.utc).isoformat()

        with get_db() as conn:
            row = conn.execute("SELECT id, status, name, tier FROM api_keys WHERE id = ?", (key_id,)).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="API key request not found")

            conn.execute(
                """
                UPDATE api_keys
                SET status = 'active', key_hash = ?, prefix = ?, approved_at = ?
                WHERE id = ?
                """,
                (key_hash, prefix, now_iso, key_id),
            )

        return {
            "id": key_id,
            "status": "active",
            "name": row["name"],
            "tier": row["tier"],
            "api_key": raw_secret,  # Displayed once upon approval
            "message": "API key approved successfully. Save this secret key securely.",
            "approved_at": now_iso,
        }

    def revoke_key(self, key_id: str) -> Dict[str, Any]:
        """Revoke an active API key immediately."""
        with get_db() as conn:
            row = conn.execute("SELECT id, status FROM api_keys WHERE id = ?", (key_id,)).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="API key not found")
            conn.execute("UPDATE api_keys SET status = 'revoked' WHERE id = ?", (key_id,))

        return {"id": key_id, "status": "revoked", "message": "API key has been revoked."}

    def authenticate_and_rate_limit(self, token: str) -> Dict[str, Any]:
        """Validates API token, enforces RPM and monthly quota, and updates usage telemetry."""
        key_hash = self.hash_key(token)

        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM api_keys WHERE key_hash = ?", (key_hash,)
            ).fetchone()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key provided",
            )

        if row["status"] == "pending":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="API key is pending administrator approval",
            )

        if row["status"] == "revoked":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key has been revoked",
            )

        key_id = row["id"]
        now = time.time()
        rpm = row["rate_limit_rpm"] or 60
        quota = row["monthly_quota"] or 10000
        used = row["requests_used"] or 0

        # Check monthly quota
        if used >= quota:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Monthly API request quota exceeded ({quota} requests). Upgrade tier to continue.",
            )

        # Token Bucket / Sliding Window (1 minute)
        timestamps = self._rate_limits.setdefault(key_id, [])
        # Evict timestamps older than 60 seconds
        cutoff = now - 60.0
        self._rate_limits[key_id] = [t for t in timestamps if t > cutoff]

        if len(self._rate_limits[key_id]) >= rpm:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {rpm} requests per minute maximum for {row['tier']} tier.",
            )

        # Record this request
        self._rate_limits[key_id].append(now)

        # Increment usage in DB asynchronously / synchronously
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            with get_db() as conn:
                conn.execute(
                    "UPDATE api_keys SET requests_used = requests_used + 1, last_used_at = ? WHERE id = ?",
                    (now_iso, key_id),
                )
        except Exception:
            pass

        return dict(row)


api_key_manager = APIKeyManager()


async def get_current_api_key(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """
    FastAPI dependency that extracts and validates the API key.
    If no header is passed, defaults to the bootstrap sandbox master key for ease of use in local testing.
    """
    token: Optional[str] = None
    if x_api_key:
        token = x_api_key.strip()
    elif authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1].strip()
        else:
            token = authorization.strip()

    if not token:
        # Fallback to local sandbox key
        token = "gx_live_sandbox_master_key"

    return api_key_manager.authenticate_and_rate_limit(token)
