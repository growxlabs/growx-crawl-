import asyncio
import pytest
from growx_crawl.api.v1.router import ExtractFromTargetRequest, extract_from_target
from growx_crawl.core.auth import api_key_manager, get_current_api_key
from growx_crawl.crawler.batch import batch_scraper
from growx_crawl.crawler.multi_page import multi_page_crawler
from growx_crawl.crawler.robots import robots_engine
from growx_crawl.crawler.scraper import scraper_engine
from growx_crawl.extractors.structured import structured_extractor
from growx_crawl.storage.db import get_db


@pytest.mark.asyncio
async def test_robots_txt_engine():
    """Verify robots.txt compliance engine parses rules and caches them."""
    # Test checking a known URL
    info = await robots_engine.get_robots_info("https://httpbin.org/html")
    assert "domain" in info
    assert "allowed" in info
    assert isinstance(info["allowed"], bool)

    # Test can_fetch
    can_fetch = await robots_engine.can_fetch("https://httpbin.org/status/200")
    assert isinstance(can_fetch, bool)


@pytest.mark.asyncio
async def test_api_key_lifecycle():
    """Verify end-to-end API key management: request, approve, authenticate, rate limit, revoke."""
    # 1. Request key
    req_res = api_key_manager.request_key(
        name="Test Corp",
        email="test@corp.com",
        tier="growth",
    )
    assert req_res["status"] == "pending"
    key_id = req_res["id"]
    assert req_res["rate_limit_rpm"] == 300

    # 2. List keys and find pending key
    pending_keys = api_key_manager.list_keys(status_filter="pending")
    assert any(k["id"] == key_id for k in pending_keys)

    # 3. Approve key
    appr_res = api_key_manager.approve_key(key_id)
    assert appr_res["status"] == "active"
    secret_key = appr_res["api_key"]
    assert secret_key.startswith("gx_live_")

    # 4. Authenticate with active key
    auth_data = api_key_manager.authenticate_and_rate_limit(secret_key)
    assert auth_data["id"] == key_id
    assert auth_data["status"] == "active"
    assert auth_data["tier"] == "growth"

    # 5. Revoke key
    rev_res = api_key_manager.revoke_key(key_id)
    assert rev_res["status"] == "revoked"

    # 6. Verify revoked key is rejected
    with pytest.raises(Exception):
        api_key_manager.authenticate_and_rate_limit(secret_key)


@pytest.mark.asyncio
async def test_persistent_target_page_storage_and_extraction():
    """Verify single-page scrape stores snapshot with target_id, and extract-from extracts from SQLite."""
    # 1. Scrape page
    scrape_res = await scraper_engine.scrape("https://httpbin.org/html", fetcher="fast", timeout=15)
    assert scrape_res["status"] == "success"
    target_id = scrape_res.get("target_id")
    assert target_id is not None
    assert target_id.startswith("tgt_")

    # 2. Verify snapshot is stored in SQLite
    with get_db() as conn:
        row = conn.execute("SELECT * FROM pages WHERE target_id = ?", (target_id,)).fetchone()
        assert row is not None
        assert "Moby-Dick" in row["html_content"]

    # 3. Extract from stored target_id using extract_from_target
    req = ExtractFromTargetRequest(
        target_id=target_id,
        selectors={"extracted_h1": "h1"},
    )
    extract_res = await extract_from_target(req, auth={"prefix": "test"})
    assert extract_res["status"] == "success"
    assert extract_res["target_id"] == target_id
    assert extract_res["source"] == "sqlite_page_snapshot"
    assert "Herman Melville - Moby-Dick" in str(extract_res["data"]["extracted_h1"])


@pytest.mark.asyncio
async def test_durable_jobs_persistence():
    """Verify crawl and batch jobs persist to SQLite and are retrievable."""
    # 1. Crawl job
    job = multi_page_crawler.create_job(
        seed_url="https://httpbin.org/html",
        max_depth=1,
        max_pages=1,
    )
    await multi_page_crawler.execute_crawl(job.job_id)

    # Clear memory cache to simulate process restart
    multi_page_crawler.jobs.clear()

    # Re-retrieve from SQLite
    restored_job = multi_page_crawler.get_job(job.job_id)
    assert restored_job is not None
    assert restored_job.seed_url == "https://httpbin.org/html"
    assert restored_job.status == "completed"

    # 2. Batch job
    batch_job = batch_scraper.create_batch(urls=["https://httpbin.org/status/200"])
    await batch_scraper.execute_batch(batch_job.batch_id, concurrency=2)

    # Clear batch memory cache
    batch_scraper.jobs.clear()

    # Re-retrieve from SQLite
    restored_batch = batch_scraper.get_batch(batch_job.batch_id)
    assert restored_batch is not None
    assert restored_batch.status == "completed"
    assert len(restored_batch.results) == 1


@pytest.mark.asyncio
async def test_aeo360_analyze_route():
    """Verify /v1/aeo360/analyze endpoint route returns full AI & SEO audit."""
    from growx_crawl.api.v1.router import SEOAuditRequest, analyze_aeo360
    req = SEOAuditRequest(url="https://httpbin.org/html", check_ai_readiness=True)
    res = await analyze_aeo360(req, auth={"prefix": "test"})
    assert res["status"] == "success"
    assert "ai_readiness" in res
    assert "checks" in res
    assert res["overall_score"] > 0
