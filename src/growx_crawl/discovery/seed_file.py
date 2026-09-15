import csv
from pathlib import Path
from typing import Any, Dict, List, Optional
from growx_crawl.discovery.base import DiscoveryProvider
from growx_crawl.models.discovery import DiscoveryCandidate
from growx_crawl.normalization.normalizer import Normalizer


class SeedFileDiscoveryProvider(DiscoveryProvider):
    def __init__(self, seed_file_path: str):
        self.seed_file_path = Path(seed_file_path)

    def health_check(self) -> Dict[str, Any]:
        return {
            "name": "SeedFileDiscoveryProvider",
            "status": "available" if self.seed_file_path.exists() else "file_not_found",
            "path": str(self.seed_file_path),
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
        if not self.seed_file_path.exists():
            raise FileNotFoundError(f"Seed file not found: {self.seed_file_path}")

        candidates: List[DiscoveryCandidate] = []
        seen_domains = set()

        if self.seed_file_path.suffix.lower() == ".csv":
            with open(self.seed_file_path, "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    url = row.get("url") or row.get("website") or row.get("link")
                    company_name = row.get("company_name") or row.get("name")
                    source = row.get("source") or "seed_file"

                    if not url:
                        url = list(row.values())[0] if row.values() else None
                    if not url:
                        continue

                    url = url.strip()
                    if not url.startswith(("http://", "https://")):
                        url = f"https://{url}"

                    domain = Normalizer.normalize_domain(url)
                    if not domain or domain in seen_domains:
                        continue
                    seen_domains.add(domain)

                    candidates.append(
                        DiscoveryCandidate(
                            job_id=job_id,
                            company_name=Normalizer.clean_company_name(company_name or domain.split(".")[0].capitalize()),
                            domain=domain,
                            website=url,
                            url=url,
                            city=location,
                            category=industry or "Jewellery",
                            source=source,
                            source_url=url,
                            discovered_from=["seed_file"],
                            query_variant=query,
                        )
                    )
                    if len(candidates) >= limit:
                        break
        else:
            with open(self.seed_file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    url = line.strip()
                    if not url or url.startswith("#"):
                        continue
                    if not url.startswith(("http://", "https://")):
                        url = f"https://{url}"

                    domain = Normalizer.normalize_domain(url)
                    if not domain or domain in seen_domains:
                        continue
                    seen_domains.add(domain)

                    candidates.append(
                        DiscoveryCandidate(
                            job_id=job_id,
                            company_name=Normalizer.clean_company_name(domain.split(".")[0].capitalize()),
                            domain=domain,
                            website=url,
                            url=url,
                            city=location,
                            category=industry or "Jewellery",
                            source="seed_file",
                            source_url=url,
                            discovered_from=["seed_file"],
                            query_variant=query,
                        )
                    )
                    if len(candidates) >= limit:
                        break

        return candidates
