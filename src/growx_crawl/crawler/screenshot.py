import base64
from pathlib import Path
import time
import uuid
from typing import Any, Dict, Optional


class ScreenshotEngine:
    """
    Capability 5: High-Resolution Full-Page & Viewport Screenshot Capture (PNG/JPEG).
    """

    def __init__(self):
        self.output_dir = Path("exports/screenshots")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def capture(
        self,
        url: str,
        format: str = "png",
        full_page: bool = True,
        viewport: Optional[Dict[str, int]] = None,
        wait_ms: int = 500,
    ) -> Dict[str, Any]:
        vp = viewport or {"width": 1920, "height": 1080}
        img_id = f"scr_{uuid.uuid4().hex[:10]}"
        fmt = "jpeg" if format.lower() == "jpeg" else "png"
        filename = f"{img_id}.{fmt}"
        file_path = self.output_dir / filename

        start_time = time.time()
        try:
            from playwright.async_api import async_playwright
            from growx_crawl.crawler.stealth import apply_stealth_to_context, solve_turnstile_if_present
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-blink-features=AutomationControlled",
                    ],
                )
                context = await browser.new_context(viewport=vp)
                await apply_stealth_to_context(context)
                page = await context.new_page()
                try:
                    await page.goto(url, wait_until="load", timeout=30000)
                except Exception:
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)

                # Solve Turnstile challenge if present before taking screenshot
                await solve_turnstile_if_present(page, timeout_seconds=6)

                try:
                    await page.evaluate("() => document.fonts ? document.fonts.ready : Promise.resolve()")
                except Exception:
                    pass

                if wait_ms > 0:
                    await page.wait_for_timeout(wait_ms)

                screenshot_bytes = await page.screenshot(
                    path=str(file_path),
                    full_page=full_page,
                    type=fmt,
                )
                await browser.close()

                latency_ms = int((time.time() - start_time) * 1000)
                b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
                return {
                    "status": "success",
                    "url": url,
                    "format": fmt,
                    "full_page": full_page,
                    "dimensions": vp,
                    "file_path": str(file_path),
                    "file_name": filename,
                    "size_bytes": len(screenshot_bytes),
                    "base64_preview": f"data:image/{fmt};base64,{b64[:100]}... (truncated)",
                    "latency_ms": latency_ms,
                }
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "status": "error",
                "error": "ScreenshotCaptureFailed",
                "message": str(e),
                "latency_ms": latency_ms,
            }


screenshot_engine = ScreenshotEngine()
