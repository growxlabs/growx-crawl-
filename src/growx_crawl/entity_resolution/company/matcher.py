"""
GrowX Company Matcher.
Executes pairwise comparison and scoring between two company records.
"""

from typing import Any, Dict, Optional, Tuple
from growx_crawl.entity_resolution.company.features import extract_company_features
from growx_crawl.entity_resolution.company.rules import evaluate_company_rules
from growx_crawl.entity_resolution.explain import build_explanation
from growx_crawl.entity_resolution.models import MatchExplanation


class CompanyMatcher:
    """Matches two company entities using rule-based feature comparison."""

    def match(self, c1: Dict[str, Any], c2: Dict[str, Any]) -> Tuple[float, MatchExplanation]:
        f1 = extract_company_features(c1)
        f2 = extract_company_features(c2)

        signals = evaluate_company_rules(f1, f2)
        explanation = build_explanation(signals)
        return explanation.confidence, explanation
