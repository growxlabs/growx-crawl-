"""
GrowX Entity Resolution Conflicts.
Detects hard discrepancies between entity pairs that should prevent automated merges.
"""

from typing import Any, Dict, List


def detect_company_conflicts(c1: Dict[str, Any], c2: Dict[str, Any]) -> List[str]:
    """Detects conflicting hard attributes (e.g. conflicting distinct registered domains or different countries)."""
    conflicts = []
    d1 = c1.get("registrable_domain")
    d2 = c2.get("registrable_domain")
    if d1 and d2 and d1.lower() != d2.lower():
        conflicts.append(f"conflicting_registrable_domain: '{d1}' vs '{d2}'")

    country1 = c1.get("country_code")
    country2 = c2.get("country_code")
    if country1 and country2 and country1.upper() != country2.upper():
        conflicts.append(f"conflicting_country: '{country1}' vs '{country2}'")

    return conflicts
