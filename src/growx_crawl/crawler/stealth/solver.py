"""
Level 4: Universal CAPTCHA & Challenge Token Solver Adapter.
Supports all major CAPTCHA types across CapSolver and 2Captcha providers
with automatic failover, budget tracking, and challenge-type detection.
"""

import asyncio
import logging
import os
import time
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger("growx_crawl.stealth.solver")


class CaptchaType(str, Enum):
    TURNSTILE = "turnstile"
    RECAPTCHA_V2 = "recaptcha_v2"
    RECAPTCHA_V3 = "recaptcha_v3"
    HCAPTCHA = "hcaptcha"
    FUNCAPTCHA = "funcaptcha"
    IMAGE = "image_captcha"


class SolveResult:
    """Structured result from a CAPTCHA solve attempt."""

    __slots__ = ("success", "token", "provider", "captcha_type", "solve_time_ms", "error", "cost_usd")

    def __init__(
        self,
        success: bool = False,
        token: Optional[str] = None,
        provider: Optional[str] = None,
        captcha_type: Optional[str] = None,
        solve_time_ms: int = 0,
        error: Optional[str] = None,
        cost_usd: float = 0.0,
    ):
        self.success = success
        self.token = token
        self.provider = provider
        self.captcha_type = captcha_type
        self.solve_time_ms = solve_time_ms
        self.error = error
        self.cost_usd = cost_usd


# ── CapSolver task type mapping ──────────────────────────────────────────
_CAPSOLVER_TASK_TYPES = {
    CaptchaType.TURNSTILE: "AntiTurnstileTaskProxyLess",
    CaptchaType.RECAPTCHA_V2: "ReCaptchaV2TaskProxyLess",
    CaptchaType.RECAPTCHA_V3: "ReCaptchaV3TaskProxyLess",
    CaptchaType.HCAPTCHA: "HCaptchaTaskProxyLess",
    CaptchaType.FUNCAPTCHA: "FunCaptchaTaskProxyLess",
}

# ── 2Captcha method mapping ──────────────────────────────────────────────
_2CAPTCHA_METHODS = {
    CaptchaType.TURNSTILE: "turnstile",
    CaptchaType.RECAPTCHA_V2: "userrecaptcha",
    CaptchaType.RECAPTCHA_V3: "userrecaptcha",
    CaptchaType.HCAPTCHA: "hcaptcha",
    CaptchaType.FUNCAPTCHA: "funcaptcha",
}


