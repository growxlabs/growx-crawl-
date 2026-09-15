"""
Level 3: Smart Tiered Proxy Orchestrator.
Manages proxy pools across tiers (Direct -> Datacenter -> Residential/Mobile) with automatic failure escalation.
"""

import logging
import os
import random
import time
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("growx_crawl.proxies")


class ProxyTier:
    DIRECT = 0
    DATACENTER = 1
    RESIDENTIAL = 2
    MOBILE = 3


class ProxyPoolManager:
    """Manages multi-tier proxy rotation, health tracking, and circuit-breaking escalation."""

    def __init__(self):
        self.datacenter_proxies: List[str] = self._load_proxies("DATACENTER_PROXIES", "PROXY_URL")
        self.residential_proxies: List[str] = self._load_proxies("RESIDENTIAL_PROXIES")
        self.mobile_proxies: List[str] = self._load_proxies("MOBILE_PROXIES")

        # Proxy health: proxy_url -> {"failures": int, "cooldown_until": float}
        self.health: Dict[str, Dict[str, float]] = {}

    def _load_proxies(self, *env_keys: str) -> List[str]:
        proxies = []
        for key in env_keys:
            val = os.getenv(key, "").strip()
            if val:
                for item in val.split(","):
                    item = item.strip()
                    if item and item not in proxies:
                        proxies.append(item)
        return proxies

    def get_proxy(self, tier: int = ProxyTier.DIRECT) -> Optional[str]:
        """Returns an available healthy proxy for the specified tier, or None for Direct."""
        if tier == ProxyTier.DIRECT:
            return None

        candidates = []
        if tier == ProxyTier.DATACENTER:
            candidates = self.datacenter_proxies
        elif tier == ProxyTier.RESIDENTIAL:
            candidates = self.residential_proxies or self.datacenter_proxies
        elif tier == ProxyTier.MOBILE:
            candidates = self.mobile_proxies or self.residential_proxies or self.datacenter_proxies

        if not candidates:
            return None

        # Filter out proxies currently in cooldown
        now = time.time()
        healthy = [p for p in candidates if self.health.get(p, {}).get("cooldown_until", 0) <= now]
        chosen = random.choice(healthy) if healthy else random.choice(candidates)
        return chosen

    def escalate_tier(self, current_tier: int) -> Tuple[int, Optional[str]]:
        """Escalates to the next higher proxy tier upon 403/429/Anti-Bot detection."""
        next_tier = min(current_tier + 1, ProxyTier.MOBILE)
        proxy = self.get_proxy(next_tier)
        logger.warning(f"Escalating proxy tier from {current_tier} to {next_tier} (Proxy: {bool(proxy)})")
        return next_tier, proxy

    def record_result(self, proxy: Optional[str], status_code: int) -> None:
        """Records outcome to maintain health and cooldown unhealthy IPs."""
        if not proxy:
            return

        now = time.time()
        info = self.health.setdefault(proxy, {"failures": 0, "cooldown_until": 0.0})

        if status_code in (403, 429, 503):
            info["failures"] += 1
            # Exponential backoff cooldown up to 10 minutes
            cooldown_seconds = min(600, 30 * (2 ** (info["failures"] - 1)))
            info["cooldown_until"] = now + cooldown_seconds
            logger.info(f"Proxy {proxy[:25]}... rate-limited. Cooldown for {cooldown_seconds}s.")
        elif status_code == 200:
            info["failures"] = max(0, info["failures"] - 1)


proxy_manager = ProxyPoolManager()
