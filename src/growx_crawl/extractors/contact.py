import re
from typing import List
from bs4 import BeautifulSoup
from growx_crawl.extractors.base import BaseExtractor
from growx_crawl.models.lead import Contact
from growx_crawl.models.page import FetchedPage


class ContactExtractor(BaseExtractor):
    ROLE_KEYWORDS = [
        "Founder", "Co-Founder", "CEO", "Managing Director", "MD", "Director",
        "Owner", "Partner", "President", "Vice President", "General Manager",
        "Store Manager", "Head of Sales", "Operations Manager"
    ]

    def extract(self, page: FetchedPage) -> List[Contact]:
        if not page.html_content:
            return []

        contacts: List[Contact] = []
        soup = BeautifulSoup(page.html_content, "lxml")

        # Search for team member cards or any element containing role keywords
        cards = soup.find_all(class_=re.compile(r"team|leadership|member|executive|profile|person", re.I))
        if not cards:
            cards = soup.find_all(["div", "section", "article"])

        for card in cards[:20]:
            text = card.get_text(separator=" | ", strip=True)
            for role in self.ROLE_KEYWORDS:
                if role.lower() in text.lower():
                    # Look for heading or name paragraph in the card
                    name_elem = card.find(["h1", "h2", "h3", "h4", "h5", "strong", "b"])
                    name = name_elem.get_text(strip=True) if name_elem else None

                    if not name:
                        parts = [p.strip() for p in text.split("|") if p.strip()]
                        for part in parts:
                            if 2 <= len(part.split()) <= 3 and not any(kw in part for kw in ["About", "Contact", "Team", role]):
                                name = part
                                break

                    if name and len(name) <= 50:
                        tier = "Tier 1" if any(k in role for k in ["Owner", "Founder", "CEO", "Managing Director", "MD", "Proprietor"]) else ("Tier 2" if any(k in role for k in ["Director", "Head", "COO"]) else "Tier 3")
                        contacts.append(
                            Contact(
                                company_id="",
                                job_id=page.job_id,
                                name=name,
                                title=role,
                                decision_maker_tier=tier,
                                source_url=page.url,
                            )
                        )
                        break
        return contacts
