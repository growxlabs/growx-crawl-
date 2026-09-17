"""
GrowX Person Matcher.
Executes pairwise comparison and scoring between two person records.
"""

from typing import Any, Dict, Tuple
from growx_crawl.entity_resolution.explain import build_explanation
from growx_crawl.entity_resolution.models import MatchExplanation
from growx_crawl.entity_resolution.person.features import extract_person_features
from growx_crawl.entity_resolution.person.rules import evaluate_person_rules


class PersonMatcher:
    """Matches two person entities using rule-based feature comparison."""

    def match(self, p1: Dict[str, Any], p2: Dict[str, Any]) -> Tuple[float, MatchExplanation]:
        f1 = extract_person_features(p1)
        f2 = extract_person_features(p2)

        signals = evaluate_person_rules(f1, f2)
        explanation = build_explanation(signals)
        return explanation.confidence, explanation
