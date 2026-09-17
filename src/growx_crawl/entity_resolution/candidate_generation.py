"""
GrowX Candidate Generation & Blocking Rules.
Generates candidate pairs using high-recall blocking keys to avoid O(N^2) pairwise comparisons.
"""

from typing import Dict, List, Set, Tuple
from growx_crawl.entity_resolution.models import BlockingKey
from growx_crawl.normalization.company import normalize_company_name_key
from growx_crawl.normalization.domain import get_registrable_domain


def generate_company_blocking_keys(entity_id: str, name: str, domain: str = "") -> List[BlockingKey]:
    """Generates standard blocking keys for a company."""
    keys = []
    if domain:
        reg_domain = get_registrable_domain(domain)
        if reg_domain:
            keys.append(BlockingKey(key_type="domain_root", key_value=reg_domain, entity_id=entity_id, entity_type="company"))

    if name:
        name_key = normalize_company_name_key(name)
        if len(name_key) >= 4:
            # First 4 chars prefix blocking
            keys.append(BlockingKey(key_type="name_prefix_4", key_value=name_key[:4], entity_id=entity_id, entity_type="company"))
            keys.append(BlockingKey(key_type="name_full_key", key_value=name_key, entity_id=entity_id, entity_type="company"))

    return keys


def find_candidate_pairs(blocking_keys: List[BlockingKey]) -> Set[Tuple[str, str]]:
    """Groups entity IDs sharing at least one blocking key and generates candidate pairs."""
    inverted_index: Dict[str, List[str]] = {}
    for bk in blocking_keys:
        compound_key = f"{bk.key_type}:{bk.key_value}"
        inverted_index.setdefault(compound_key, []).append(bk.entity_id)

    pairs: Set[Tuple[str, str]] = set()
    for entity_ids in inverted_index.values():
        unique_ids = sorted(list(set(entity_ids)))
        for i in range(len(unique_ids)):
            for j in range(i + 1, len(unique_ids)):
                pairs.add((unique_ids[i], unique_ids[j]))

    return pairs
