"""
GrowX ICP Intelligence Module.
Provides structured, versioned, explainable Ideal Customer Profiles for prospect discovery and qualification.
"""

from growx_crawl.intelligence.icp.builder import ICPBuilder
from growx_crawl.intelligence.icp.criteria import CriterionEvaluator
from growx_crawl.intelligence.icp.evidence import ICPEvidenceLinker
from growx_crawl.intelligence.icp.exclusions import ExclusionEngine
from growx_crawl.intelligence.icp.explain import ICPExplainer
from growx_crawl.intelligence.icp.models import (
    CriterionCategory,
    CriterionOperator,
    ExclusionType,
    FitStatus,
    ICPCompanyScoreEntity,
    ICPCriterionEntity,
    ICPEntity,
    ICPEvidenceEntity,
    ICPExclusionEntity,
    ICPPersonaEntity,
    ICPPersonScoreEntity,
    ICPStatus,
    ICPType,
    ICPVersionEntity,
    PersonaCategory,
    ReasonCode,
    ReasonCode as ICPReasonCode,
    RequirementType,
    SellerSnapshotEntity,
)
from growx_crawl.intelligence.icp.personas import PersonaMatcher
from growx_crawl.intelligence.icp.policies import DEFAULT_ICP_POLICY, ICPEvaluationPolicy
from growx_crawl.intelligence.icp.refresh import ICPRefreshEngine
from growx_crawl.intelligence.icp.repository import BaseICPRepository, SqliteICPRepository
from growx_crawl.intelligence.icp.scoring import ICPScorer
from growx_crawl.intelligence.icp.service import ICPIntelligenceService, icp_service
from growx_crawl.intelligence.icp.versions import ICPVersionManager

__all__ = [
    "ICPType",
    "ICPStatus",
    "CriterionCategory",
    "RequirementType",
    "CriterionOperator",
    "ExclusionType",
    "FitStatus",
    "PersonaCategory",
    "ReasonCode",
    "ICPReasonCode",
    "ICPEntity",
    "ICPVersionEntity",
    "SellerSnapshotEntity",
    "ICPCriterionEntity",
    "ICPExclusionEntity",
    "ICPPersonaEntity",
    "ICPCompanyScoreEntity",
    "ICPPersonScoreEntity",
    "ICPEvidenceEntity",
    "ICPEvaluationPolicy",
    "DEFAULT_ICP_POLICY",
    "CriterionEvaluator",
    "ExclusionEngine",
    "PersonaMatcher",
    "ICPExplainer",
    "ICPVersionManager",
    "ICPEvidenceLinker",
    "ICPBuilder",
    "ICPScorer",
    "ICPRefreshEngine",
    "BaseICPRepository",
    "SqliteICPRepository",
    "ICPIntelligenceService",
    "icp_service",
]
