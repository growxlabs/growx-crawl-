"""
GrowX Quality Scoring Engine.
Computes normalized 0.0 - 1.0 quality scores across attribute completeness,
verification confidence, and evidence grounding.
"""

from typing import Any, Dict, List, Tuple


def compute_quality_score(
    has_required: bool,
    completeness_ratio: float,
    verification_confidence: float = 1.0,
    evidence_score: float = 1.0,
    penalties: float = 0.0,
) -> Tuple[float, Dict[str, float]]:
    """
    Computes a composite quality score between 0.0 and 1.0.
    Formula:
        score = (0.30 * required) + (0.30 * completeness) + (0.25 * verification) + (0.15 * evidence) - penalties
    """
    if not has_required:
        # Severe penalty if mandatory requirements missing
        req_val = 0.0
    else:
        req_val = 1.0

    comp_val = max(0.0, min(1.0, completeness_ratio))
    ver_val = max(0.0, min(1.0, verification_confidence))
    evi_val = max(0.0, min(1.0, evidence_score))

    raw_score = (0.30 * req_val) + (0.30 * comp_val) + (0.25 * ver_val) + (0.15 * evi_val) - penalties
    final_score = round(max(0.0, min(1.0, raw_score)), 3)

    return final_score, {
        "required_component": round(0.30 * req_val, 3),
        "completeness_component": round(0.30 * comp_val, 3),
        "verification_component": round(0.25 * ver_val, 3),
        "evidence_component": round(0.15 * evi_val, 3),
        "penalties": round(penalties, 3),
        "final_score": final_score,
    }