class CaptchaSolverManager:
    """
    Universal CAPTCHA solver with multi-provider failover.

    Provider priority: CapSolver (faster, cheaper) → 2Captcha (fallback).
    Supports: Turnstile, reCAPTCHA v2/v3, hCaptcha, FunCaptcha.
    """

    CAPSOLVER_API = "https://api.capsolver.com"
    TWOCAPTCHA_API = "https://api.2captcha.com"

    def __init__(self):
        self.capsolver_key = os.getenv("CAPSOLVER_API_KEY")
        self.twocaptcha_key = os.getenv("TWOCAPTCHA_API_KEY")

        # Solve statistics
        self._total_solves = 0
        self._total_failures = 0
        self._total_cost_usd = 0.0

    @property
    def has_active_provider(self) -> bool:
        return bool(self.capsolver_key or self.twocaptcha_key)

    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "total_solves": self._total_solves,
            "total_failures": self._total_failures,
            "total_cost_usd": round(self._total_cost_usd, 4),
            "providers": {
                "capsolver": bool(self.capsolver_key),
                "twocaptcha": bool(self.twocaptcha_key),
            },
        }

    # ── Public API ───────────────────────────────────────────────────────

    async def solve(
        self,
        captcha_type: CaptchaType,
        website_url: str,
        website_key: str,
        action: Optional[str] = None,
        min_score: Optional[float] = None,
    ) -> SolveResult:
        """
        Solve any CAPTCHA type with automatic provider failover.

        Args:
            captcha_type: Type of CAPTCHA to solve.
            website_url: URL where the CAPTCHA is hosted.
            website_key: The sitekey/website key for the CAPTCHA widget.
            action: Required for reCAPTCHA v3 — the action parameter.
            min_score: Required for reCAPTCHA v3 — minimum score (0.1-0.9).
        """
        start = time.time()

        # Try CapSolver first (faster, cheaper)
        if self.capsolver_key:
            result = await self._solve_capsolver(
                captcha_type, website_url, website_key, action, min_score
            )
            if result.success:
                self._total_solves += 1
                return result
            logger.info(f"CapSolver failed for {captcha_type.value}: {result.error}. Trying 2Captcha...")

        # Fallback to 2Captcha
        if self.twocaptcha_key:
            result = await self._solve_2captcha(
                captcha_type, website_url, website_key, action, min_score
            )
            if result.success:
                self._total_solves += 1
                return result

        self._total_failures += 1
        elapsed = int((time.time() - start) * 1000)
        return SolveResult(
            success=False,
            captcha_type=captcha_type.value,
            solve_time_ms=elapsed,
            error="No solver provider available or all providers failed",
        )

    # Convenience shortcuts
    async def solve_turnstile(self, website_url: str, website_key: str) -> SolveResult:
        return await self.solve(CaptchaType.TURNSTILE, website_url, website_key)

    async def solve_recaptcha_v2(self, website_url: str, website_key: str) -> SolveResult:
        return await self.solve(CaptchaType.RECAPTCHA_V2, website_url, website_key)

    async def solve_recaptcha_v3(
        self, website_url: str, website_key: str, action: str = "verify", min_score: float = 0.7
    ) -> SolveResult:
        return await self.solve(
            CaptchaType.RECAPTCHA_V3, website_url, website_key, action=action, min_score=min_score
        )

    async def solve_hcaptcha(self, website_url: str, website_key: str) -> SolveResult:
        return await self.solve(CaptchaType.HCAPTCHA, website_url, website_key)

    # Legacy compatibility
    async def solve_turnstile_token(self, website_url: str, website_key: str) -> Optional[str]:
        """Backward-compatible method — returns raw token string or None."""
        result = await self.solve_turnstile(website_url, website_key)
        return result.token if result.success else None

    # ── CapSolver Implementation ─────────────────────────────────────────

    async def _solve_capsolver(
        self,
        captcha_type: CaptchaType,
        website_url: str,
        website_key: str,
        action: Optional[str] = None,
        min_score: Optional[float] = None,
    ) -> SolveResult:
        start = time.time()
        task_type = _CAPSOLVER_TASK_TYPES.get(captcha_type)
        if not task_type:
            return SolveResult(error=f"Unsupported type for CapSolver: {captcha_type.value}")

        task: Dict[str, Any] = {
            "type": task_type,
            "websiteURL": website_url,
            "websiteKey": website_key,
        }
        if captcha_type == CaptchaType.RECAPTCHA_V3:
            task["pageAction"] = action or "verify"
            task["minScore"] = min_score or 0.7

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Create task
                create_resp = await client.post(
                    f"{self.CAPSOLVER_API}/createTask",
                    json={"clientKey": self.capsolver_key, "task": task},
                )
                data = create_resp.json()
                if data.get("errorId", 0) != 0:
                    return SolveResult(
                        error=f"CapSolver create error: {data.get('errorDescription', 'unknown')}",
                        captcha_type=captcha_type.value,
                        provider="capsolver",
                    )
                task_id = data.get("taskId")
                if not task_id:
                    return SolveResult(error="No taskId returned", provider="capsolver")

                # Poll for result (max 90 seconds)
                for attempt in range(30):
                    await asyncio.sleep(3.0)
                    res = await client.post(
                        f"{self.CAPSOLVER_API}/getTaskResult",
                        json={"clientKey": self.capsolver_key, "taskId": task_id},
                    )
                    res_data = res.json()
                    status = res_data.get("status")
                    if status == "ready":
                        solution = res_data.get("solution", {})
                        token = (
                            solution.get("token")
                            or solution.get("gRecaptchaResponse")
                            or solution.get("captcha_response")
                        )
                        elapsed = int((time.time() - start) * 1000)
                        cost = res_data.get("cost", 0.0)
                        self._total_cost_usd += float(cost) if cost else 0.0
                        logger.info(
                            f"CapSolver solved {captcha_type.value} in {elapsed}ms "
                            f"(cost: ${cost})"
                        )
                        return SolveResult(
                            success=True,
                            token=token,
                            provider="capsolver",
                            captcha_type=captcha_type.value,
                            solve_time_ms=elapsed,
                            cost_usd=float(cost) if cost else 0.0,
                        )
                    if status == "failed":
                        return SolveResult(
                            error=f"CapSolver failed: {res_data.get('errorDescription', 'unknown')}",
                            provider="capsolver",
                            captcha_type=captcha_type.value,
                        )

                return SolveResult(error="CapSolver timeout (90s)", provider="capsolver")

        except Exception as e:
            logger.warning(f"CapSolver exception: {e}")
            return SolveResult(error=str(e), provider="capsolver", captcha_type=captcha_type.value)

    # ── 2Captcha Implementation ──────────────────────────────────────────

    async def _solve_2captcha(
        self,
        captcha_type: CaptchaType,
        website_url: str,
        website_key: str,
        action: Optional[str] = None,
        min_score: Optional[float] = None,
    ) -> SolveResult:
        start = time.time()
        method = _2CAPTCHA_METHODS.get(captcha_type)
        if not method:
            return SolveResult(error=f"Unsupported type for 2Captcha: {captcha_type.value}")

        params: Dict[str, Any] = {
            "key": self.twocaptcha_key,
            "method": method,
            "sitekey": website_key,
            "pageurl": website_url,
            "json": 1,
        }
        if captcha_type == CaptchaType.RECAPTCHA_V3:
            params["version"] = "v3"
            params["action"] = action or "verify"
            params["min_score"] = min_score or 0.7

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Submit task
                submit_resp = await client.post(
                    f"{self.TWOCAPTCHA_API}/in.php", data=params
                )
                submit_data = submit_resp.json()
                if submit_data.get("status") != 1:
                    return SolveResult(
                        error=f"2Captcha submit error: {submit_data.get('request', 'unknown')}",
                        provider="2captcha",
                        captcha_type=captcha_type.value,
                    )
                request_id = submit_data["request"]

                # Poll for result (max 120 seconds)
                for attempt in range(24):
                    await asyncio.sleep(5.0)
                    res = await client.get(
                        f"{self.TWOCAPTCHA_API}/res.php",
                        params={
                            "key": self.twocaptcha_key,
                            "action": "get",
                            "id": request_id,
                            "json": 1,
                        },
                    )
                    res_data = res.json()
                    if res_data.get("status") == 1:
                        token = res_data.get("request", "")
                        elapsed = int((time.time() - start) * 1000)
                        # 2Captcha: ~$3/1K = $0.003 per solve
                        cost = 0.003
                        self._total_cost_usd += cost
                        logger.info(
                            f"2Captcha solved {captcha_type.value} in {elapsed}ms"
                        )
                        return SolveResult(
                            success=True,
                            token=token,
                            provider="2captcha",
                            captcha_type=captcha_type.value,
                            solve_time_ms=elapsed,
                            cost_usd=cost,
                        )
                    if res_data.get("request") not in ("CAPCHA_NOT_READY",):
                        return SolveResult(
                            error=f"2Captcha error: {res_data.get('request', 'unknown')}",
                            provider="2captcha",
                            captcha_type=captcha_type.value,
                        )

                return SolveResult(error="2Captcha timeout (120s)", provider="2captcha")

        except Exception as e:
            logger.warning(f"2Captcha exception: {e}")
            return SolveResult(error=str(e), provider="2captcha", captcha_type=captcha_type.value)


