"""
Level 4: External CAPTCHA & Challenge Token Solver Adapter.
Supports pluggable automated solving via CapSolver, 2Captcha, or custom token solvers.
"""

import asyncio
import logging
import os
from typing import Any, Dict, Optional
import httpx

logger = logging.getLogger("growx_crawl.stealth.solver")


class CaptchaSolverManager:
    """Pluggable third-party solver adapter for hard CAPTCHAs & Turnstile tokens."""

    def __init__(self):
        self.capsolver_key = os.getenv("CAPSOLVER_API_KEY")
        self.twocaptcha_key = os.getenv("TWOCAPTCHA_API_KEY")

    @property
    def has_active_provider(self) -> bool:
        return bool(self.capsolver_key or self.twocaptcha_key)

    async def solve_turnstile_token(
        self,
        website_url: str,
        website_key: str,
    ) -> Optional[str]:
        """
        Submits Turnstile challenge to CapSolver or 2Captcha and returns response token.
        """
        if self.capsolver_key:
            return await self._solve_capsolver(website_url, website_key)
        return None

    async def _solve_capsolver(self, website_url: str, website_key: str) -> Optional[str]:
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                create_resp = await client.post(
                    "https://api.capsolver.com/createTask",
                    json={
                        "clientKey": self.capsolver_key,
                        "task": {
                            "type": "AntiTurnstileTaskProxyLess",
                            "websiteURL": website_url,
                            "websiteKey": website_key,
                        },
                    },
                )
                task_data = create_resp.json()
                task_id = task_data.get("taskId")
                if not task_id:
                    return None

                # Poll for result
                for _ in range(15):
                    await asyncio.sleep(2.0)  # Polling delay
                    res_resp = await client.post(
                        "https://api.capsolver.com/getTaskResult",
                        json={"clientKey": self.capsolver_key, "taskId": task_id},
                    )
                    res_data = res_resp.json()
                    if res_data.get("status") == "ready":
                        return res_data.get("solution", {}).get("token")
        except Exception as e:
            logger.warning(f"CapSolver execution failed: {e}")
        return None


captcha_solver = CaptchaSolverManager()
