"""
GrowX Company Entity Resolution Package.
"""

from growx_crawl.entity_resolution.company.features import extract_company_features
from growx_crawl.entity_resolution.company.rules import evaluate_company_rules
from growx_crawl.entity_resolution.company.matcher import CompanyMatcher

__all__ = [
    "extract_company_features",
    "evaluate_company_rules",
    "CompanyMatcher",
]
