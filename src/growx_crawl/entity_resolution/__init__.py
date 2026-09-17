"""
GrowX Entity Resolution Subsystem.
Owns candidate generation, similarity matching, scoring, thresholds, explanations, and review.
"""

from growx_crawl.entity_resolution.models import (
    ResolutionDecision,
    MatchSignal,
    MatchExplanation,
    ResolutionCandidate,
    BlockingKey,
)
from growx_crawl.entity_resolution.thresholds import (
    AUTO_MERGE_THRESHOLD,
    REVIEW_THRESHOLD,
    NO_MATCH_THRESHOLD,
)
from growx_crawl.entity_resolution.decisions import evaluate_decision
from growx_crawl.entity_resolution.explain import build_explanation
from growx_crawl.entity_resolution.scoring import jaro_winkler_similarity, token_overlap_score
from growx_crawl.entity_resolution.candidate_generation import generate_company_blocking_keys, find_candidate_pairs
from growx_crawl.entity_resolution.conflicts import detect_company_conflicts
from growx_crawl.entity_resolution.review import ReviewManager
from growx_crawl.entity_resolution.company.matcher import CompanyMatcher
from growx_crawl.entity_resolution.person.matcher import PersonMatcher
from growx_crawl.entity_resolution.service import EntityResolutionService, entity_resolution_service

__all__ = [
    "ResolutionDecision",
    "MatchSignal",
    "MatchExplanation",
    "ResolutionCandidate",
    "BlockingKey",
    "AUTO_MERGE_THRESHOLD",
    "REVIEW_THRESHOLD",
    "NO_MATCH_THRESHOLD",
    "evaluate_decision",
    "build_explanation",
    "jaro_winkler_similarity",
    "token_overlap_score",
    "generate_company_blocking_keys",
    "find_candidate_pairs",
    "detect_company_conflicts",
    "ReviewManager",
    "CompanyMatcher",
    "PersonMatcher",
    "EntityResolutionService",
    "entity_resolution_service",
]
