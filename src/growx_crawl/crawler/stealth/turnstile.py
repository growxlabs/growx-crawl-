"""
Level 4: Automated Cloudflare Turnstile & Challenge Solver.
Detects interactive Cloudflare Turnstile verification iframes and solves them using human cursor physics.
"""

import asyncio
import logging
import random
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from growx_crawl.crawler.stealth.behavior import HumanBehavior

logger = logging.getLogger("growx_crawl.stealth.turnstile")

CHALLENGE_TITLE_KEYWORDS = [
    "just a moment...",
    "attention required! | cloudflare",
    "security check",
    "ddos protection",
]


class TurnstileDetector:
    """Detects and resolves Cloudflare Turnstile challenges in Playwright pages."""

    @staticmethod
    async def is_challenge_page(page: Any) -> bool:
        """Determines if the current page is a Cloudflare or WAF challenge barrier."""
        try:
            title = (await page.title()).lower()
            if any(k in title for k in CHALLENGE_TITLE_KEYWORDS):
                return True

            # Check for Cloudflare challenge elements
            cf_elements = await page.query_selector_all(
                "iframe[src*='challenges.cloudflare.com'], "
                "#challenge-stage, #cf-stage, .cf-turnstile, div[class*='turnstile']"
            )
            return len(cf_elements) > 0
        except Exception:
            return False

    @staticmethod
    async def solve(
        page: Any,
        timeout_seconds: int = 15,
    ) -> Dict[str, Any]:
        """
        Attempts to automatically solve Cloudflare Turnstile challenge using human cursor emulation.
        """
        if not await TurnstileDetector.is_challenge_page(page):
            return {"status": "not_present", "solved": False}

        logger.info("Cloudflare challenge detected. Initiating automated Turnstile solver...")
        hb = HumanBehavior(page)

        # Allow challenge iframe to initialize and mount into DOM
        try:
            await page.wait_for_selector(
                "iframe[src*='challenges.cloudflare.com'], div[class*='turnstile'] iframe, #cf-stage iframe",
                timeout=5000,
            )
        except Exception:
            pass
        await asyncio.sleep(random.uniform(0.8, 1.5))

        # Look for Turnstile iframe
        turnstile_frame_el = None
        selectors = [
            "iframe[src*='challenges.cloudflare.com']",
            "div[class*='turnstile'] iframe",
            "#cf-stage iframe",
            "iframe[title*='Cloudflare']",
        ]
        for sel in selectors:
            turnstile_frame_el = await page.query_selector(sel)
            if turnstile_frame_el:
                break

        if turnstile_frame_el:
            box = await turnstile_frame_el.bounding_box()
            if box:
                # The Turnstile checkbox square is precisely located 25-32px from the left edge
                # and centered vertically (approx 32px from top of a 65px widget)
                cb_x = box["x"] + random.uniform(26.0, 32.0)
                cb_y = box["y"] + box["height"] * 0.5

                logger.info(f"Targeting Turnstile verification checkbox at ({cb_x:.1f}, {cb_y:.1f})")

                # Move cursor with natural Bezier curve and click
                clicked = await hb.click((cb_x, cb_y), wait_after_ms=800)

                # Secondary fallback: click inside the frame context if accessible
                try:
                    frame = await turnstile_frame_el.content_frame()
                    if frame:
                        cb = await frame.query_selector("input[type='checkbox'], #challenge-stage, .ctp-checkbox-label")
                        if cb:
                            await cb.click(timeout=2000)
                except Exception:
                    pass

                if clicked:
                    # Poll for resolution (challenge disappearance or cookie injection)
                    start_time = asyncio.get_event_loop().time()
                    while asyncio.get_event_loop().time() - start_time < timeout_seconds:
                        await asyncio.sleep(0.5)
                        # Check cookies for cf_clearance
                        cookies = await page.context.cookies()
                        for c in cookies:
                            if c.get("name") == "cf_clearance":
                                logger.info("Turnstile solved successfully: cf_clearance acquired.")
                                return {
                                    "status": "solved",
                                    "solved": True,
                                    "method": "turnstile_click",
                                    "cf_clearance": c.get("value"),
                                }

                        # Check for Turnstile completion token in DOM
                        try:
                            token = await page.evaluate(
                                "() => document.querySelector('[name=\"cf-turnstile-response\"]')?.value || ''"
                            )
                            if token:
                                logger.info(f"Turnstile token acquired: {token[:20]}...")
                                return {
                                    "status": "solved",
                                    "solved": True,
                                    "method": "turnstile_token",
                                    "token": token,
                                }
                        except Exception:
                            pass

                        # Check if challenge title disappeared
                        title = (await page.title()).lower()
                        if not any(k in title for k in CHALLENGE_TITLE_KEYWORDS):
                            logger.info("Turnstile challenge passed (page redirected).")
                            return {"status": "solved", "solved": True, "method": "navigation"}

        # ── API Fallback: use CapSolver/2Captcha if click-based solve failed ──
        try:
            from growx_crawl.crawler.stealth.solver import captcha_solver, CaptchaType

            if captcha_solver.has_active_provider:
                logger.info("Click-based Turnstile failed. Falling back to API solver...")
                sitekey = await self._extract_turnstile_sitekey(page)
                if sitekey:
                    result = await captcha_solver.solve(
                        CaptchaType.TURNSTILE, page.url, sitekey
                    )
                    if result.success and result.token:
                        # Inject the token into the page
                        await page.evaluate(f"""() => {{
                            const resp = document.querySelector('[name="cf-turnstile-response"]');
                            if (resp) resp.value = '{result.token}';
                        }}""")
                        logger.info(f"Turnstile solved via API ({result.provider}) in {result.solve_time_ms}ms")
                        return {
                            "status": "solved",
                            "solved": True,
                            "method": f"api_{result.provider}",
                            "token": result.token,
                        }
        except Exception as api_err:
            logger.warning(f"API solver fallback failed: {api_err}")

        return {"status": "failed", "solved": False, "error": "Turnstile timeout or unresolved"}

    @staticmethod
    async def _extract_turnstile_sitekey(page: Any) -> Optional[str]:
        """Extract the Turnstile sitekey from the page DOM."""
        try:
            return await page.evaluate("""() => {
                const el = document.querySelector('[data-sitekey], .cf-turnstile[data-sitekey]');
                return el ? el.getAttribute('data-sitekey') : null;
            }""")
        except Exception:
            return None


async def solve_turnstile_if_present(page: Any, timeout_seconds: int = 12) -> bool:
    """Convenience helper to auto-clear Turnstile on any page if detected."""
    res = await TurnstileDetector.solve(page, timeout_seconds=timeout_seconds)
    return bool(res.get("solved"))
