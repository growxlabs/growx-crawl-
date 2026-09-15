import httpx
import pytest
from bs4 import BeautifulSoup

from growx_crawl.crawler.scraper import ensure_base_href, scraper_engine
from growx_crawl.crawler.fetcher import FetcherResult
from growx_crawl.web.app import app
from growx_crawl.storage.db import get_db


def test_ensure_base_href_injection():
    """Verify ensure_base_href injects <base href="..."> into <head> properly."""
    # Scenario 1: Document with standard <head>
    html1 = "<!DOCTYPE html><html><head><title>Test</title><link rel='stylesheet' href='/css/app.css'></head><body>Hello</body></html>"
    res1 = ensure_base_href(html1, "https://example.com/blog/")
    assert '<base href="https://example.com/blog/">' in res1
    assert res1.index('<base href="https://example.com/blog/">') < res1.index('<link')

    # Scenario 2: Document with no <head> but <html>
    html2 = "<html><body><h1>No head</h1></body></html>"
    res2 = ensure_base_href(html2, "https://example.com/docs")
    assert '<base href="https://example.com/docs">' in res2

    # Scenario 3: Document already having <base>
    html3 = '<html><head><base href="https://other.com/"></head><body></body></html>'
    res3 = ensure_base_href(html3, "https://example.com/")
    assert res3.count("<base") == 1
    assert 'href="https://other.com/"' in res3


@pytest.mark.asyncio
async def test_scraper_css_extraction(monkeypatch):
    """Verify scraper engine parses linked stylesheets, resolves absolute URLs, and counts inline styles."""
    mock_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Full CSS Test</title>
        <link rel="stylesheet" href="/assets/main.css" media="screen" id="main-css">
        <link rel="stylesheet" href="https://cdn.example.com/theme.css">
        <link rel="icon" href="/favicon.ico">
        <style id="custom-theme">
            body { background: #000; color: #fff; }
            h1 { font-size: 2rem; }
        </style>
        <style>
            .container { max-width: 1200px; margin: 0 auto; }
        </style>
    </head>
    <body>
        <h1>Hello Styled World</h1>
        <p>Testing full page CSS crawling fidelity.</p>
        <a href="/about">About</a>
        <img src="/img/logo.png" alt="Logo">
    </body>
    </html>
    """

    async def mock_fetch(*args, **kwargs):
        return FetcherResult(
            html=mock_html,
            status_code=200,
            fetcher_used="fast",
            latency_ms=45,
            extra_data={
                "dynamic_stylesheets": [
                    {"href": "https://cdn.example.com/dynamic.css", "rules_count": 12, "media": "all"}
                ]
            }
        )

    from growx_crawl.crawler import scraper
    monkeypatch.setattr(scraper.fetcher_pipeline, "fetch", mock_fetch)

    result = await scraper_engine.scrape("https://example.com/products/item-1")

    assert result["status"] == "success"
    data = result["data"]

    # Verify stylesheet extraction
    assert "stylesheets" in data
    assert data["stylesheets_count"] >= 2

    hrefs = [s["href"] for s in data["stylesheets"]]
    # Should resolve relative path to absolute
    assert "https://example.com/assets/main.css" in hrefs
    assert "https://cdn.example.com/theme.css" in hrefs
    # Should include dynamic stylesheets from browser runtime
    assert "https://cdn.example.com/dynamic.css" in hrefs

    # Verify inline styles extraction
    assert data["inline_styles_count"] == 2
    assert data["inline_css_chars"] > 0

    # Verify target was persisted with base href
    target_id = result["target_id"]
    with get_db() as conn:
        row = conn.execute("SELECT html_content FROM pages WHERE target_id = ?", (target_id,)).fetchone()
        assert row is not None
        assert '<base href="https://example.com/products/item-1">' in row["html_content"]


@pytest.mark.asyncio
async def test_target_preview_endpoint():
    """Verify /v1/targets/{target_id}/preview renders HTML with base href."""
    job_id = "job_csstest_999"
    mock_id = "tgt_csstest_999"
    now_iso = "2026-09-14T12:00:00Z"
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO crawl_jobs (id, query, status, created_at) VALUES (?, 'https://testsite.org/app', 'completed', ?)",
            (job_id, now_iso),
        )
        conn.execute(
            "INSERT OR REPLACE INTO crawl_targets (id, job_id, url, domain, status, depth, discovered_at, started_at, completed_at) VALUES (?, ?, 'https://testsite.org/app', 'testsite.org', 'completed', 0, ?, ?, ?)",
            (mock_id, job_id, now_iso, now_iso, now_iso),
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO pages (
                id, job_id, target_id, url, status_code, content_type,
                html_content, title, text_content, created_at
            ) VALUES (?, ?, ?, 'https://testsite.org/app', 200, 'text/html', ?, 'Test Title', 'Test', ?)
            """,
            (
                f"page_{mock_id}",
                job_id,
                mock_id,
                "<html><head><link rel='stylesheet' href='/style.css'></head><body><h1>Preview Test</h1></body></html>",
                now_iso,
            ),
        )

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.get(f"/v1/targets/{mock_id}/preview")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert '<base href="https://testsite.org/app">' in resp.text
        assert "<h1>Preview Test</h1>" in resp.text
