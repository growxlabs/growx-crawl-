import json
from typing import Any, Dict, List
from bs4 import BeautifulSoup
from growx_crawl.models.page import FetchedPage
from growx_crawl.normalization.normalizer import Normalizer


class SchemaOrgExtractor:
    @classmethod
    def extract_structured_data(cls, page: FetchedPage) -> Dict[str, Any]:
        if not page.html_content:
            return {}

        soup = BeautifulSoup(page.html_content, "lxml")
        facts: Dict[str, Any] = {
            "name": None,
            "telephone": None,
            "email": None,
            "address": None,
            "same_as": [],
            "founders": [],
            "brand": None,
        }

        # 1. JSON-LD Scripts
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "{}")
                if isinstance(data, list):
                    for item in data:
                        cls._process_json_ld_item(item, facts)
                elif isinstance(data, dict):
                    if "@graph" in data and isinstance(data["@graph"], list):
                        for item in data["@graph"]:
                            cls._process_json_ld_item(item, facts)
                    else:
                        cls._process_json_ld_item(data, facts)
            except Exception:
                pass

        return facts

    @classmethod
    def _process_json_ld_item(cls, item: dict, facts: dict):
        if not isinstance(item, dict):
            return
        t = item.get("@type", "")
        if t in ["Organization", "LocalBusiness", "Corporation", "JewelryStore", "Store", "Place"]:
            if item.get("name") and not facts["name"]:
                facts["name"] = Normalizer.clean_company_name(item["name"])
            if item.get("telephone") and not facts["telephone"]:
                facts["telephone"] = item["telephone"]
            if item.get("email") and not facts["email"]:
                facts["email"] = item["email"]
            if item.get("brand") and not facts["brand"]:
                b = item["brand"]
                facts["brand"] = b.get("name") if isinstance(b, dict) else str(b)

            same_as = item.get("sameAs")
            if same_as:
                if isinstance(same_as, str):
                    facts["same_as"].append(same_as)
                elif isinstance(same_as, list):
                    facts["same_as"].extend(same_as)

            founder = item.get("founder") or item.get("founders")
            if founder:
                if isinstance(founder, str):
                    facts["founders"].append(founder)
                elif isinstance(founder, dict) and founder.get("name"):
                    facts["founders"].append(founder["name"])
                elif isinstance(founder, list):
                    for f in founder:
                        if isinstance(f, str):
                            facts["founders"].append(f)
                        elif isinstance(f, dict) and f.get("name"):
                            facts["founders"].append(f["name"])

            addr = item.get("address")
            if addr and not facts["address"]:
                if isinstance(addr, str):
                    facts["address"] = addr
                elif isinstance(addr, dict):
                    parts = [
                        addr.get("streetAddress"),
                        addr.get("addressLocality"),
                        addr.get("addressRegion"),
                        addr.get("postalCode"),
                        addr.get("addressCountry"),
                    ]
                    clean_parts = [str(p).strip() for p in parts if p]
                    facts["address"] = ", ".join(clean_parts)
