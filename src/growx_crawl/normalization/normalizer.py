"""
GrowX Normalization Facade.
Maintains 100% backward compatibility for existing callers while delegating
to domain-specific normalization modules.
"""

from typing import Optional
from growx_crawl.normalization.address import normalize_address
from growx_crawl.normalization.company import clean_company_name, normalize_company_name, normalize_company_name_key
from growx_crawl.normalization.domain import get_registrable_domain, normalize_domain, normalize_url
from growx_crawl.normalization.person import clean_person_name, normalize_person_name, split_person_name
from growx_crawl.normalization.phone import extract_country_code, normalize_phone


class Normalizer:
    @classmethod
    def normalize_domain(cls, url_or_domain: str) -> str:
        return normalize_domain(url_or_domain)

    @classmethod
    def normalize_url(cls, url: str) -> str:
        return normalize_url(url)

    @classmethod
    def normalize_email(cls, email: str) -> Optional[str]:
        if not email:
            return None
        clean = email.strip().lower()
        if "@" in clean and len(clean) >= 5:
            return clean
        return None

    @classmethod
    def normalize_phone(cls, phone: str) -> Optional[str]:
        return normalize_phone(phone)

    @classmethod
    def extract_country_code(cls, phone: str) -> Optional[str]:
        return extract_country_code(phone)

    @classmethod
    def clean_company_name(cls, name: str) -> str:
        return clean_company_name(name)

    @classmethod
    def normalize_company_name_key(cls, name: str) -> str:
        return normalize_company_name_key(name)

    @classmethod
    def normalize_person_name(cls, name: str) -> str:
        return normalize_person_name(name)

    @classmethod
    def clean_person_name(cls, name: str) -> str:
        return clean_person_name(name)

    @classmethod
    def normalize_address(cls, address: str) -> str:
        return normalize_address(address)
