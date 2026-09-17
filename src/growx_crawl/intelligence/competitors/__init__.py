"""
GrowX Competitor Graph Package.
"""

from growx_crawl.intelligence.competitors.discovery import (
    CompetitiveProfileBuilder,
    CompetitorCandidateGenerator,
)
from growx_crawl.intelligence.competitors.explain import CompetitorExplainer
from growx_crawl.intelligence.competitors.graph import CompetitorGraph
from growx_crawl.intelligence.competitors.models import (
    CompanyCompetitorSummary,
    CompetitiveProfile,
    CompetitorEvidenceEntity,
    CompetitorRejectionEntity,
    CompetitorRelationshipEntity,
    EvidenceType,
    ReasonCode,
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
    jaccard_similarity,
)
from growx_crawl.intelligence.competitors.service import (
    CompetitorGraphService,
    competitor_service,
)
from growx_crawl.intelligence.competitors.verification import CompetitorVerifier

__all__ = [
    "RelationshipType",
    "RelationshipStatus",
    "EvidenceType",
    "ReasonCode",
    "CompetitiveProfile",
    "CompetitorRelationshipEntity",
    "CompetitorEvidenceEntity",
    "CompetitorRejectionEntity",
    "CompanyCompetitorSummary",
    "CompetitorVerificationPolicy",
    "DEFAULT_COMPETITOR_POLICY",
    "canonical_pair",
    "CompetitorExplainer",
    "jaccard_similarity",
    "calculate_market_overlap",
    "calculate_offering_overlap",
    "calculate_customer_overlap",
    "calculate_geography_overlap",
    "calculate_strength",
    "calculate_confidence",
    "classify_relationship_type",
    "CompetitiveProfileBuilder",
    "CompetitorCandidateGenerator",
    "CompetitorVerifier",
    "BaseCompetitorRepository",
    "SqliteCompetitorRepository",
    "CompetitorGraph",
    "CompetitorRefreshEngine",
    "CompetitorGraphService",
    "competitor_service",
]
