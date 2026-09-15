import asyncio
import pytest
from growx_crawl.api.v1.router import v1_router
from growx_crawl.core.cache import ResponseCache
from growx_crawl.crawler.batch import batch_scraper
from growx_crawl.crawler.fetcher import fetcher_pipeline
from growx_crawl.crawler.multi_page import multi_page_crawler
from growx_crawl.crawler.scraper import scraper_engine
from growx_crawl.crawler.seo_audit import seo_auditor
from growx_crawl.extractors.structured import structured_extractor


@pytest.mark.asyncio
async def test_fast_http_fetcher():
    """Verify Fast HTTP mode fetches cleanly with low latency."""
    res = await fetcher_pipeline.fetch_fast("https://httpbin.org/html", timeout=15)
    assert res.status_code == 200
    assert "Herman Melville - Moby-Dick" in res.html
    assert res.fetcher_used == "fast"
    assert res.latency_ms > 0


@pytest.mark.asyncio
async def test_stealth_fetcher():
    """Verify Stealth mode operates with anti-detection headers."""
    res = await fetcher_pipeline.fetch_stealth("https://httpbin.org/headers", timeout=15)
    assert res.status_code == 200
    assert "User-Agent" in res.html
    assert res.fetcher_used == "stealth"


@pytest.mark.asyncio
async def test_structured_extractor_css_and_xpath():
    """Verify structured CSS and XPath extraction using Parsel."""
    selectors = {
        "title": "h1",
        "first_heading": "//h1/text()",
        "paragraphs": "p",
    }
    res = await structured_extractor.extract(
        url="https://httpbin.org/html",
        selectors=selectors,
        fetcher="fast",
        timeout=15,
    )
    assert res["status"] == "success"
    assert res["extracted_fields"] >= 2
    assert "Herman Melville - Moby-Dick" in str(res["data"]["title"])


@pytest.mark.asyncio
async def test_scraper_engine():
    """Verify full-page scraper parses metadata, links, and headings."""
    res = await scraper_engine.scrape("https://httpbin.org/html", fetcher="fast", timeout=15)
    assert res["status"] == "success"
    assert res["response_metadata"]["http_status"] == 200
    assert "data" in res
    assert "headings" in res["data"]
    assert "word_count" in res["response_metadata"]


@pytest.mark.asyncio
async def test_seo_audit_engine():
    """Verify SEO audit engine scores pages and checks AI readiness."""
    res = await seo_auditor.audit("https://httpbin.org/html", check_ai_readiness=True)
    assert res["status"] == "success"
    assert 0 <= res["overall_score"] <= 100
    assert "checks" in res
    assert "ai_readiness" in res


def test_response_cache():
    """Verify cache TTL and eviction."""
    cache = ResponseCache(default_ttl_seconds=1)
    cache.set("key1", {"data": "test"})
    assert cache.get("key1") == {"data": "test"}
    # Verify expiration
    import time
    time.sleep(1.1)
    assert cache.get("key1") is None


@pytest.mark.asyncio
async def test_batch_parallel_scraper():
    """Verify batch scraping up to multiple URLs in parallel."""
    urls = ["https://httpbin.org/status/200", "https://httpbin.org/status/201"]
    job = batch_scraper.create_batch(urls=urls)
    await batch_scraper.execute_batch(job.batch_id, concurrency=5)
    assert job.status == "completed"
    assert job.completed_count == 2
    assert len(job.results) == 2


@pytest.mark.asyncio
async def test_multi_page_crawler_limits():
    """Verify multi-page crawler enforces depth and page limits."""
    job = multi_page_crawler.create_job(
        seed_url="https://httpbin.org/html",
        max_depth=1,
        max_pages=2,
    )
    assert job.max_depth == 1
    assert job.max_pages == 2
    await multi_page_crawler.execute_crawl(job.job_id)
    assert job.status in ["completed", "failed"]
    assert job.pages_crawled <= 2


@pytest.mark.asyncio
async def test_stored_targets_endpoints():
    """Verify stored targets listing and target retrieval endpoints."""
    from growx_crawl.web.app import app
    import httpx

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        res = await client.get("/v1/targets?limit=5", headers={"Authorization": "Bearer gx_live_sandbox_master_key"})
        assert res.status_code == 200
        data = res.json()
        assert "total" in data
        assert "targets" in data
        assert isinstance(data["targets"], list)
        if data["total"] > 0:
            sample_id = data["targets"][0]["id"]
            single_res = await client.get(f"/v1/targets/{sample_id}", headers={"Authorization": "Bearer gx_live_sandbox_master_key"})
            assert single_res.status_code == 200
            assert "url" in single_res.json()
