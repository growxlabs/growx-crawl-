"""
Ghost Level: C++ Engine-Level Anti-Detect Browser with Camoufox & Session Aging.
Provides native OS and C++ fingerprint spoofing with persistent clearance caching.
"""

import asyncio
import logging
import random
import time
from urllib.parse import urlparse
from typing import Any, Dict, List, Optional

from growx_crawl.crawler.stealth.behavior import HumanBehavior, random_dwell
from growx_crawl.crawler.stealth.fingerprint import apply_stealth_to_context
from growx_crawl.crawler.stealth.turnstile import solve_turnstile_if_present
from growx_crawl.crawler.stealth.warmer import session_aging_manager

logger = logging.getLogger("growx_crawl.stealth.ghost")


class GhostEngine:
    """
    Ghost-Level Extraction Engine:
    Employs C++ binary anti-detection (Camoufox) or hardened Playwright Chromium,
    with persistent clearance session reuse and behavioral physics.
    """

    async def fetch(
        self,
        url: str,
        wait_for: Optional[str] = None,
        wait_ms: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
        proxy: Optional[str] = None,
        timeout: int = 35,
        warm_session: bool = False,
    ) -> Dict[str, Any]:
        start_time = time.time()
        domain = urlparse(url).netloc
        cached_cookies = session_aging_manager.get_session(domain)

        # 1. Attempt Native C++ Camoufox Engine
        try:
            from camoufox.async_api import AsyncCamoufox
            logger.info("Engaging Ghost Level C++ engine (Camoufox)...")

            async with AsyncCamoufox(
                headless=True,
                geoip=True if not proxy else False,
                proxy={"server": proxy} if proxy else None,
            ) as browser:
                context = await browser.new_context(extra_http_headers=headers or {})
                if cached_cookies:
                    logger.info(f"Injecting cached aged cookies for {domain}")
                    await context.add_cookies(cached_cookies)

                page = await context.new_page()
                try:
                    resp = await page.goto(url, timeout=timeout * 1000, wait_until="load")
                except Exception:
                    resp = await page.goto(url, timeout=timeout * 1000, wait_until="domcontentloaded")

                # Turnstile auto-solving
                await solve_turnstile_if_present(page, timeout_seconds=8)

                try:
                    await page.evaluate("() => document.fonts ? document.fonts.ready : Promise.resolve()")
                except Exception:
                    pass

                if wait_for:
                    try:
                        await page.wait_for_selector(wait_for, timeout=5000)
                    except Exception:
                        pass

                # Behavioral scroll & human dwell
                hb = HumanBehavior(page)
                await hb.scroll(max_bursts=2)
                await random_dwell(min_ms=300, max_ms=800)

                if wait_ms:
                    await page.wait_for_timeout(wait_ms)

                content = await page.content()
                status_code = resp.status if resp else 200

                # Cache newly acquired cookies & clearance state
                new_cookies = await context.cookies()
                ua = await page.evaluate("() => navigator.userAgent")
                session_aging_manager.save_session(domain, new_cookies, ua)

                latency_ms = int((time.time() - start_time) * 1000)
                return {
                    "html": content,
                    "status_code": status_code,
                    "fetcher_used": "ghost_c++",
                    "latency_ms": latency_ms,
                    "engine": "camoufox_native",
                }

        except Exception as camoufox_err:
            logger.info(f"Camoufox native skipped ({camoufox_err}). Utilizing Hardened Ghost Chromium.")

        # 2. Hardened Ghost Chromium with Session Aging & Pre-Warming
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                launch_args = [
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-features=IsolateOrigins,site-per-process",
                ]
                browser = await p.chromium.launch(
                    headless=True,
                    args=launch_args,
                    proxy={"server": proxy} if proxy else None,
                )
                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    extra_http_headers=headers or {},
                )

                # Pre-warm profile with authentic browsing history if requested
                if warm_session and not cached_cookies:
                    await session_aging_manager.warm_profile(context, max_warmup_pages=1)

                if cached_cookies:
                    await context.add_cookies(cached_cookies)

                await apply_stealth_to_context(context)
                page = await context.new_page()

                try:
                    resp = await page.goto(url, timeout=timeout * 1000, wait_until="load")
                except Exception:
                    resp = await page.goto(url, timeout=timeout * 1000, wait_until="domcontentloaded")

                await solve_turnstile_if_present(page, timeout_seconds=8)

                try:
                    await page.evaluate("() => document.fonts ? document.fonts.ready : Promise.resolve()")
                except Exception:
                    pass

                if wait_for:
                    try:
                        await page.wait_for_selector(wait_for, timeout=5000)
                    except Exception:
                        pass

                hb = HumanBehavior(page)
                await hb.scroll(max_bursts=2)
                await random_dwell(min_ms=300, max_ms=700)

                if wait_ms:
                    await page.wait_for_timeout(wait_ms)

                content = await page.content()
                status_code = resp.status if resp else 200

                # Cache clearance cookies
                new_cookies = await context.cookies()
                ua = await page.evaluate("() => navigator.userAgent")
                session_aging_manager.save_session(domain, new_cookies, ua)

                await context.close()
                await browser.close()

                latency_ms = int((time.time() - start_time) * 1000)
                return {
                    "html": content,
                    "status_code": status_code,
                    "fetcher_used": "ghost_chromium",
                    "latency_ms": latency_ms,
                    "engine": "stealth_playwright",
                }

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "html": "",
                "status_code": 500,
                "fetcher_used": "ghost",
                "latency_ms": latency_ms,
                "error": str(e),
            }


ghost_engine = GhostEngine()
