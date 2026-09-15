import re
from typing import List
from bs4 import BeautifulSoup
from growx_crawl.extractors.base import BaseExtractor
from growx_crawl.models.lead import SocialProfile
from growx_crawl.models.page import FetchedPage
from growx_crawl.normalization.normalizer import Normalizer


class SocialExtractor(BaseExtractor):
    PLATFORMS = {
        "instagram": re.compile(r"(?:https?://)?(?:www\.)?instagram\.com/([a-zA-Z0-9._]+)/?", re.I),
        "linkedin": re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/(?:company|in)/([a-zA-Z0-9._-]+)/?", re.I),
        "facebook": re.compile(r"(?:https?://)?(?:www\.)?facebook\.com/([a-zA-Z0-9._-]+)/?", re.I),
        "youtube": re.compile(r"(?:https?://)?(?:www\.)?youtube\.com/(?:c/|channel/|user/|@)?([a-zA-Z0-9._-]+)/?", re.I),
        "whatsapp": re.compile(r"(?:https?://)?(?:api|web|chat)\.whatsapp\.com/send\?phone=([0-9]+)|wa\.me/([0-9]+)", re.I),
    }

    def extract(self, page: FetchedPage) -> List[SocialProfile]:
        if not page.html_content:
            return []

        extracted_socials: List[SocialProfile] = []
        seen = set()

        soup = BeautifulSoup(page.html_content, "lxml")

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            for platform, pattern in self.PLATFORMS.items():
                match = pattern.search(href)
                if match:
                    norm_url = Normalizer.normalize_url(href)
                    if norm_url not in seen:
                        seen.add(norm_url)
                        handle = match.group(1) or (match.group(2) if len(match.groups()) > 1 else None)
                        extracted_socials.append(
                            SocialProfile(
                                company_id="",
                                platform=platform,
                                url=href,
                                normalized_url=norm_url,
                                handle=handle,
                                source_url=page.url,
                            )
                        )

        return extracted_socials
