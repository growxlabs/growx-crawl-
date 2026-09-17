"""
GrowX ICP Fit Scorer.
Evaluates company alignment against target ICP criteria (industry, geography, employee band).
Score range: 0.0 - 100.0
"""

from typing import Any, Dict, List, Optional, Tuple


def calculate_icp_fit(
    company_data: Dict[str, Any],
    target_industry: Optional[str] = None,
    target_location: Optional[str] = None,
) -> Tuple[float, List[str]]:
    """Evaluates ICP alignment independent of data quality."""
    score = 0.0
    reasons = []

    comp_ind = (company_data.get("industry") or "").lower()
    if target_industry:
        t_ind = target_industry.lower()
        if t_ind in comp_ind or comp_ind in t_ind:
            score += 50.0
            reasons.append(f"Industry '{target_industry}' matched (+50)")
        elif comp_ind:
            score += 20.0
            reasons.append("General industry populated (+20)")
    elif comp_ind:
        score += 30.0
        reasons.append("Industry defined (+30)")

    city = (company_data.get("city") or "").lower()
    if target_location:
        t_loc = target_location.lower()
        if t_loc in city:
            score += 50.0
            reasons.append(f"Location '{target_location}' matched (+50)")
    elif city:
        score += 20.0
        reasons.append("Location defined (+20)")

    return min(score, 100.0), reasons
