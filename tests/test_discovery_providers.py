import asyncio
from growx_crawl.discovery import ProviderRegistry
from growx_crawl.models import DiscoveryCandidate


def test_provider_registry_health():
    registry = ProviderRegistry()
    health = registry.get_provider_health()
    assert len(health) >= 3
    provider_names = {h["name"] for h in health}
    assert "MapsProvider" in provider_names
    assert "SearchProvider" in provider_names


def test_source_deduplication():
    registry = ProviderRegistry()
    c1 = DiscoveryCandidate(
        job_id="j1",
        company_name="Royal Jewellers",
        domain="royaljewellers.com",
        website="https://royaljewellers.com",
        phone="+914023456789",
        discovered_from=["maps"],
    )
    c2 = DiscoveryCandidate(
        job_id="j1",
        company_name="Royal Jewellers Pvt Ltd",
        domain="royaljewellers.com",
        website="https://royaljewellers.com",
        discovered_from=["search"],
    )

    deduped = registry._deduplicate_candidates([c1, c2], limit=10)
    assert len(deduped) == 1
    assert "maps" in deduped[0].discovered_from
    assert "search" in deduped[0].discovered_from
