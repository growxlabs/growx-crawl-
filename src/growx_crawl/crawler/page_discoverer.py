import urllib.parse
from typing import List, Set
from bs4 import BeautifulSoup
from growx_crawl.models.target import CrawlTarget
from growx_crawl.normalization.normalizer import Normalizer


class PageDiscoverer:
    HIGH_VALUE_PATHS = [
        "/about",
        "/about-us",
        "/contact",
        "/contact-us",
        "/team",
        "/leadership",
        "/management",
        "/company",
        "/our-story",
    ]

    @classmethod
    def generate_seed_subpages(
        self, base_target: CrawlTarget, max_depth: int = 2
    ) -> List[CrawlTarget]:
        if base_target.depth >= max_depth:
            return []

        discovered: List[CrawlTarget] = []
        parsed = urllib.parse.urlparse(base_target.url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        for path in self.HIGH_VALUE_PATHS:
            sub_url = f"{base_url}{path}"
            discovered.append(
                CrawlTarget(
                    job_id=base_target.job_id,
                    url=sub_url,
                    domain=base_target.domain,
                    source="page_discoverer",
                    depth=base_target.depth + 1,
                )
            )
        return discovered

    @classmethod
    def extract_internal_links(
        self,
        base_target: CrawlTarget,
        html_content: str,
        max_depth: int = 2,
        max_links: int = 10,
    ) -> List[CrawlTarget]:
        if base_target.depth >= max_depth or not html_content:
            return []

        discovered: List[CrawlTarget] = []
        seen_urls: Set[str] = set()
        soup = BeautifulSoup(html_content, "lxml")

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue

            full_url = urllib.parse.urljoin(base_target.url, href)
            # Remove query params & fragments for canonical link
            parsed = urllib.parse.urlparse(full_url)
            clean_url = urllib.parse.urlunparse(
                (parsed.scheme, parsed.netloc, parsed.path, "", "", "")
            )

            link_domain = Normalizer.normalize_domain(clean_url)
            if link_domain != base_target.domain:
                continue

            # Prioritize links with keywords in path
            path_lower = parsed.path.lower()
            if any(kw in path_lower for kw in ["about", "contact", "team", "leader", "people", "management", "company", "store"]):
                if clean_url not in seen_urls:
                    seen_urls.add(clean_url)
                    discovered.append(
                        CrawlTarget(
                            job_id=base_target.job_id,
                            url=clean_url,
                            domain=base_target.domain,
                            source="link_extractor",
                            depth=base_target.depth + 1,
                        )
                    )
                    if len(discovered) >= max_links:
                        break

        return discovered
