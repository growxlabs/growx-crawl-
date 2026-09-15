from typing import Any, Dict
from growx_crawl.models.lead import Company


class LeadEnricher:
    @classmethod
    def enrich(cls, company: Company) -> Dict[str, Any]:
        """
        Enriches company data with completeness indicators.
        Strictly distinguishes OBSERVED FACTS from INFERRED metadata.
        """
        has_website = bool(company.website and company.website.startswith("http"))
        has_email = len(company.emails) > 0
        has_phone = len(company.phones) > 0
        has_instagram = any(s.platform == "instagram" for s in company.social_profiles)
        has_linkedin = any(s.platform == "linkedin" for s in company.social_profiles)
        has_contacts = len(company.contacts) > 0
        has_description = bool(company.description and len(company.description) >= 15)

        completeness_facts = {
            "has_website": has_website,
            "has_email": has_email,
            "has_phone": has_phone,
            "has_instagram": has_instagram,
            "has_linkedin": has_linkedin,
            "has_contacts": has_contacts,
            "has_description": has_description,
            "email_count": len(company.emails),
            "phone_count": len(company.phones),
            "social_count": len(company.social_profiles),
        }

        # Inferred / Derived quality score
        fact_weights = [has_website, has_email, has_phone, has_instagram, has_contacts, has_description]
        completeness_pct = int((sum(fact_weights) / len(fact_weights)) * 100)

        return {
            "facts": completeness_facts,
            "inferred": {
                "completeness_score_pct": completeness_pct,
                "data_tier": "Tier 1" if completeness_pct >= 70 else ("Tier 2" if completeness_pct >= 40 else "Tier 3"),
            },
        }
