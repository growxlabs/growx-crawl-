"""
GrowX Entity Resolution Review Queue.
Manages candidate resolution records requiring human or supervisor review.
"""

from typing import List, Optional
from growx_crawl.entity_resolution.models import ResolutionCandidate, ResolutionDecision


class ReviewManager:
    """Manages manual approval or rejection of resolution candidates."""

    def approve_candidate(self, candidate: ResolutionCandidate, resolved_by: str = "reviewer") -> ResolutionCandidate:
        candidate.decision = ResolutionDecision.MERGED_MANUAL
        candidate.status = "approved"
        candidate.metadata_json["resolved_by"] = resolved_by
        return candidate

    def reject_candidate(self, candidate: ResolutionCandidate, rejected_by: str = "reviewer", reason: str = "") -> ResolutionCandidate:
        candidate.decision = ResolutionDecision.REJECTED_MANUAL
        candidate.status = "rejected"
        candidate.metadata_json["rejected_by"] = rejected_by
        candidate.metadata_json["rejection_reason"] = reason
        return candidate
