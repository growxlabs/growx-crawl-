"""
GrowX Verification Subsystem (Phase 06 — GrowX Verify).
The canonical verification service that decides whether companies, domains,
people, employments, emails, and facts are trustworthy enough for downstream GTM use.
"""

from growx_crawl.verification.models import (
    SubjectType,
    VerificationStatus,
    GateDecision,
    FreshnessState,
    DomainState,
    EmploymentState,
    EmailState,
    ReasonCode,
    VerificationCheckEntity,
    VerificationRunEntity,
    VerificationStateEntity,
    VerificationResultEntity,
    VerificationPolicy,
)
from growx_crawl.verification.policies import (
    STANDARD_POLICIES,
    POLICIES,
    get_policy,
)
from growx_crawl.verification.freshness import (
    evaluate_freshness,
    calculate_valid_until,
    recommend_refresh,
)
from growx_crawl.verification.confidence import (
    compute_verification_confidence,
    calculate_verification_confidence,
    CONFIDENCE_PROFILES,
)
from growx_crawl.verification.gate import (
    VerificationGate,
    GateEvaluation,
    verification_gate,
)
from growx_crawl.verification.domain import (
    DomainVerifier,
    domain_verifier,
    verify_domain,
)
from growx_crawl.verification.company import (
    CompanyVerifier,
    company_verifier,
    verify_company,
)
from growx_crawl.verification.company_domain import (
    CompanyDomainVerifier,
    company_domain_verifier,
    verify_company_domain,
)
from growx_crawl.verification.person import (
    PersonVerifier,
    person_verifier,
    verify_person,
)
from growx_crawl.verification.employment import (
    EmploymentVerifier,
    employment_verifier,
    verify_employment,
)
from growx_crawl.verification.email import (
    EmailVerifier,
    email_verifier,
)
from growx_crawl.verification.fact import (
    FactVerifier,
    fact_verifier,
    verify_fact,
)
from growx_crawl.verification.repository import (
    BaseVerificationRepository,
    InMemoryVerificationRepository,
    SqliteVerificationRepository,
)
from growx_crawl.verification.events import (
    VerificationEvent,
    VerificationEventPublisher,
    verification_events,
)
from growx_crawl.verification.metrics import (
    VerificationMetricsTracker,
    verification_metrics,
)
from growx_crawl.verification.service import (
    VerificationService,
    verification_service,
)

__all__ = [
    # Models & Enums
    "SubjectType",
    "VerificationStatus",
    "GateDecision",
    "FreshnessState",
    "DomainState",
    "EmploymentState",
    "EmailState",
    "ReasonCode",
    "VerificationCheckEntity",
    "VerificationRunEntity",
    "VerificationStateEntity",
    "VerificationResultEntity",
    "VerificationPolicy",
    # Policies & Freshness
    "STANDARD_POLICIES",
    "POLICIES",
    "get_policy",
    "evaluate_freshness",
    "calculate_valid_until",
    "recommend_refresh",
    # Confidence
    "compute_verification_confidence",
    "calculate_verification_confidence",
    "CONFIDENCE_PROFILES",
    # Gate
    "VerificationGate",
    "GateEvaluation",
    "verification_gate",
    # Verifiers
    "DomainVerifier",
    "domain_verifier",
    "verify_domain",
    "CompanyVerifier",
    "company_verifier",
    "verify_company",
    "CompanyDomainVerifier",
    "company_domain_verifier",
    "verify_company_domain",
    "PersonVerifier",
    "person_verifier",
    "verify_person",
    "EmploymentVerifier",
    "employment_verifier",
    "verify_employment",
    "EmailVerifier",
    "email_verifier",
    "FactVerifier",
    "fact_verifier",
    "verify_fact",
    # Storage & Observability
    "BaseVerificationRepository",
    "InMemoryVerificationRepository",
    "SqliteVerificationRepository",
    "VerificationEvent",
    "VerificationEventPublisher",
    "verification_events",
    "VerificationMetricsTracker",
    "verification_metrics",
    # Facade Service
    "VerificationService",
    "verification_service",
]
