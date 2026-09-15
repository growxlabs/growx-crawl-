import re
from typing import List
from bs4 import BeautifulSoup
from growx_crawl.extractors.base import BaseExtractor
from growx_crawl.models.lead import Email
from growx_crawl.models.page import FetchedPage
from growx_crawl.normalization.normalizer import Normalizer


class EmailExtractor(BaseExtractor):
    GENERIC_PREFIXES = {"info", "sales", "contact", "hello", "support", "admin", "enquiry", "office", "careers", "help"}
    IGNORED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".js", ".css", ".wixpress.com"}

    EMAIL_REGEX = re.compile(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", re.I
    )

    def extract(self, page: FetchedPage) -> List[Email]:
        if not page.html_content and not page.text_content:
            return []

        extracted_emails: List[Email] = []
        seen = set()

        soup = BeautifulSoup(page.html_content or "", "lxml")

        # 1. Mailto links
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.lower().startswith("mailto:"):
                raw_email = href.split(":", 1)[1].split("?")[0].strip()
                norm_email = Normalizer.normalize_email(raw_email)
                if norm_email and norm_email not in seen and self._is_valid_email(norm_email):
                    seen.add(norm_email)
                    prefix = norm_email.split("@")[0].lower()
                    extracted_emails.append(
                        Email(
                            company_id="",
                            email=raw_email,
                            normalized_email=norm_email,
                            is_generic=prefix in self.GENERIC_PREFIXES,
                            source_url=page.url,
                        )
                    )

        # 2. Text regex matching
        text = (page.text_content or "") + " " + (page.html_content or "")
        for match in self.EMAIL_REGEX.findall(text):
            norm_email = Normalizer.normalize_email(match)
            if norm_email and norm_email not in seen and self._is_valid_email(norm_email):
                seen.add(norm_email)
                prefix = norm_email.split("@")[0].lower()
                extracted_emails.append(
                    Email(
                        company_id="",
                        email=match,
                        normalized_email=norm_email,
                        is_generic=prefix in self.GENERIC_PREFIXES,
                        source_url=page.url,
                    )
                )

        return extracted_emails

    def _is_valid_email(self, email: str) -> bool:
        if any(email.lower().endswith(ext) for ext in self.IGNORED_EXTENSIONS):
            return False
        if "sentry" in email or "example" in email or "domain.com" in email:
            return False
        return True
