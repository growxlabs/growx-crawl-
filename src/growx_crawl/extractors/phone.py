import re
from typing import List
from bs4 import BeautifulSoup
from growx_crawl.extractors.base import BaseExtractor
from growx_crawl.models.lead import Phone
from growx_crawl.models.page import FetchedPage
from growx_crawl.normalization.normalizer import Normalizer


class PhoneExtractor(BaseExtractor):
    # Matches tel links and international/Indian phone formats
    PHONE_REGEX = re.compile(
        r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,5}\)?[-.\s]?\d{3,5}[-.\s]?\d{3,5}"
    )

    def extract(self, page: FetchedPage) -> List[Phone]:
        if not page.html_content and not page.text_content:
            return []

        extracted_phones: List[Phone] = []
        seen = set()

        soup = BeautifulSoup(page.html_content or "", "lxml")

        # 1. Tel links
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.lower().startswith("tel:"):
                raw_phone = href.split(":", 1)[1].strip()
                norm_phone = Normalizer.normalize_phone(raw_phone)
                if norm_phone and norm_phone not in seen and len(norm_phone) >= 7:
                    seen.add(norm_phone)
                    extracted_phones.append(
                        Phone(
                            company_id="",
                            phone=raw_phone,
                            normalized_phone=norm_phone,
                            raw_phone=raw_phone,
                            country_code=Normalizer.extract_country_code(raw_phone),
                            source_url=page.url,
                        )
                    )

        # 2. Text regex
        text = page.text_content or ""
        for match in self.PHONE_REGEX.findall(text):
            match_str = match.strip()
            norm_phone = Normalizer.normalize_phone(match_str)
            if norm_phone and norm_phone not in seen and 7 <= len(norm_phone) <= 15:
                seen.add(norm_phone)
                extracted_phones.append(
                    Phone(
                        company_id="",
                        phone=match_str,
                        normalized_phone=norm_phone,
                        raw_phone=match_str,
                        country_code=Normalizer.extract_country_code(match_str),
                        source_url=page.url,
                    )
                )

        return extracted_phones
