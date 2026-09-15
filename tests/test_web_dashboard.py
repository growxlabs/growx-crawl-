import httpx
import pytest
from growx_crawl.web.app import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.asyncio
async def test_dashboard_root():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert "GrowX Crawl" in response.text


@pytest.mark.asyncio
async def test_api_overview():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/overview")
        assert response.status_code == 200
        data = response.json()
        assert "total_jobs" in data
        assert "total_leads" in data


@pytest.mark.asyncio
async def test_api_sources():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/sources")
        assert response.status_code == 200
        sources = response.json()
        assert len(sources) >= 2


@pytest.mark.asyncio
async def test_api_jobs_list():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/jobs")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_api_leads_list():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/leads")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
