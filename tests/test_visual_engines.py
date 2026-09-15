import pytest
from growx_crawl.crawler.screenshot import screenshot_engine
from growx_crawl.crawler.pdf import pdf_engine


@pytest.mark.asyncio
async def test_screenshot_engine_capture():
    """Verify Playwright captures high-res screenshots and saves to disk."""
    res = await screenshot_engine.capture(
        url="https://httpbin.org/html",
        format="png",
        full_page=True,
    )
    assert res["status"] == "success"
    assert res["format"] == "png"
    assert res["size_bytes"] > 0
    assert "file_path" in res


@pytest.mark.asyncio
async def test_pdf_engine_generate():
    """Verify Playwright compiles publication-grade PDF documents."""
    res = await pdf_engine.generate(
        url="https://httpbin.org/html",
        format="A4",
    )
    assert res["status"] == "success"
    assert res["format"] == "A4"
    assert res["size_bytes"] > 0
    assert "file_path" in res
