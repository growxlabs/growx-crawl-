import os
import urllib.parse
from typing import Any, Dict, List, Optional
import httpx
from growx_crawl.discovery.base import DiscoveryProvider
from growx_crawl.models.discovery import DiscoveryCandidate
from growx_crawl.normalization.normalizer import Normalizer


class MapsProvider(DiscoveryProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("MAPS_API_KEY")

    def health_check(self) -> Dict[str, Any]:
        return {
            "name": "MapsProvider",
            "status": "configured" if self.api_key else "available (OpenStreetMap fallback)",
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

        if self.api_key:
            candidates = await self._discover_google_places(query, job_id, location, limit)
        else:
            candidates = await self._discover_openstreetmap(query, job_id, location, limit)

        return candidates

    async def _discover_openstreetmap(
        self, query: str, job_id: str, location: Optional[str], limit: int
    ) -> List[DiscoveryCandidate]:
        candidates: List[DiscoveryCandidate] = []
        search_str = f"{query} {location or ''}".strip()
        encoded = urllib.parse.quote_plus(search_str)
        url = f"https://nominatim.openstreetmap.org/search?q={encoded}&format=json&addressdetails=1&limit={limit}"
        headers = {"User-Agent": "GrowXCrawl/1.0 (+https://growxlabs.tech)"}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data:
                        display_name = item.get("display_name", "")
                        parts = [p.strip() for p in display_name.split(",")]
                        name = parts[0] if parts else search_str

                        addr_dict = item.get("address", {})
                        city = addr_dict.get("city") or addr_dict.get("town") or addr_dict.get("state_district") or location
                        state = addr_dict.get("state")
                        country = addr_dict.get("country", "India")
                        ext_id = str(item.get("place_id", ""))

                        website = item.get("extratags", {}).get("website") if isinstance(item.get("extratags"), dict) else None
                        phone = item.get("extratags", {}).get("phone") if isinstance(item.get("extratags"), dict) else None
                        domain = Normalizer.normalize_domain(website) if website else None

                        candidates.append(
                            DiscoveryCandidate(
                                job_id=job_id,
                                company_name=Normalizer.clean_company_name(name),
                                domain=domain,
                                website=website,
                                url=website,
                                phone=phone,
                                address=display_name[:200],
                                city=city,
                                state=state,
                                country=country,
                                category=item.get("type", "local_business"),
                                source="maps",
                                source_url=f"https://www.openstreetmap.org/node/{ext_id}" if ext_id else None,
                                external_id=ext_id,
                                discovered_from=["maps"],
                                query_variant=query,
                                website_missing=not bool(website),
                            )
                        )
                        if len(candidates) >= limit:
                            break
        except Exception:
            pass

        return candidates

    async def _discover_google_places(
        self, query: str, job_id: str, location: Optional[str], limit: int
    ) -> List[DiscoveryCandidate]:
        # Google Places API integration if API key is supplied
        candidates: List[DiscoveryCandidate] = []
        # Implement API call if credentials present...
        return candidates
