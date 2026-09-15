import re
from typing import Any, Dict
from bs4 import BeautifulSoup
from growx_crawl.extractors.base import BaseExtractor
from growx_crawl.models.page import FetchedPage


class AddressExtractor(BaseExtractor):
    INDIAN_CITIES = [
        "Hyderabad", "Secunderabad", "Bangalore", "Bengaluru", "Mumbai", "Delhi",
        "New Delhi", "Chennai", "Kolkata", "Ahmedabad", "Pune", "Jaipur", "Surat",
        "Kochi", "Coimbatore", "Visakhapatnam", "Vijayawada", "Lucknow"
    ]

    INDIAN_STATES = [
        "Telangana", "Andhra Pradesh", "Karnataka", "Maharashtra", "Tamil Nadu",
        "Gujarat", "Rajasthan", "Delhi", "West Bengal", "Uttar Pradesh", "Kerala"
    ]

    def extract(self, page: FetchedPage) -> Dict[str, Any]:
        text = (page.text_content or "") + " " + (page.html_content or "")
        if not text:
            return {}

        city = self._find_match(text, self.INDIAN_CITIES)
        state = self._find_match(text, self.INDIAN_STATES)
        country = "India" if (city or state or "india" in text.lower()) else "International"

        address_text = self._extract_address_block(page.html_content or "")

        return {
            "address": address_text,
            "city": city,
            "state": state,
            "country": country,
        }

    def _find_match(self, text: str, options: list) -> str:
        for opt in options:
            if re.search(r"\b" + re.escape(opt) + r"\b", text, re.I):
                return opt
        return None

    def _extract_address_block(self, html_content: str) -> str:
        soup = BeautifulSoup(html_content, "lxml")
        addr_elem = soup.find("address") or soup.find(class_=re.compile(r"address|location|contact-info", re.I))
        if addr_elem:
            clean = addr_elem.get_text(separator=", ", strip=True)
            return clean[:250]
        return None
