"""
GrowX Company Entity Resolution Features.
Extracts match features from company domain models.
"""

from typing import Any, Dict, List, Set
from growx_crawl.normalization.company import normalize_company_name, normalize_company_name_key
from growx_crawl.normalization.domain import get_registrable_domain, normalize_domain


def extract_company_features(company_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts standardized comparison features from a company record dictionary."""
    name = company_data.get("name") or ""
    domain = company_data.get("domain") or ""
    emails = company_data.get("emails") or []
    phones = company_data.get("phones") or []
    socials = company_data.get("social_profiles") or []
    city = (company_data.get("city") or "").strip().lower()

    norm_domain = normalize_domain(domain)
    reg_domain = get_registrable_domain(domain)

    # Normalize email strings
    email_set = set()
    for e in emails:
        val = e if isinstance(e, str) else getattr(e, "normalized_email", "") or getattr(e, "email", "")
        if val:
            email_set.add(val.strip().lower())

    # Normalize phone strings
    phone_set = set()
    for p in phones:
        val = p if isinstance(p, str) else getattr(p, "normalized_phone", "") or getattr(p, "phone", "")
        if val:
            phone_set.add(val.strip())

    # Normalize social URL strings
    social_set = set()
    for s in socials:
        val = s if isinstance(s, str) else getattr(s, "normalized_url", "") or getattr(s, "url", "")
        if val:
            social_set.add(val.strip().lower().rstrip("/"))

    return {
        "raw_name": name,
        "normalized_name": normalize_company_name(name),
        "name_key": normalize_company_name_key(name),
        "domain": norm_domain,
        "registrable_domain": reg_domain,
        "emails": email_set,
        "phones": phone_set,
        "social_profiles": social_set,
        "city": city,
    }
