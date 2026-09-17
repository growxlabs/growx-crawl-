"""
GrowX Entity Resolution Scoring Metrics.
Provides string and token similarity calculations.
"""

from difflib import SequenceMatcher
from typing import Set


def jaro_winkler_similarity(s1: str, s2: str) -> float:
    """Calculates sequence similarity ratio between two strings [0.0, 1.0]."""
    if not s1 or not s2:
        return 0.0
    s1, s2 = s1.lower().strip(), s2.lower().strip()
    if s1 == s2:
        return 1.0
    return SequenceMatcher(None, s1, s2).ratio()


def token_overlap_score(tokens1: Set[str], tokens2: Set[str]) -> float:
    """Calculates Jaccard overlap between two token sets."""
    if not tokens1 or not tokens2:
        return 0.0
    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    return len(intersection) / len(union) if union else 0.0
