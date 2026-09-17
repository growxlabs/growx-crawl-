"""
GrowX Person Entity Resolution Package.
"""

from growx_crawl.entity_resolution.person.features import extract_person_features
from growx_crawl.entity_resolution.person.rules import evaluate_person_rules
from growx_crawl.entity_resolution.person.matcher import PersonMatcher

__all__ = [
    "extract_person_features",
    "evaluate_person_rules",
    "PersonMatcher",
]
