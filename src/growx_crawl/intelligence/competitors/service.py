"""
GrowX Competitor Graph Service.
Unified service boundary for discovery, pair scoring, verification, graph queries, and summaries.
"""

import logging
from typing import Any, Dict, List, Optional

from growx_crawl.intelligence.competitors.discovery import (
    CompetitiveProfileBuilder,
    CompetitorCandidateGenerator,
)
from growx_crawl.intelligence.competitors.graph import CompetitorGraph
from growx_crawl.intelligence.competitors.models import (
    CompanyCompetitorSummary,
    CompetitiveProfile,
    CompetitorEvidenceEntity,
    CompetitorRejectionEntity,
    CompetitorRelationshipEntity,
    RelationshipStatus,
    RelationshipType,
)
from growx_crawl.intelligence.competitors.policies import (
    CompetitorVerificationPolicy,
    DEFAULT_COMPETITOR_POLICY,
    canonical_pair,
)
from growx_crawl.intelligence.competitors.refresh import CompetitorRefreshEngine
from growx_crawl.intelligence.competitors.repository import (
    BaseCompetitorRepository,
    SqliteCompetitorRepository,
)
from growx_crawl.intelligence.competitors.scoring import (
    calculate_confidence,
    calculate_customer_overlap,
    calculate_geography_overlap,
    calculate_market_overlap,
    calculate_offering_overlap,
    calculate_strength,
    classify_relationship_type,
)
from growx_crawl.intelligence.competitors.verification import CompetitorVerifier
from growx_crawl.shared.ids import generate_id
from growx_crawl.shared.time import utc_iso_now

logger = logging.getLogger("growx_crawl.intelligence.competitors.service")


