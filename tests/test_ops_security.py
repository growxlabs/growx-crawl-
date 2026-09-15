import httpx
import pytest
from growx_crawl.core.ops_auth import AUTHORIZED_OPS_EMAIL, OPS_SECRET_KEY
from growx_crawl.web.app import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.asyncio
async def test_ops_page_routes():
    """Verify both /ops and /admin serve the Ops portal UI."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        r1 = await client.get("/ops")
        assert r1.status_code == 200
        assert "GrowX Ops Command" in r1.text
        assert "sai@growxlabs.tech" in r1.text

        r2 = await client.get("/admin")
        assert r2.status_code == 200
        assert "GrowX Ops Command" in r2.text


@pytest.mark.asyncio
async def test_unauthorized_email_rejected_with_403():
    """Verify that any email other than sai@growxlabs.tech is strictly rejected with 403."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Test generic outsider email
        r_outsider = await client.post(
            "/api/ops/login",
            json={"email": "hacker@evil.com", "passkey": OPS_SECRET_KEY},
        )
        assert r_outsider.status_code == 403
        assert "not authorized" in r_outsider.json()["detail"]
        assert AUTHORIZED_OPS_EMAIL in r_outsider.json()["detail"]

        # Test another email under the same domain
        r_domain = await client.post(
            "/api/ops/login",
            json={"email": "admin@growxlabs.tech", "passkey": OPS_SECRET_KEY},
        )
        assert r_domain.status_code == 403
        assert "not authorized" in r_domain.json()["detail"]


@pytest.mark.asyncio
async def test_sai_growxlabs_tech_invalid_passkey_401():
    """Verify that sai@growxlabs.tech with an invalid passkey gets 401."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        r = await client.post(
            "/api/ops/login",
            json={"email": AUTHORIZED_OPS_EMAIL, "passkey": "wrong_password"},
        )
        assert r.status_code == 401
        assert "Invalid Ops security passkey" in r.json()["detail"]


@pytest.mark.asyncio
async def test_sai_growxlabs_tech_authorized_login():
    """Verify that sai@growxlabs.tech with correct passkey succeeds and receives token."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        r = await client.post(
            "/api/ops/login",
            json={"email": AUTHORIZED_OPS_EMAIL, "passkey": OPS_SECRET_KEY},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"
        assert data["email"] == AUTHORIZED_OPS_EMAIL
        assert data["role"] == "super_admin"
        assert "gx_ops_session_" in data["token"]


@pytest.mark.asyncio
async def test_ops_endpoints_protected_and_accessible():
    """Verify administrative endpoints require session and return accurate data when authorized."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Unauthenticated request must fail with 401
        unauth_res = await client.get("/api/ops/billing")
        assert unauth_res.status_code == 401

        # 2. Authenticate as sai@growxlabs.tech
        login_res = await client.post(
            "/api/ops/login",
            json={"email": AUTHORIZED_OPS_EMAIL, "passkey": OPS_SECRET_KEY},
        )
        token = login_res.json()["token"]
        headers = {"X-Ops-Token": token}

        # 3. Session validation
        session_res = await client.get("/api/ops/session", headers=headers)
        assert session_res.status_code == 200
        assert session_res.json()["email"] == AUTHORIZED_OPS_EMAIL

        # 4. Billing & Metering
        billing_res = await client.get("/api/ops/billing", headers=headers)
        assert billing_res.status_code == 200
        assert "metering" in billing_res.json()

        # 5. Telemetry
        telemetry_res = await client.get("/api/ops/telemetry", headers=headers)
        assert telemetry_res.status_code == 200
        assert telemetry_res.json()["status"] == "online"
        assert telemetry_res.json()["anti_bot_evasion_rate"] >= 99

        # 6. Live Logs
        logs_res = await client.get("/api/ops/logs", headers=headers)
        assert logs_res.status_code == 200
        assert "logs" in logs_res.json()

        # 7. Audit Trail
        audit_res = await client.get("/api/ops/audit", headers=headers)
        assert audit_res.status_code == 200
        assert "audit" in audit_res.json()


@pytest.mark.asyncio
async def test_ops_client_key_management_lifecycle():
    """Verify Ops admin can create, list, and revoke client API keys."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Login
        login_res = await client.post(
            "/api/ops/login",
            json={"email": AUTHORIZED_OPS_EMAIL, "passkey": OPS_SECRET_KEY},
        )
        token = login_res.json()["token"]
        headers = {"X-Ops-Token": token}

        # Issue new client key
        create_res = await client.post(
            "/api/ops/clients/create",
            headers=headers,
            json={
                "name": "Test Hedge Fund",
                "email": "fund@testcapital.com",
                "tier": "enterprise",
                "monthly_quota": 50000,
            },
        )
        assert create_res.status_code == 200
        created_data = create_res.json()
        assert created_data["status"] == "success"
        assert created_data["api_key"].startswith("gx_live_")
        key_id = created_data["client_id"]

        # List keys and confirm presence
        list_res = await client.get("/api/ops/clients", headers=headers)
        assert list_res.status_code == 200
        keys = list_res.json()["clients"]
        matched = [k for k in keys if k["id"] == key_id]
        assert len(matched) == 1
        assert matched[0]["status"] == "active"
        assert matched[0]["monthly_quota"] == 50000

        # Revoke key
        revoke_res = await client.post(f"/api/ops/clients/{key_id}/revoke", headers=headers)
        assert revoke_res.status_code == 200
        assert revoke_res.json()["status"] == "revoked"

        # Confirm revoked status
        list_res2 = await client.get("/api/ops/clients", headers=headers)
        matched2 = [k for k in list_res2.json()["clients"] if k["id"] == key_id]
        assert matched2[0]["status"] == "revoked"
