"""
GrowX Company Entity Resolution Rules.
Defines weighted match signals for company comparisons.
"""

from typing import Any, Dict, List
from growx_crawl.entity_resolution.models import MatchSignal
from growx_crawl.entity_resolution.scoring import jaro_winkler_similarity


def evaluate_company_rules(f1: Dict[str, Any], f2: Dict[str, Any]) -> List[MatchSignal]:
    """Evaluates rules between two extracted company feature dictionaries."""
    signals: List[MatchSignal] = []

    # Rule 1: Same domain
    d1, d2 = f1.get("domain"), f2.get("domain")
    if d1 and d2 and d1 == d2:
        signals.append(MatchSignal(
            name="same_domain",
            weight=1.0,
            score=1.0,
            description=f"Exact domain match '{d1}'",
        ))

    # Rule 2: Shared emails
    emails1, emails2 = f1.get("emails", set()), f2.get("emails", set())
    shared_emails = emails1.intersection(emails2)
    if shared_emails:
        signals.append(MatchSignal(
            name="same_normalized_email",
            weight=0.95,
            score=0.95,
            description=f"Shared email: {list(shared_emails)[0]}",
        ))

    # Rule 3: Shared phones
    phones1, phones2 = f1.get("phones", set()), f2.get("phones", set())
    shared_phones = phones1.intersection(phones2)
    if shared_phones:
        signals.append(MatchSignal(
            name="same_normalized_phone",
            weight=0.95,
            score=0.95,
            description=f"Shared phone: {list(shared_phones)[0]}",
        ))

    # Rule 4: Shared social profile
    soc1, soc2 = f1.get("social_profiles", set()), f2.get("social_profiles", set())
    shared_soc = soc1.intersection(soc2)
    if shared_soc:
        signals.append(MatchSignal(
            name="same_social_url",
            weight=0.90,
            score=0.90,
            description=f"Shared social handle/URL: {list(shared_soc)[0]}",
        ))

    # Rule 5: Same name key and city
    k1, k2 = f1.get("name_key"), f2.get("name_key")
    c1, c2 = f1.get("city"), f2.get("city")
    if k1 and k2 and k1 == k2:
        if c1 and c2 and c1 == c2:
            signals.append(MatchSignal(
                name="same_name_and_city",
                weight=0.75,
                score=0.75,
                description=f"Identical name key '{k1}' in same city '{c1}'",
            ))
        else:
            sim = jaro_winkler_similarity(f1.get("raw_name", ""), f2.get("raw_name", ""))
            if sim >= 0.95:
                signals.append(MatchSignal(
                    name="high_name_similarity",
                    weight=0.70,
                    score=0.70,
                    description=f"High name string similarity ({sim:.2f})",
                ))

    return signals
