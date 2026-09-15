from typing import Any, Dict, List, Optional
from growx_crawl.discovery.base import DiscoveryProvider
from growx_crawl.discovery.directory import DirectoryProvider
from growx_crawl.discovery.expander import QueryExpander
from growx_crawl.discovery.maps import MapsProvider
from growx_crawl.discovery.search import SearchProvider
from growx_crawl.discovery.seed_file import SeedFileDiscoveryProvider
from growx_crawl.models.discovery import DiscoveryCandidate
from growx_crawl.normalization.normalizer import Normalizer


class ProviderRegistry:
    def __init__(self, seed_file: Optional[str] = None):
        self.maps_provider = MapsProvider()
        self.search_provider = SearchProvider()
        self.directory_provider = DirectoryProvider()
        self.seed_provider = SeedFileDiscoveryProvider(seed_file) if seed_file else None

    def get_provider_health(self) -> List[Dict[str, Any]]:
        health = [
            self.maps_provider.health_check(),
            self.search_provider.health_check(),
            self.directory_provider.health_check(),
        ]
        if self.seed_provider:
            health.append(self.seed_provider.health_check())
        return health

    async def discover_candidates(
        self,
        query: Optional[str] = None,
        location: Optional[str] = None,
        industry: Optional[str] = None,
        provider_type: str = "auto",
        limit: int = 50,
        job_id: str = "job_default",
        seed_file: Optional[str] = None,
    ) -> List[DiscoveryCandidate]:
        if seed_file and not self.seed_provider:
            self.seed_provider = SeedFileDiscoveryProvider(seed_file)

        # 1. Expand query variants
        query_variants = QueryExpander.expand_query(
            query=query, industry=industry, location=location, max_variants=5
        )

        raw_candidates: List[DiscoveryCandidate] = []

        # 2. Determine target providers
        target_providers: List[DiscoveryProvider] = []
        mode = provider_type.lower()

        if mode == "seeds" and self.seed_provider:
            target_providers = [self.seed_provider]
        elif mode == "maps":
            target_providers = [self.maps_provider]
        elif mode == "search":
            target_providers = [self.search_provider]
        elif mode == "directory":
            target_providers = [self.directory_provider]
        else:
            # Auto mode: combine seed (if available) + maps + search
            if self.seed_provider:
                target_providers.append(self.seed_provider)
            target_providers.extend([self.maps_provider, self.search_provider])

        # 3. Collect candidates across providers and query variants
        for provider in target_providers:
            for variant in query_variants:
                if len(raw_candidates) >= limit * 2:
                    break
                try:
                    res = await provider.discover(
                        query=variant,
                        job_id=job_id,
                        location=location,
                        industry=industry,
                        limit=limit,
                    )
                    raw_candidates.extend(res)
                except Exception:
                    pass

        # 4. Source Deduplication & Provenance Merging
        return self._deduplicate_candidates(raw_candidates, limit=limit)

    def _deduplicate_candidates(
        self, candidates: List[DiscoveryCandidate], limit: int
    ) -> List[DiscoveryCandidate]:
        unique_map: Dict[str, DiscoveryCandidate] = {}

        for cand in candidates:
            # Dedupe key precedence: domain > phone > external_id > name_city
            key = None
            if cand.domain:
                key = f"dom:{cand.domain}"
            elif cand.phone:
                key = f"phn:{Normalizer.normalize_phone(cand.phone)}"
            elif cand.external_id:
                key = f"ext:{cand.external_id}"
            elif cand.company_name and cand.city:
                name_key = Normalizer.normalize_company_name_key(cand.company_name)
                key = f"name_city:{name_key}_{cand.city.lower()}"

            if not key:
                key = f"cand_{len(unique_map)}"

            if key in unique_map:
                existing = unique_map[key]
                # Merge provenance
                for src in cand.discovered_from:
                    if src not in existing.discovered_from:
                        existing.discovered_from.append(src)
                # Enrich missing website/phone/address
                if not existing.website and cand.website:
                    existing.website = cand.website
                    existing.url = cand.website
                    existing.domain = cand.domain
                    existing.website_missing = False
                if not existing.phone and cand.phone:
                    existing.phone = cand.phone
                if not existing.address and cand.address:
                    existing.address = cand.address
            else:
                unique_map[key] = cand

        results = list(unique_map.values())
        return results[:limit]
