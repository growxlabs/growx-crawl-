import asyncio
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
import httpx

from growx_crawl.storage.db import get_db


class RobotsEngine:
    """
    Production-grade robots.txt compliance engine with in-memory + SQLite caching,
    crawl-delay extraction, sitemap discovery, and domain-level rules enforcement.
    """

    def __init__(self, cache_ttl_seconds: int = 86400):
        self.cache_ttl = cache_ttl_seconds
        self._parsers: Dict[str, tuple[RobotFileParser, float, List[str]]] = {}
        self._lock = asyncio.Lock()

    def _get_robots_url(self, target_url: str) -> tuple[str, str]:
        parsed = urlparse(target_url)
        scheme = parsed.scheme or "https"
        netloc = parsed.netloc
        domain = netloc.lower()
        robots_url = f"{scheme}://{domain}/robots.txt"
        return domain, robots_url

    async def get_parser(self, url: str) -> tuple[RobotFileParser, List[str]]:
        domain, robots_url = self._get_robots_url(url)
        now = time.time()

        # 1. In-memory check
        async with self._lock:
            if domain in self._parsers:
                parser, expires_at, sitemaps = self._parsers[domain]
                if now < expires_at:
                    return parser, sitemaps

        # 2. SQLite cache check
        cached_content: Optional[str] = None
        try:
            with get_db() as conn:
                row = conn.execute(
                    "SELECT content, expires_at FROM robots_cache WHERE domain = ?", (domain,)
                ).fetchone()
                if row:
                    exp = float(row["expires_at"])
                    if now < exp:
                        cached_content = row["content"]
        except Exception:
            pass

        # 3. Fetch from remote if not in SQLite or expired
        if cached_content is None:
            try:
                async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                    resp = await client.get(
                        robots_url,
                        headers={"User-Agent": "GrowXBot/1.0 (+https://growxlabs.com/bot)"},
                    )
                    if resp.status_code == 200:
                        cached_content = resp.text
                    else:
                        cached_content = ""
            except Exception:
                cached_content = ""

            # Store in SQLite cache
            try:
                expires_at_epoch = now + self.cache_ttl
                with get_db() as conn:
                    conn.execute(
                        """
                        INSERT INTO robots_cache (domain, content, status_code, fetched_at, expires_at)
                        VALUES (?, ?, 200, ?, ?)
                        ON CONFLICT(domain) DO UPDATE SET
                            content=excluded.content,
                            fetched_at=excluded.fetched_at,
                            expires_at=excluded.expires_at
                        """,
                        (domain, cached_content, str(now), str(expires_at_epoch)),
                    )
            except Exception:
                pass

        # 4. Parse content
        parser = RobotFileParser()
        parser.set_url(robots_url)
        lines = cached_content.splitlines() if cached_content else []
        parser.parse(lines)

        # Extract sitemaps manually
        sitemaps: List[str] = []
        for line in lines:
            if line.strip().lower().startswith("sitemap:"):
                parts = line.split(":", 1)
                if len(parts) > 1:
                    sitemaps.append(parts[1].strip())

        async with self._lock:
            self._parsers[domain] = (parser, now + self.cache_ttl, sitemaps)

        return parser, sitemaps

    async def can_fetch(self, url: str, user_agent: str = "*") -> bool:
        """Check whether user_agent is permitted by robots.txt to crawl url."""
        try:
            parser, _ = await self.get_parser(url)
            return parser.can_fetch(user_agent, url)
        except Exception:
            return True  # Permissive fallback on parse error

    async def get_crawl_delay(self, url: str, user_agent: str = "*") -> Optional[float]:
        """Return crawl delay in seconds specified in robots.txt if any."""
        try:
            parser, _ = await self.get_parser(url)
            delay = parser.crawl_delay(user_agent)
            return float(delay) if delay is not None else None
        except Exception:
            return None

    async def get_robots_info(self, url: str, user_agent: str = "*") -> Dict[str, Any]:
        """Return detailed robots.txt status for a URL."""
        domain, robots_url = self._get_robots_url(url)
        try:
            parser, sitemaps = await self.get_parser(url)
            allowed = parser.can_fetch(user_agent, url)
            delay = parser.crawl_delay(user_agent)
            return {
                "domain": domain,
                "robots_url": robots_url,
                "allowed": allowed,
                "crawl_delay": delay,
                "sitemaps": sitemaps,
            }
        except Exception as e:
            return {
                "domain": domain,
                "robots_url": robots_url,
                "allowed": True,
                "crawl_delay": None,
                "sitemaps": [],
                "error": str(e),
            }


robots_engine = RobotsEngine()
