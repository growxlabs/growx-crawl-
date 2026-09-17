"""
GrowX Verification Package.
Canonical verification for companies, domains, people, employment, emails, and facts.
"""

from growx_crawl.verification.models import (
    VerificationStatus,
    VerificationResultEntity,
    VerificationPolicy,
)
from growx_crawl.verification.policies import POLICIES, get_policy
from growx_crawl.verification.confidence import calculate_verification_confidence
from growx_crawl.verification.email import EmailVerifier, email_verifier
from growx_crawl.verification.domain import verify_domain
from growx_crawl.verification.company import verify_company
from growx_crawl.verification.person import verify_person
from growx_crawl.verification.employment import verify_employment
from growx_crawl.verification.fact import verify_fact
from growx_crawl.verification.repository import BaseVerificationRepository, InMemoryVerificationRepository
from growx_crawl.verification.service import VerificationService, verification_service

__all__ = [
    "VerificationStatus",
    "VerificationResultEntity",
    "VerificationPolicy",
    "POLICIES",
    "get_policy",
    "calculate_verification_confidence",
    "EmailVerifier",
    "email_verifier",
    "verify_domain",
    "verify_company",
    "verify_person",
    "verify_employment",
    "verify_fact",
    "BaseVerificationRepository",
    "InMemoryVerificationRepository",
    "VerificationService",
    "verification_service",
]
