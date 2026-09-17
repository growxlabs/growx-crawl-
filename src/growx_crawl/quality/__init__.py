"""
GrowX Data Quality System.
Exports the complete Data Quality Gates subsystem:
- Facade service & default singleton
- 5 Gate implementations
- Reason codes & required remediation actions
- Enums, models, and repositories
- Telemetry metrics and event bus
"""

from growx_crawl.quality.actions import RequiredAction, map_reasons_to_actions
from growx_crawl.quality.gates import (
    CanonicalIngestionGate,
    IntelligenceTrustGate,
    OutreachEligibilityGate,
    PersonalizationGate,
    ProspectEligibilityGate,
)
from growx_crawl.quality.metrics import (
    QualityEventBus,
    QualityMetrics,
    quality_events,
    quality_metrics,
)
from growx_crawl.quality.models import (
    GateType,
    ProspectQualitySnapshot,
    QualityDecision,
    QualityPolicy,
    QualityResultEntity,
    QualityRuleResult,
    QualityStateEntity,
    QualityStatus,
    QuarantineEntity,
    RuleType,
)
from growx_crawl.quality.policies import (
    ALL_POLICIES,
    get_quality_policy,
)
from growx_crawl.quality.profiles import (
    ALL_PROFILES,
    get_quality_profile,
)
from growx_crawl.quality.quarantine import QuarantineManager, quarantine_manager
from growx_crawl.quality.reasons import QualityReasonCode
from growx_crawl.quality.repository import (
    InMemoryQualityRepository,
    QualityRepository,
    SqliteQualityRepository,
)
from growx_crawl.quality.rules import QualityRuleEvaluator
from growx_crawl.quality.scoring import compute_quality_score
from growx_crawl.quality.service import DataQualityService, quality_service

__all__ = [
    # Facade
    "DataQualityService",
    "quality_service",
    # Enums & Models
    "GateType",
    "QualityStatus",
    "RuleType",
    "QualityRuleResult",
    "QualityDecision",
    "QualityPolicy",
    "QualityResultEntity",
    "QualityStateEntity",
    "QuarantineEntity",
    "ProspectQualitySnapshot",
    # Reasons & Actions
    "QualityReasonCode",
    "RequiredAction",
    "map_reasons_to_actions",
    # Gates
    "CanonicalIngestionGate",
    "IntelligenceTrustGate",
    "ProspectEligibilityGate",
    "PersonalizationGate",
    "OutreachEligibilityGate",
    # Rules & Scoring
    "QualityRuleEvaluator",
    "compute_quality_score",
    # Profiles & Policies
    "get_quality_profile",
    "ALL_PROFILES",
    "get_quality_policy",
    "ALL_POLICIES",
    # Quarantine
    "QuarantineManager",
    "quarantine_manager",
    # Telemetry
    "QualityEventBus",
    "QualityMetrics",
    "quality_events",
    "quality_metrics",
    # Persistence
    "QualityRepository",
    "InMemoryQualityRepository",
    "SqliteQualityRepository",
]