# ── CAPTCHA Auto-Detector ────────────────────────────────────────────────

class CaptchaDetector:
    """Detects CAPTCHA type from a Playwright page's DOM."""

    @staticmethod
    async def detect(page: Any) -> Optional[CaptchaType]:
        """Inspects the page DOM and returns the detected CAPTCHA type, or None."""
        try:
            html = await page.content()
            html_lower = html.lower()

            # Cloudflare Turnstile
            if any(sig in html_lower for sig in [
                "challenges.cloudflare.com", "cf-turnstile", "turnstile"
            ]):
                return CaptchaType.TURNSTILE

            # reCAPTCHA
            if "google.com/recaptcha" in html_lower or "g-recaptcha" in html_lower:
                # v3 if grecaptcha.execute is used without visible widget
                if "grecaptcha.execute" in html_lower and "g-recaptcha-response" not in html_lower:
                    return CaptchaType.RECAPTCHA_V3
                return CaptchaType.RECAPTCHA_V2

            # hCaptcha
            if "hcaptcha.com" in html_lower or "h-captcha" in html_lower:
                return CaptchaType.HCAPTCHA

            # FunCaptcha (Arkose Labs)
            if "funcaptcha" in html_lower or "arkoselabs.com" in html_lower:
                return CaptchaType.FUNCAPTCHA

        except Exception:
            pass
        return None

    @staticmethod
    async def extract_sitekey(page: Any, captcha_type: CaptchaType) -> Optional[str]:
        """Extracts the sitekey for the detected CAPTCHA type from the page DOM."""
        try:
            if captcha_type in (CaptchaType.RECAPTCHA_V2, CaptchaType.RECAPTCHA_V3):
                key = await page.evaluate("""() => {
                    const el = document.querySelector('[data-sitekey]');
                    if (el) return el.getAttribute('data-sitekey');
                    // Check script src for sitekey param
                    const scripts = document.querySelectorAll('script[src*="recaptcha"]');
                    for (const s of scripts) {
                        const m = s.src.match(/[?&]render=([^&]+)/);
                        if (m) return m[1];
                    }
                    return null;
                }""")
                return key

            if captcha_type == CaptchaType.HCAPTCHA:
                return await page.evaluate("""() => {
                    const el = document.querySelector('[data-sitekey], .h-captcha[data-sitekey]');
                    return el ? el.getAttribute('data-sitekey') : null;
                }""")

            if captcha_type == CaptchaType.TURNSTILE:
                return await page.evaluate("""() => {
                    const el = document.querySelector('[data-sitekey], .cf-turnstile[data-sitekey]');
                    return el ? el.getAttribute('data-sitekey') : null;
                }""")

            if captcha_type == CaptchaType.FUNCAPTCHA:
                return await page.evaluate("""() => {
                    const el = document.querySelector('[data-pkey]');
                    return el ? el.getAttribute('data-pkey') : null;
                }""")

        except Exception:
            pass
        return None


