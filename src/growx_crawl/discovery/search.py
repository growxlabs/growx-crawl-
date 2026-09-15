import os
import urllib.parse
from typing import Any, Dict, List, Optional
import httpx
from bs4 import BeautifulSoup
from growx_crawl.discovery.base import DiscoveryProvider
from growx_crawl.discovery.url_classifier import URLClassifier
from growx_crawl.models.discovery import DiscoveryCandidate
from growx_crawl.normalization.normalizer import Normalizer


class SearchProvider(DiscoveryProvider):
    def __init__(self, user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"):
        self.user_agent = user_agent
        self.api_key = os.getenv("SEARCH_API_KEY")

    def health_check(self) -> Dict[str, Any]:
        return {
            "name": "SearchProvider",
            "status": "configured" if self.api_key else "available (DuckDuckGo fallback)",
            "api_key_set": bool(self.api_key),
        }

    async def discover(
        self,
        query: str,
        job_id: str,
        location: Optional[str] = None,
        industry: Optional[str] = None,
        limit: int = 50,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[DiscoveryCandidate]:
        candidates: List[DiscoveryCandidate] = []
        seen_domains = set()

        search_query = f"{query} {location or ''}".strip()
        encoded_query = urllib.parse.quote_plus(search_query)
        search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        headers = {"User-Agent": self.user_agent}

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(search_url, headers=headers)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "lxml")
                    results = soup.select("div.result")
                    for r in results:
                        a = r.select_one("a.result__url")
                        title_elem = r.select_one("a.result__title")
                        snippet_elem = r.select_one("a.result__snippet")

                        if not a:
                            continue

                        raw_url = a.get("href", "").strip()
                        if raw_url.startswith("//"):
                            raw_url = f"https:{raw_url}"
                        elif raw_url.startswith("/"):
                            parsed_q = urllib.parse.parse_qs(urllib.parse.urlparse(raw_url).query)
                            if "uddg" in parsed_q:
                                raw_url = parsed_q["uddg"][0]

                        if not raw_url.startswith(("http://", "https://")):
                            continue

                        url_type = URLClassifier.classify(raw_url)
                        if url_type in ["article", "marketplace"]:
                            continue

                        domain = Normalizer.normalize_domain(raw_url)
                        if not domain or domain in seen_domains:
                            continue

                        seen_domains.add(domain)
                        title = title_elem.get_text(strip=True) if title_elem else domain.split(".")[0].capitalize()
                        snippet = snippet_elem.get_text(strip=True) if snippet_elem else None

                        candidates.append(
                            DiscoveryCandidate(
                                job_id=job_id,
                                company_name=Normalizer.clean_company_name(title),
                                domain=domain,
                                website=raw_url,
                                url=raw_url,
                                city=location,
                                category=industry or "Jewellery",
                                source="search",
                                source_url=raw_url,
                                discovered_from=["search"],
                                query_variant=search_query,
                                metadata={"snippet": snippet, "url_type": url_type},
                            )
                        )
                        if len(candidates) >= limit:
                            break
        except Exception:
            pass

        return candidates
