"""
GrowX Person Entity Resolution Rules.
"""

from typing import Any, Dict, List
from growx_crawl.entity_resolution.models import MatchSignal
from growx_crawl.entity_resolution.scoring import jaro_winkler_similarity


def evaluate_person_rules(p1: Dict[str, Any], p2: Dict[str, Any]) -> List[MatchSignal]:
    """Evaluates rules between two person feature records."""
    signals: List[MatchSignal] = []

    # Rule 1: Same email
    e1, e2 = p1.get("email"), p2.get("email")
    if e1 and e2 and e1 == e2:
        signals.append(MatchSignal(
            name="same_email",
            weight=1.0,
            score=1.0,
            description=f"Exact email match '{e1}'",
        ))

    # Rule 2: Same LinkedIn URL
    l1, l2 = p1.get("linkedin_url"), p2.get("linkedin_url")
    if l1 and l2 and l1 == l2:
        signals.append(MatchSignal(
            name="same_linkedin_url",
            weight=0.98,
            score=0.98,
            description=f"Exact LinkedIn profile match '{l1}'",
        ))

    # Rule 3: Same company + high name similarity
    c1, c2 = p1.get("company_id"), p2.get("company_id")
    if c1 and c2 and c1 == c2:
        sim = jaro_winkler_similarity(p1.get("normalized_name", ""), p2.get("normalized_name", ""))
        if sim >= 0.90:
            signals.append(MatchSignal(
                name="same_company_and_name",
                weight=0.85,
                score=0.85,
                description=f"High name match ({sim:.2f}) at same company ID '{c1}'",
            ))

    return signals
