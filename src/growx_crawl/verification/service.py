"""
GrowX Verification Service.
Authoritative service boundary answering: 'Can we trust this data enough to use it?'
Coordinates email, company, domain, person, employment, and fact verification.
"""

from typing import Any, Dict, Optional
from growx_crawl.verification.company import verify_company
from growx_crawl.verification.domain import verify_domain
from growx_crawl.verification.email import EmailVerifier, email_verifier
from growx_crawl.verification.employment import verify_employment
from growx_crawl.verification.fact import verify_fact
from growx_crawl.verification.models import VerificationResultEntity
from growx_crawl.verification.person import verify_person
from growx_crawl.verification.repository import BaseVerificationRepository, InMemoryVerificationRepository


class VerificationService:
    """Canonical facade for all verification operations across GrowX."""

    def __init__(
        self,
        repository: Optional[BaseVerificationRepository] = None,
        email_v: Optional[EmailVerifier] = None,
    ):
        self.repository = repository or InMemoryVerificationRepository()
        self.email_verifier = email_v or email_verifier

    async def verify_email(self, email: str) -> Dict[str, Any]:
        """Runs asynchronous DoH and SMTP verification for an email address."""
        return await self.email_verifier.verify(email)

    async def verify_domain(self, domain_str: str) -> VerificationResultEntity:
        """Verifies DNS reachability of a domain."""
        result = await verify_domain(domain_str)
        self.repository.save_result(result)
        return result

    async def verify_company(self, company_id: str, company_data: Dict[str, Any]) -> VerificationResultEntity:
        """Verifies company identity readiness."""
        result = await verify_company(company_id, company_data)
        self.repository.save_result(result)
        return result

    async def verify_person(self, person_id: str, person_data: Dict[str, Any]) -> VerificationResultEntity:
        """Verifies individual identity readiness."""
        result = await verify_person(person_id, person_data)
        self.repository.save_result(result)
        return result

    async def verify_employment(
        self,
        person_id: str,
        company_id: str,
        person_email: str,
        company_domain: str,
    ) -> VerificationResultEntity:
        """Verifies person employment at specified company."""
        result = await verify_employment(person_id, company_id, person_email, company_domain)
        self.repository.save_result(result)
        return result

    async def verify_fact(self, fact_id: str, fact_data: Dict[str, Any]) -> VerificationResultEntity:
        """Verifies canonical fact provenance and confidence threshold."""
        result = await verify_fact(fact_id, fact_data)
        self.repository.save_result(result)
        return result


verification_service = VerificationService()
