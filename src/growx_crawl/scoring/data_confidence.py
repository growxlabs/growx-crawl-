"""
GrowX Data Confidence Scorer.
Evaluates data completeness, verified presence, and attribute density independently.
Score range: 0.0 - 100.0
"""

from typing import Any, Dict, List, Tuple


def calculate_data_confidence(company_data: Dict[str, Any]) -> Tuple[float, List[str]]:
    """Calculates data completeness and provenance confidence score."""
    score = 0.0
    reasons = []

    if company_data.get("domain") or company_data.get("website"):
        score += 25.0
        reasons.append("Web presence identified (+25)")

    if company_data.get("emails"):
        score += 25.0
        reasons.append("Contact emails identified (+25)")

    if company_data.get("phones"):
        score += 20.0
        reasons.append("Contact phones identified (+20)")

    if company_data.get("address") or company_data.get("city"):
        score += 15.0
        reasons.append("Physical/city location identified (+15)")

    if company_data.get("description"):
        score += 15.0
        reasons.append("Business description populated (+15)")

    return min(score, 100.0), reasons