async def auto_solve_captcha(page: Any, website_url: str) -> SolveResult:
    """
    All-in-one: detect CAPTCHA type on page, extract sitekey, solve via API,
    and inject the token back into the page.
    """
    detected = await CaptchaDetector.detect(page)
    if not detected:
        return SolveResult(success=True, error="No CAPTCHA detected")

    logger.info(f"Auto-detected {detected.value} CAPTCHA on {website_url}")
    sitekey = await CaptchaDetector.extract_sitekey(page, detected)
    if not sitekey:
        return SolveResult(error=f"Could not extract sitekey for {detected.value}")

    result = await captcha_solver.solve(detected, website_url, sitekey)
    if result.success and result.token:
        # Inject token back into the page
        try:
            if detected in (CaptchaType.RECAPTCHA_V2, CaptchaType.RECAPTCHA_V3):
                await page.evaluate(f"""() => {{
                    document.querySelector('#g-recaptcha-response')?.setAttribute('value', '{result.token}');
                    const textarea = document.querySelector('[name="g-recaptcha-response"]');
                    if (textarea) {{ textarea.value = '{result.token}'; textarea.style.display = 'block'; }}
                    if (typeof ___grecaptcha_cfg !== 'undefined') {{
                        Object.keys(___grecaptcha_cfg.clients).forEach(k => {{
                            const c = ___grecaptcha_cfg.clients[k];
                            Object.keys(c).forEach(kk => {{
                                if (c[kk]?.S) c[kk].S = '{result.token}';
                            }});
                        }});
                    }}
                }}""")
            elif detected == CaptchaType.HCAPTCHA:
                await page.evaluate(f"""() => {{
                    const resp = document.querySelector('[name="h-captcha-response"]');
                    if (resp) resp.value = '{result.token}';
                    const iframe_resp = document.querySelector('[data-hcaptcha-response]');
                    if (iframe_resp) iframe_resp.setAttribute('data-hcaptcha-response', '{result.token}');
                }}""")
            elif detected == CaptchaType.TURNSTILE:
                await page.evaluate(f"""() => {{
                    const resp = document.querySelector('[name="cf-turnstile-response"]');
                    if (resp) resp.value = '{result.token}';
                }}""")
            logger.info(f"Injected {detected.value} token into page DOM")
        except Exception as e:
            logger.warning(f"Token injection failed: {e}")

    return result


captcha_solver = CaptchaSolverManager()
captcha_detector = CaptchaDetector()