class CompetitorGraphService:
    """
    Primary service boundary for competitor intelligence.
    Enforces internal-data-first discovery, multi-dimensional scoring, and evidence-backed verification.
    """

    def __init__(
        self,
        repository: Optional[BaseCompetitorRepository] = None,
        policy: CompetitorVerificationPolicy = DEFAULT_COMPETITOR_POLICY,
        profile_builder: Optional[CompetitiveProfileBuilder] = None,
        candidate_generator: Optional[CompetitorCandidateGenerator] = None,
        verifier: Optional[CompetitorVerifier] = None,
    ):
        self.repository = repository or SqliteCompetitorRepository()
        self.policy = policy
        self.profile_builder = profile_builder or CompetitiveProfileBuilder()
        self.candidate_generator = candidate_generator or CompetitorCandidateGenerator(
            profile_builder=self.profile_builder
        )
        self.verifier = verifier or CompetitorVerifier(policy=self.policy)
        self.graph = CompetitorGraph(repository=self.repository)
        self.refresh_engine = CompetitorRefreshEngine(repository=self.repository)

    def discover(
        self,
        company_id: str,
        company_data: Optional[Dict[str, Any]] = None,
        max_candidates: int = 50,
        verify_top: int = 20,
        known_companies: Optional[List[Dict[str, Any]]] = None,
    ) -> List[CompetitorRelationshipEntity]:
        """
        Discovers, scores, and verifies competitor relationships for a target company.
        Applies internal-data-first candidate generation and updates the competitor summary.
        """
        target_profile = self.profile_builder.build_profile(
            company_id=company_id,
            company_data=company_data,
        )

        candidates = self.candidate_generator.generate_candidates(
            target_profile=target_profile,
            rejection_check_fn=self.repository.is_rejected,
            limit=max_candidates,
            known_companies=known_companies,
        )

        relationships: List[CompetitorRelationshipEntity] = []

        for candidate_profile in candidates:
            rel = self._evaluate_and_persist_pair(
                target_profile, candidate_profile, evidence_list=None
            )
            relationships.append(rel)

        # Sort by strength
        relationships.sort(key=lambda r: r.strength, reverse=True)

        # Update denormalized competitor summary (Section 44)
        top_ids = [
            (r.competitor_company_id if r.company_id == company_id else r.company_id)
            for r in relationships[:5]
            if r.status in (RelationshipStatus.VERIFIED.value, RelationshipStatus.SUPPORTED.value)
        ]
        verified_count = sum(
            1 for r in relationships if r.status == RelationshipStatus.VERIFIED.value
        )
        summary = CompanyCompetitorSummary(
            company_id=company_id,
            top_competitor_ids=top_ids,
            competitor_count=len(relationships),
            verified_competitor_count=verified_count,
            last_refreshed_at=utc_iso_now(),
        )
        self.repository.save_summary(summary)

        return relationships[:verify_top]

    def score_pair(
        self,
        company_a_id: str,
        company_b_id: str,
        profile_a: Optional[CompetitiveProfile] = None,
        profile_b: Optional[CompetitiveProfile] = None,
        evidence_list: Optional[List[CompetitorEvidenceEntity]] = None,
    ) -> CompetitorRelationshipEntity:
        """Scores and verifies a single competitor pair."""
        p_a = profile_a or self.profile_builder.build_profile(company_a_id)
        p_b = profile_b or self.profile_builder.build_profile(company_b_id)
        return self._evaluate_and_persist_pair(p_a, p_b, evidence_list)

    def _evaluate_and_persist_pair(
        self,
        profile_a: CompetitiveProfile,
        profile_b: CompetitiveProfile,
        evidence_list: Optional[List[CompetitorEvidenceEntity]] = None,
    ) -> CompetitorRelationshipEntity:
        """Internal pair evaluation, verification, and persistence logic."""
        pair_key = canonical_pair(profile_a.company_id, profile_b.company_id)
        ev_list = evidence_list or []

        # Check existing evidence in repository if none supplied
        existing_rel = self.repository.get_relationship_by_pair(pair_key)
        if existing_rel and not ev_list:
            ev_list = self.repository.list_evidence(existing_rel.id)

        # Overlap calculations
        m_overlap = calculate_market_overlap(profile_a, profile_b)
        o_overlap = calculate_offering_overlap(profile_a, profile_b)
        c_overlap = calculate_customer_overlap(profile_a, profile_b)
        g_overlap = calculate_geography_overlap(profile_a, profile_b)

        # Strength & Confidence (Kept strictly separate per Section 19)
        strength = calculate_strength(
            market_overlap=m_overlap,
            offering_overlap=o_overlap,
            customer_overlap=c_overlap,
            geography_overlap=g_overlap,
            explicit_evidence_count=len(ev_list),
            policy=self.policy,
        )
        confidence = calculate_confidence(
            evidence_list=ev_list,
            profile_a_quality=profile_a.data_quality_score,
            profile_b_quality=profile_b.data_quality_score,
        )

        # Relationship typing
        rel_type = classify_relationship_type(
            strength=strength,
            market_overlap=m_overlap,
            offering_overlap=o_overlap,
            customer_overlap=c_overlap,
            geography_overlap=g_overlap,
            policy=self.policy,
        )

        # Corporate relationships check (e.g. parent/subsidiary, supplier/partner)
        corp_rel = self.repository.get_corporate_relationship(
            profile_a.company_id, profile_b.company_id
        )

        # Verification gate
        status, reasons = self.verifier.verify(
            profile_a=profile_a,
            profile_b=profile_b,
            strength=strength,
            confidence=confidence,
            market_overlap=m_overlap,
            offering_overlap=o_overlap,
            customer_overlap=c_overlap,
            geography_overlap=g_overlap,
            evidence_list=ev_list,
            corporate_relationship=corp_rel,
        )

        now = utc_iso_now()
        rel_id = existing_rel.id if existing_rel else generate_id("cpr_")

        rel = CompetitorRelationshipEntity(
            id=rel_id,
            company_id=profile_a.company_id,
            competitor_company_id=profile_b.company_id,
            canonical_pair=pair_key,
            relationship_type=rel_type,
            status=status,
            confidence=confidence,
            strength=strength,
            market_overlap=m_overlap,
            offering_overlap=o_overlap,
            customer_overlap=c_overlap,
            geography_overlap=g_overlap,
            evidence_count=len(ev_list),
            first_seen_at=existing_rel.first_seen_at if existing_rel else now,
            last_seen_at=now,
            last_verified_at=now if status == RelationshipStatus.VERIFIED.value else None,
            scoring_version="v1",
            policy_version=self.policy.policy_version,
            reasons=reasons,
        )

        self.repository.save_relationship(rel)

        # Rejection Memory (Section 57): Remember strong rejections to prevent wasted re-evaluation
        if status == RelationshipStatus.REJECTED.value and reasons:
            rejection = CompetitorRejectionEntity(
                canonical_pair=pair_key,
                company_a=profile_a.company_id,
                company_b=profile_b.company_id,
                reason_code=reasons[0],
                rejected_at=now,
                policy_version=self.policy.policy_version,
            )
            self.repository.save_rejection(rejection)

        # Attach evidence items
        for ev in ev_list:
            ev.relationship_id = rel.id
            self.repository.save_evidence(ev)

        return rel

    def get_competitors(
        self,
        company_id: str,
        relationship_types: Optional[List[str]] = None,
        min_strength: float = 0.0,
        status: Optional[str] = None,
        limit: int = 20,
    ) -> List[CompetitorRelationshipEntity]:
        """Queries competitor list for a company."""
        return self.graph.get_competitors(
            company_id=company_id,
            relationship_types=relationship_types,
            min_strength=min_strength,
            status=status,
            limit=limit,
        )

    def get_graph(
        self,
        company_id: str,
        depth: int = 1,
        min_strength: float = 0.0,
        status_filter: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Retrieves network nodes and edges around a company."""
        return self.graph.get_graph(
            company_id=company_id,
            depth=depth,
            min_strength=min_strength,
            status_filter=status_filter,
        )

    def get_company_summary(self, company_id: str) -> Optional[CompanyCompetitorSummary]:
        """Retrieves cached competitor summary for GTM consumption."""
        return self.repository.get_summary(company_id)

    def add_evidence(
        self,
        relationship_id: str,
        evidence_type: str,
        source_id: Optional[str] = None,
        confidence: float = 1.0,
        metadata_json: Optional[Dict[str, Any]] = None,
    ) -> CompetitorEvidenceEntity:
        """Attaches external evidence to an existing competitor relationship."""
        ev = CompetitorEvidenceEntity(
            id=generate_id("cpe_"),
            relationship_id=relationship_id,
            source_id=source_id,
            evidence_type=evidence_type,
            confidence=confidence,
            metadata_json=metadata_json or {},
        )
        self.repository.save_evidence(ev)
        return ev


# Module singleton
competitor_service = CompetitorGraphService()
