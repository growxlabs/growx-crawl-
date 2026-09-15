"""
Ghost Level: Session Aging & Cookie Profile Pre-Warmer.
Generates authentic browsing history, aged tracking cookies, and persistent clearance state.
"""

import asyncio
import json
import logging
from pathlib import Path
import random
import time
from typing import Any, Dict, List, Optional

from growx_crawl.crawler.stealth.behavior import HumanBehavior, random_dwell
from growx_crawl.storage.db import get_db

logger = logging.getLogger("growx_crawl.stealth.warmer")

WARMUP_SEED_DOMAINS = [
    "https://www.wikipedia.org",
    "https://news.ycombinator.com",
    "https://httpbin.org/cookies",
]


class SessionAgingManager:
    """
    Maintains persistent, aged browser storage states (cookies, localStorage, clearance tokens).
    Prevents newly initialized "naked" browser profiles from triggering low-trust bot scores.
    """

    def __init__(self, profiles_dir: Optional[str] = None):
        self.profiles_dir = Path(profiles_dir or "data/profiles")
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_table()

    def _ensure_table(self):
        """Ensures the clearance_sessions table exists in SQLite storage."""
        try:
            with get_db() as conn:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS clearance_sessions (
                    domain TEXT PRIMARY KEY,
                    cookies_json TEXT NOT NULL,
                    user_agent TEXT NOT NULL,
                    trust_score REAL DEFAULT 0.9,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                );
                """)
        except Exception as e:
            logger.warning(f"Could not initialize clearance_sessions table: {e}")

    def save_session(
        self,
        domain: str,
        cookies: List[Dict[str, Any]],
        user_agent: str,
        ttl_seconds: int = 86400,
    ) -> None:
        """Stores clearance cookies (e.g. cf_clearance) for a domain."""
        now = time.time()
        expires_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now + ttl_seconds))
        created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))
        cookies_str = json.dumps(cookies)

        try:
            with get_db() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO clearance_sessions 
                    (domain, cookies_json, user_agent, trust_score, created_at, expires_at)
                    VALUES (?, ?, ?, 0.9, ?, ?)
                    """,
                    (domain, cookies_str, user_agent, created_at, expires_at),
                )
            logger.info(f"Saved aged session for domain: {domain}")
        except Exception as e:
            logger.warning(f"Failed to persist session: {e}")

    def get_session(self, domain: str) -> Optional[List[Dict[str, Any]]]:
        """Retrieves cached unexpired clearance cookies for a domain."""
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        try:
            with get_db() as conn:
                row = conn.execute(
                    "SELECT cookies_json FROM clearance_sessions WHERE domain = ? AND expires_at > ?",
                    (domain, now_iso),
                ).fetchone()
                if row:
                    return json.loads(row["cookies_json"])
        except Exception:
            pass
        return None

    async def warm_profile(
        self,
        context: Any,
        target_domain: Optional[str] = None,
        max_warmup_pages: int = 2,
    ) -> None:
        """
        Executes a background warm-up routine:
        Navigates through high-reputation domains, simulates human scrolling,
        and accumulates genuine third-party ad/analytics cookies.
        """
        logger.info("Initializing Ghost profile pre-warmer...")
        page = await context.new_page()
        hb = HumanBehavior(page)

        seeds = random.sample(WARMUP_SEED_DOMAINS, min(max_warmup_pages, len(WARMUP_SEED_DOMAINS)))
        for seed_url in seeds:
            try:
                logger.info(f"Warming profile with {seed_url}")
                await page.goto(seed_url, timeout=15000, wait_until="domcontentloaded")
                await random_dwell(min_ms=400, max_ms=900)
                await hb.scroll(max_bursts=2)
            except Exception:
                continue

        await page.close()
        logger.info("Profile warming complete. Authentic cookies acquired.")


session_aging_manager = SessionAgingManager()
