"""
GrowX Person Entity Resolution Features.
"""

from typing import Any, Dict
from growx_crawl.normalization.person import clean_person_name, normalize_person_name, split_person_name


def extract_person_features(person_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts comparison features for a person record."""
    name = person_data.get("name") or ""
    email = (person_data.get("email") or "").strip().lower()
    company_id = person_data.get("company_id") or ""
    linkedin = (person_data.get("linkedin_url") or "").strip().lower().rstrip("/")

    norm_name = normalize_person_name(name)
    first_name, last_name = split_person_name(name)

    return {
        "raw_name": name,
        "clean_name": clean_person_name(name),
        "normalized_name": norm_name,
        "first_name": first_name.lower(),
        "last_name": last_name.lower(),
        "email": email,
        "company_id": company_id,
        "linkedin_url": linkedin,
    }
