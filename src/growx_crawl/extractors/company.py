import json
import re
from typing import Any, Dict, Optional
from bs4 import BeautifulSoup
from growx_crawl.extractors.base import BaseExtractor
from growx_crawl.models.page import FetchedPage
from growx_crawl.normalization.normalizer import Normalizer


class CompanyExtractor(BaseExtractor):
    def extract(self, page: FetchedPage) -> Dict[str, Any]:
        if not page.html_content:
            return {}

        soup = BeautifulSoup(page.html_content, "lxml")
        company_name = self._extract_name(soup, page)
        description = self._extract_description(soup)
        industry = self._extract_industry(soup, page)

        domain = Normalizer.normalize_domain(page.url)

        return {
            "name": company_name or Normalizer.clean_company_name(domain.split(".")[0].capitalize()),
            "domain": domain,
            "website": page.url,
            "description": description,
            "industry": industry,
            "source_url": page.url,
        }

    def _extract_name(self, soup: BeautifulSoup, page: FetchedPage) -> Optional[str]:
        # 1. JSON-LD Schema.org
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "{}")
                if isinstance(data, list):
                    data = data[0] if data else {}
                if isinstance(data, dict):
                    t = data.get("@type", "")
                    if t in ["Organization", "LocalBusiness", "Corporation", "JewelryStore", "Store"]:
                        name = data.get("name")
                        if name:
                            return Normalizer.clean_company_name(name)
            except Exception:
                pass

        # 2. og:site_name meta tag
        meta_site = soup.find("meta", property="og:site_name")
        if meta_site and meta_site.get("content"):
            return Normalizer.clean_company_name(meta_site["content"])

        # 3. Logo img alt tag
        logo = soup.find("img", class_=re.compile(r"logo", re.I)) or soup.find("img", alt=re.compile(r"logo|jewel", re.I))
        if logo and logo.get("alt"):
            alt_text = logo["alt"].replace("Logo", "").replace("logo", "").strip()
            if len(alt_text) > 2:
                return Normalizer.clean_company_name(alt_text)

        # 4. Copyright text in footer
        footer = soup.find("footer")
        if footer:
            text = footer.get_text()
            match = re.search(r"©\s*(?:\d{4})?\s*([A-Za-z0-9\s&,.'-]+?)(?:\.|All\s+Rights|\s*-\s*|$)", text, re.I)
            if match:
                cp = match.group(1).strip()
                if 3 <= len(cp) <= 50:
                    return Normalizer.clean_company_name(cp)

        # 5. Page Title tag
        if page.title:
            parts = re.split(r"[|\-–—:]", page.title)
            if parts:
                candidate = parts[0].strip()
                if 2 <= len(candidate) <= 60:
                    return Normalizer.clean_company_name(candidate)

        return None

    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        meta_desc = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", property="og:description")
        if meta_desc and meta_desc.get("content"):
            desc = meta_desc["content"].strip()
            return desc[:500]
        return None

    def _extract_industry(self, soup: BeautifulSoup, page: FetchedPage) -> Optional[str]:
        text_lower = (page.text_content or "").lower() + " " + (page.title or "").lower()
        if any(w in text_lower for w in ["jewel", "gold", "diamond", "gemstone", "ornament"]):
            return "Jewellery"
        if any(w in text_lower for w in ["manufactur", "factory", "textile"]):
            return "Manufacturing"
        if any(w in text_lower for w in ["tech", "software", "solution", "digital"]):
            return "Technology"
        return "General"
