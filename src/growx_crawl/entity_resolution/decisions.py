"""
GrowX Entity Resolution Decisions.
Evaluates match score against standard thresholds to produce a deterministic decision.
"""

from growx_crawl.entity_resolution.models import ResolutionDecision
from growx_crawl.entity_resolution.thresholds import AUTO_MERGE_THRESHOLD, REVIEW_THRESHOLD


def evaluate_decision(confidence: float) -> ResolutionDecision:
    """Classifies a confidence score into AUTO_MERGED, REVIEW_REQUIRED, or NO_MATCH."""
    if confidence >= AUTO_MERGE_THRESHOLD:
        return ResolutionDecision.AUTO_MERGED
    if confidence >= REVIEW_THRESHOLD:
        return ResolutionDecision.REVIEW_REQUIRED
    return ResolutionDecision.NO_MATCH
