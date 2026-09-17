import asyncio
import logging
import random
import time
from typing import Any, Dict, List, Optional
import httpx

from growx_crawl.crawler.proxies import ProxyTier, proxy_manager
from growx_crawl.crawler.stealth import (
    apply_stealth_to_context,
    ghost_engine,
    human_scroll,
    random_dwell,
    solve_turnstile_if_present,
    auto_solve_captcha,
)

logger = logging.getLogger("growx_crawl.fetcher")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]


class FetcherResult:
    def __init__(
        self,
        html: str,
        status_code: int,
        fetcher_used: str,
        latency_ms: int,
        escalated: bool = False,
        headers: Optional[Dict[str, str]] = None,
        error: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None,
    ):
        self.html = html
        self.status_code = status_code
        self.fetcher_used = fetcher_used
        self.latency_ms = latency_ms
        self.escalated = escalated
        self.headers = headers or {}
        self.error = error
        self.extra_data = extra_data or {}


def decode_response_html(resp: httpx.Response) -> str:
    """Safely decode HTTP response into string, decompressing br/zstd/gzip/deflate if needed."""
    content_encoding = resp.headers.get("content-encoding", "").lower()
    raw = resp.content

    # If already clean string and doesn't start with binary null bytes
    if resp.text and not resp.text.startswith("\x00") and "\x00\x00" not in resp.text[:50]:
        return resp.text

    try:
        if "br" in content_encoding:
            import brotli
            raw = brotli.decompress(raw)
        elif "zstd" in content_encoding:
            import zstandard
            dctx = zstandard.ZstdDecompressor()
            raw = dctx.decompress(raw)
        elif "gzip" in content_encoding:
            import gzip
            raw = gzip.decompress(raw)
        elif "deflate" in content_encoding:
            import zlib
            try:
                raw = zlib.decompress(raw)
            except zlib.error:
                raw = zlib.decompress(raw, -zlib.MAX_WBITS)
    except Exception:
        pass

    for enc in ["utf-8", "latin-1", "windows-1252"]:
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


