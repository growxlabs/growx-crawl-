"""
GrowX Entity Resolution Service.
Answers: 'Are these two records actually the same entity?'
Owns candidate generation, scoring, blocking rules, match explanations, and review decisions.
"""

from typing import Any, Dict, List, Optional
from growx_crawl.entity_resolution.candidate_generation import (
    find_candidate_pairs,
    generate_company_blocking_keys,
)
from growx_crawl.entity_resolution.company.matcher import CompanyMatcher
from growx_crawl.entity_resolution.decisions import evaluate_decision
from growx_crawl.entity_resolution.models import ResolutionCandidate, ResolutionDecision
from growx_crawl.entity_resolution.person.matcher import PersonMatcher
from growx_crawl.entity_resolution.repository import BaseResolutionRepository, InMemoryResolutionRepository
from growx_crawl.shared.ids import generate_id


class EntityResolutionService:
    """Canonical service boundary for pairwise matching, candidate generation, and merge decisions."""

    def __init__(self, repository: Optional[BaseResolutionRepository] = None):
        self.repository = repository or InMemoryResolutionRepository()
        self.company_matcher = CompanyMatcher()
        self.person_matcher = PersonMatcher()

    def evaluate_companies(
        self,
        c1: Dict[str, Any],
        c2: Dict[str, Any],
        c1_id: str,
        c2_id: str,
    ) -> ResolutionCandidate:
        confidence, explanation = self.company_matcher.match(c1, c2)
        decision = evaluate_decision(confidence)

        candidate = ResolutionCandidate(
            id=generate_id("cand_"),
            entity_type="company",
            source_entity_id=c1_id,
            target_entity_id=c2_id,
            confidence=confidence,
            decision=decision,
            signals=[s.name for s in explanation.signals],
            explanation=explanation,
            status="pending" if decision == ResolutionDecision.REVIEW_REQUIRED else "resolved",
        )
        self.repository.save_candidate(candidate)
        return candidate

    def evaluate_persons(
        self,
        p1: Dict[str, Any],
        p2: Dict[str, Any],
        p1_id: str,
        p2_id: str,
    ) -> ResolutionCandidate:
        confidence, explanation = self.person_matcher.match(p1, p2)
        decision = evaluate_decision(confidence)

        candidate = ResolutionCandidate(
            id=generate_id("cand_"),
            entity_type="person",
            source_entity_id=p1_id,
            target_entity_id=p2_id,
            confidence=confidence,
            decision=decision,
            signals=[s.name for s in explanation.signals],
            explanation=explanation,
            status="pending" if decision == ResolutionDecision.REVIEW_REQUIRED else "resolved",
        )
        self.repository.save_candidate(candidate)
        return candidate


entity_resolution_service = EntityResolutionService()