class AutoEscalatingFetcher:
    """
    Auto-Escalating Fetcher Pipeline (5-Level Anti-Bot Bypass):
    Mode 1: Fast (HTTP/2 async client, ~80-120ms)
    Mode 2: Dynamic (Anti-detect Chromium via Playwright + WebGL/Canvas stealth + Turnstile auto-solver)
    Mode 3: Stealth (TLS & JA3/JA4 browser impersonation via curl_cffi + anti-bot bypass)
    """

    def __init__(self, default_timeout: int = 30):
        self.timeout = default_timeout

    async def fetch_fast(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        proxy: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> FetcherResult:
        """
        Mode 1: Fast HTTP - High throughput, minimal memory, ~100ms latency.
        """
        start_time = time.time()
        active_proxy = proxy or proxy_manager.get_proxy(ProxyTier.DIRECT)
        req_headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br, zstd",
        }
        if headers:
            req_headers.update(headers)

        transport = None
        if active_proxy:
            transport = httpx.AsyncHTTPTransport(proxy=active_proxy)

        try:
            async with httpx.AsyncClient(
                transport=transport,
                follow_redirects=True,
                timeout=timeout or self.timeout,
                verify=False,
            ) as client:
                resp = await client.get(url, headers=req_headers)
                latency_ms = int((time.time() - start_time) * 1000)
                proxy_manager.record_result(active_proxy, resp.status_code)
                html_text = decode_response_html(resp)
                return FetcherResult(
                    html=html_text,
                    status_code=resp.status_code,
                    fetcher_used="fast",
                    latency_ms=latency_ms,
                    headers=dict(resp.headers),
                )
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return FetcherResult(
                html="",
                status_code=500,
                fetcher_used="fast",
                latency_ms=latency_ms,
                error=str(e),
            )

    async def fetch_dynamic(
        self,
        url: str,
        wait_for: Optional[str] = None,
        wait_ms: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
        proxy: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> FetcherResult:
        """
        Mode 2: Dynamic JS - Anti-Detect Chromium with Level 2 fingerprint masking,
        Level 5 behavioral scrolling, and Level 4 Turnstile auto-clearance.
        """
        start_time = time.time()
        t = timeout or self.timeout
        active_proxy = proxy or proxy_manager.get_proxy(ProxyTier.DIRECT)

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
                    proxy={"server": active_proxy} if active_proxy else None,
                )
                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent=random.choice(USER_AGENTS),
                    extra_http_headers=headers or {},
                )

                # Level 2: Apply deep anti-detect fingerprint masking
                await apply_stealth_to_context(context)

                page = await context.new_page()
                try:
                    resp = await page.goto(url, timeout=t * 1000, wait_until="load")
                except Exception:
                    # Fallback to domcontentloaded if external assets/trackers timeout
                    resp = await page.goto(url, timeout=t * 1000, wait_until="domcontentloaded")

                # Level 4: Auto-detect and solve any CAPTCHA (Turnstile, reCAPTCHA, hCaptcha, etc.)
                await solve_turnstile_if_present(page, timeout_seconds=8)
                solve_result = await auto_solve_captcha(page, url)
                if solve_result.success and solve_result.token:
                    logger.info(f"CAPTCHA solved: {solve_result.captcha_type} via {solve_result.provider}")

                # Ensure web fonts and external stylesheets finish computing
                try:
                    await page.evaluate("() => document.fonts ? document.fonts.ready : Promise.resolve()")
                except Exception:
                    pass

                if wait_for:
                    try:
                        await page.wait_for_selector(wait_for, timeout=5000)
                    except Exception:
                        pass

                # Level 5: Behavioral scrolling & human dwell
                if wait_ms:
                    await page.wait_for_timeout(wait_ms)
                else:
                    await page.wait_for_timeout(400)

                # Extract runtime CSS stylesheets and dynamic CSS rules
                dynamic_stylesheets = []
                try:
                    dynamic_stylesheets = await page.evaluate("""() => {
                        const results = [];
                        for (const s of document.styleSheets) {
                            try {
                                results.push({
                                    href: s.href || null,
                                    rules_count: s.cssRules ? s.cssRules.length : 0,
                                    media: s.media ? s.media.mediaText : null,
                                    title: s.title || null
                                });
                            } catch(e) {
                                results.push({ href: s.href || null, rules_count: 0, cors: true });
                            }
                        }
                        return results;
                    }""")
                except Exception:
                    pass

                content = await page.content()
                status_code = resp.status if resp else 200
                await context.close()
                await browser.close()

                proxy_manager.record_result(active_proxy, status_code)
                latency_ms = int((time.time() - start_time) * 1000)
                return FetcherResult(
                    html=content,
                    status_code=status_code,
                    fetcher_used="dynamic",
                    latency_ms=latency_ms,
                    extra_data={"dynamic_stylesheets": dynamic_stylesheets},
                )
        except Exception as e:
            # Fallback to fast mode with dynamic tag if browser launch was interrupted
            res = await self.fetch_fast(url, headers=headers, proxy=active_proxy, timeout=timeout)
            res.fetcher_used = "dynamic"
            res.error = f"DynamicBrowserWarning: {str(e)}"
            return res

    async def fetch_stealth(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        proxy: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> FetcherResult:
        """
        Mode 3: Stealth - TLS / JA3 / JA4 browser fingerprint spoofing via curl_cffi.
        """
        start_time = time.time()
        t = timeout or self.timeout
        active_proxy = proxy or proxy_manager.get_proxy(ProxyTier.DIRECT)
        ua = random.choice(USER_AGENTS)

        stealth_headers = {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not?A_Brand";v="99"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        }
        if headers:
            stealth_headers.update(headers)

        # 1. Primary: curl_cffi TLS impersonation
        try:
            from curl_cffi.requests import AsyncSession
            proxies = {"http": active_proxy, "https": active_proxy} if active_proxy else None
            async with AsyncSession(impersonate="chrome124") as s:
                resp = await s.get(
                    url,
                    headers=stealth_headers,
                    proxies=proxies,
                    timeout=t,
                    allow_redirects=True,
                )
                latency_ms = int((time.time() - start_time) * 1000)
                proxy_manager.record_result(active_proxy, resp.status_code)
                return FetcherResult(
                    html=resp.text,
                    status_code=resp.status_code,
                    fetcher_used="stealth",
                    latency_ms=latency_ms,
                    headers=dict(resp.headers),
                )
        except Exception:
            # 2. Secondary fallback: httpx with advanced browser spoof headers
            res = await self.fetch_fast(url, headers=stealth_headers, proxy=active_proxy, timeout=timeout)
            res.fetcher_used = "stealth"
            return res

    async def fetch_ghost(
        self,
        url: str,
        wait_for: Optional[str] = None,
        wait_ms: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
        proxy: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> FetcherResult:
        """
        Mode 4: Ghost Level - Native C++ / Camoufox Engine with session aging,
        genuine cookie vaults, and behavioral mouse physics.
        """
        active_proxy = proxy or proxy_manager.get_proxy(ProxyTier.RESIDENTIAL)
        res = await ghost_engine.fetch(
            url=url,
            wait_for=wait_for,
            wait_ms=wait_ms,
            headers=headers,
            proxy=active_proxy,
            timeout=timeout or 35,
        )
        return FetcherResult(
            html=res.get("html", ""),
            status_code=res.get("status_code", 200),
            fetcher_used=res.get("fetcher_used", "ghost"),
            latency_ms=res.get("latency_ms", 0),
            error=res.get("error"),
        )

    async def fetch(
        self,
        url: str,
        mode: str = "auto",
        wait_for: Optional[str] = None,
        wait_ms: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
        proxy: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> FetcherResult:
        """
        Auto-escalating fetch pipeline (4 Tiers):
        Executes Fast HTTP -> Dynamic JS -> Stealth -> Ghost Level based on target resistance.
        """
        mode_lower = mode.lower()
        if mode_lower == "fast":
            return await self.fetch_fast(url, headers=headers, proxy=proxy, timeout=timeout)
        elif mode_lower == "dynamic":
            return await self.fetch_dynamic(
                url, wait_for=wait_for, wait_ms=wait_ms, headers=headers, proxy=proxy, timeout=timeout
            )
        elif mode_lower == "stealth":
            return await self.fetch_stealth(url, headers=headers, proxy=proxy, timeout=timeout)
        elif mode_lower == "ghost":
            return await self.fetch_ghost(
                url, wait_for=wait_for, wait_ms=wait_ms, headers=headers, proxy=proxy, timeout=timeout
            )

        # ── AUTO ESCALATION PIPELINE ──
        # Step 1: Attempt Fast HTTP
        fast_res = await self.fetch_fast(url, headers=headers, proxy=proxy, timeout=timeout)
        if fast_res.status_code == 200 and not self._is_challenge_or_empty(fast_res.html):
            return fast_res

        # If challenged or blocked and no explicit proxy, attempt proxy escalation
        escalated_proxy = proxy
        if not proxy and (fast_res.status_code in (403, 429) or self._is_challenge_or_empty(fast_res.html)):
            _, escalated_proxy = proxy_manager.escalate_tier(ProxyTier.DIRECT)

        # Step 2: Escalate to Dynamic JS with Level 2 Anti-Detect + Level 4 Turnstile solver
        dynamic_res = await self.fetch_dynamic(
            url, wait_for=wait_for, wait_ms=wait_ms, headers=headers, proxy=escalated_proxy, timeout=timeout
        )
        dynamic_res.escalated = True
        if dynamic_res.status_code == 200 and not self._is_challenge_or_empty(dynamic_res.html):
            return dynamic_res

        # Step 3: Escalate to Stealth (TLS fingerprint impersonation & anti-bot evasion)
        stealth_res = await self.fetch_stealth(url, headers=headers, proxy=escalated_proxy, timeout=timeout)
        stealth_res.escalated = True
        if stealth_res.status_code == 200 and not self._is_challenge_or_empty(stealth_res.html):
            return stealth_res

        # Step 4: Final Escalation to Ghost Level (C++ Camoufox / Hardened Session Aging)
        ghost_res = await self.fetch_ghost(
            url, wait_for=wait_for, wait_ms=wait_ms, headers=headers, proxy=escalated_proxy, timeout=timeout
        )
        ghost_res.escalated = True
        return ghost_res

    def _is_challenge_or_empty(self, html: str) -> bool:
        if not html or len(html.strip()) < 150:
            return True
        lower = html.lower()
        bot_signatures = [
            # Cloudflare
            "cf-browser-verification",
            "challenge-platform",
            "cloudflare turnstile",
            "cf-chl-bypass",
            "just a moment...",
            # DataDome
            "datadome",
            "captcha-delivery.com",
            # PerimeterX / HUMAN
            "px-captcha",
            "perimeterx",
            "_px3",
            # Imperva / Incapsula
            "incapsula_resource",
            "_incap_",
            # Akamai
            "akamai-bot-manager",
            "akamai ghost",
            # DDoS-Guard & AWS WAF
            "ddos-guard",
            "aws waf captcha",
            # reCAPTCHA
            "google.com/recaptcha",
            "g-recaptcha",
            "grecaptcha",
            # hCaptcha
            "hcaptcha.com",
            "h-captcha",
            # FunCaptcha / Arkose Labs
            "arkoselabs.com",
            "funcaptcha",
            # Generic challenge phrases
            "please verify you are a human",
            "unusual traffic from your computer network",
            "access denied",
            "attention required! | cloudflare",
        ]
        return any(sig in lower for sig in bot_signatures)


fetcher_pipeline = AutoEscalatingFetcher()
