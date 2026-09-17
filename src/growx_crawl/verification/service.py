"""
GrowX Verification Service.
The canonical verification service that decides whether companies, domains,
people, employments, emails, and facts are trustworthy enough for downstream GTM use.
"""

from typing import Any, Dict, List, Optional
from growx_crawl.shared.hashing import deterministic_json_hash
from growx_crawl.verification.company import CompanyVerifier, company_verifier
from growx_crawl.verification.company_domain import CompanyDomainVerifier, company_domain_verifier
from growx_crawl.verification.domain import DomainVerifier, domain_verifier
from growx_crawl.verification.email import EmailVerifier, email_verifier
from growx_crawl.verification.employment import EmploymentVerifier, employment_verifier
from growx_crawl.verification.events import verification_events
from growx_crawl.verification.fact import FactVerifier, fact_verifier
from growx_crawl.verification.freshness import evaluate_freshness
from growx_crawl.verification.gate import GateEvaluation, VerificationGate
from growx_crawl.verification.metrics import verification_metrics
from growx_crawl.verification.models import (
    FreshnessState,
    GateDecision,
    VerificationResultEntity,
    VerificationStatus,
)
from growx_crawl.verification.person import PersonVerifier, person_verifier
from growx_crawl.verification.policies import get_policy
from growx_crawl.verification.repository import BaseVerificationRepository, InMemoryVerificationRepository


class VerificationService:
    """The authoritative verification domain facade."""

    def __init__(
        self,
        repository: Optional[BaseVerificationRepository] = None,
        d_verifier: Optional[DomainVerifier] = None,
        c_verifier: Optional[CompanyVerifier] = None,
        cd_verifier: Optional[CompanyDomainVerifier] = None,
        p_verifier: Optional[PersonVerifier] = None,
        e_verifier: Optional[EmploymentVerifier] = None,
        em_verifier: Optional[EmailVerifier] = None,
        f_verifier: Optional[FactVerifier] = None,
    ):
        self.repository = repository or InMemoryVerificationRepository()
        self.domain_verifier = d_verifier or domain_verifier
        self.company_verifier = c_verifier or company_verifier
        self.company_domain_verifier = cd_verifier or company_domain_verifier
        self.person_verifier = p_verifier or person_verifier
        self.employment_verifier = e_verifier or employment_verifier
        self.email_verifier = em_verifier or email_verifier
        self.fact_verifier = f_verifier or fact_verifier

    def _should_reuse_state(self, current_state) -> bool:
        if not current_state or not current_state.valid_until:
            return False
        state, _ = evaluate_freshness(current_state.last_verified_at, current_state.valid_until)
        return state == FreshnessState.FRESH

    async def verify_company(
        self,
        company_id: str,
        company_data: Optional[Dict[str, Any]] = None,
        *,
        policy: Optional[str] = None,
        force_refresh: bool = False,
    ) -> VerificationResultEntity:
        policy_name = policy or "company_default_v1"
        if not force_refresh:
            state = self.repository.get_state("company", company_id, "company")
            if state and self._should_reuse_state(state):
                return VerificationResultEntity(
                    id=state.latest_run_id,
                    subject_type="company",
                    subject_id=company_id,
                    verification_type="company",
                    status=state.status,
                    confidence=state.confidence,
                    policy_name=policy_name,
                    verified_at=state.last_verified_at,
                    valid_until=state.valid_until,
                    details_json=state.metadata_json,
                )

        verification_events.emit("verification.started", "company", company_id, "started", 0.0)
        data = company_data or {"name": company_id}
        result = await self.company_verifier.verify(company_id, data, policy_name)

        self.repository.save_result(result)
        verification_metrics.record_result(result)
        verification_events.emit(
            "verification.completed", "company", company_id, result.status.value, result.confidence
        )
        return result

    async def verify_domain(
        self,
        domain_str: str,
        *,
        policy: Optional[str] = None,
        force_refresh: bool = False,
    ) -> VerificationResultEntity:
        policy_name = policy or "domain_default_v1"
        if not force_refresh:
            state = self.repository.get_state("domain", domain_str, "domain")
            if state and self._should_reuse_state(state):
                return VerificationResultEntity(
                    id=state.latest_run_id,
                    subject_type="domain",
                    subject_id=domain_str,
                    verification_type="domain",
                    status=state.status,
                    confidence=state.confidence,
                    policy_name=policy_name,
                    verified_at=state.last_verified_at,
                    valid_until=state.valid_until,
                    details_json=state.metadata_json,
                )

        verification_events.emit("verification.started", "domain", domain_str, "started", 0.0)
        result = await self.domain_verifier.verify(domain_str, policy_name)

        self.repository.save_result(result)
        verification_metrics.record_result(result)
        verification_events.emit(
            "verification.completed", "domain", domain_str, result.status.value, result.confidence
        )
        return result

    async def verify_company_domain(
        self,
        company_id: str,
        domain_str: str,
        *,
        company_name: str = "",
        site_metadata: Optional[Dict[str, Any]] = None,
        company_emails: Optional[List[str]] = None,
        policy: Optional[str] = None,
    ) -> VerificationResultEntity:
        policy_name = policy or "company_domain_default_v1"
        result = await self.company_domain_verifier.verify(
            company_id=company_id,
            company_name=company_name or company_id,
            domain_str=domain_str,
            site_metadata=site_metadata,
            company_emails=company_emails,
            policy_name=policy_name,
        )
        self.repository.save_result(result)
        verification_metrics.record_result(result)
        return result

    async def verify_person(
        self,
        person_id: str,
        person_data: Optional[Dict[str, Any]] = None,
        *,
        policy: Optional[str] = None,
        force_refresh: bool = False,
    ) -> VerificationResultEntity:
        policy_name = policy or "person_default_v1"
        if not force_refresh:
            state = self.repository.get_state("person", person_id, "person")
            if state and self._should_reuse_state(state):
                return VerificationResultEntity(
                    id=state.latest_run_id,
                    subject_type="person",
                    subject_id=person_id,
                    verification_type="person",
                    status=state.status,
                    confidence=state.confidence,
                    policy_name=policy_name,
                    verified_at=state.last_verified_at,
                    valid_until=state.valid_until,
                    details_json=state.metadata_json,
                )

        verification_events.emit("verification.started", "person", person_id, "started", 0.0)
        data = person_data or {"name": person_id}
        result = await self.person_verifier.verify(person_id, data, policy_name)

        self.repository.save_result(result)
        verification_metrics.record_result(result)
        verification_events.emit(
            "verification.completed", "person", person_id, result.status.value, result.confidence
        )
        return result

    async def verify_employment(
        self,
        person_id: str,
        company_id: str,
        person_email: str = "",
        company_domain: str = "",
        *,
        observed_at_iso: Optional[str] = None,
        on_team_page: bool = False,
        policy: Optional[str] = None,
    ) -> VerificationResultEntity:
        policy_name = policy or "employment_default_v1"
        result = await self.employment_verifier.verify(
            person_id=person_id,
            company_id=company_id,
            person_email=person_email,
            company_domain=company_domain,
            observed_at_iso=observed_at_iso,
            on_team_page=on_team_page,
            policy_name=policy_name,
        )
        self.repository.save_result(result)
        verification_metrics.record_result(result)
        verification_events.emit(
            "employment.verified", "employment", f"{person_id}:{company_id}", result.status.value, result.confidence
        )
        return result

    async def verify_email(
        self,
        email: str,
        person_id: Optional[str] = None,
        company_id: Optional[str] = None,
        *,
        policy: Optional[str] = None,
        force_refresh: bool = False,
    ) -> VerificationResultEntity:
        policy_name = policy or "email_default_v1"
        if not force_refresh:
            state = self.repository.get_state("email", email, "email")
            if state and self._should_reuse_state(state):
                return VerificationResultEntity(
                    id=state.latest_run_id,
                    subject_type="email",
                    subject_id=email,
                    verification_type="email",
                    status=state.status,
                    confidence=state.confidence,
                    policy_name=policy_name,
                    verified_at=state.last_verified_at,
                    valid_until=state.valid_until,
                    details_json=state.metadata_json,
                )

        verification_events.emit("verification.started", "email", email, "started", 0.0)
        result = await self.email_verifier.verify_entity(
            email=email, person_id=person_id, company_id=company_id, policy_name=policy_name
        )

        self.repository.save_result(result)
        verification_metrics.record_result(result)
        verification_events.emit(
            "email.verified", "email", email, result.status.value, result.confidence
        )
        return result

    async def verify_fact(
        self,
        fact_id: str,
        fact_data: Optional[Dict[str, Any]] = None,
        *,
        policy: Optional[str] = None,
    ) -> VerificationResultEntity:
        policy_name = policy or "fact_default_v1"
        data = fact_data or {}
        result = await self.fact_verifier.verify(fact_id, data, policy_name)

        self.repository.save_result(result)
        verification_metrics.record_result(result)
        verification_events.emit(
            "fact.verified", "fact", fact_id, result.status.value, result.confidence
        )
        return result

    async def verify_entity_bundle(
        self,
        company_data: Dict[str, Any],
        person_data: Dict[str, Any],
        email: str,
    ) -> GateEvaluation:
        """Executes end-to-end multi-subject verification and evaluates the trust gate."""
        comp_id = company_data.get("id") or "cmp_temp"
        per_id = person_data.get("id") or "per_temp"
        domain = company_data.get("domain") or (email.split("@")[1] if "@" in email else "")

        comp_res = await self.verify_company(comp_id, company_data=company_data)
        per_res = await self.verify_person(per_id, person_data=person_data)
        emp_res = await self.verify_employment(
            person_id=per_id,
            company_id=comp_id,
            person_email=email,
            company_domain=domain,
            on_team_page=bool(person_data.get("on_team_page")),
        )
        email_res = await self.verify_email(email, person_id=per_id, company_id=comp_id)

        gate_eval = VerificationGate.evaluate(
            company_res=comp_res,
            person_res=per_res,
            employment_res=emp_res,
            email_res=email_res,
        )
        return gate_eval

    async def batch_verify(
        self,
        items: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Processes verification requests in concurrent batches."""
        results = []
        for item in items:
            subj_type = item.get("subject_type")
            subj_id = item.get("subject_id")
            if subj_type == "email":
                res = await self.verify_email(subj_id)
            elif subj_type == "company":
                res = await self.verify_company(subj_id, company_data=item.get("data", {}))
            elif subj_type == "domain":
                res = await self.verify_domain(subj_id)
            elif subj_type == "person":
                res = await self.verify_person(subj_id, person_data=item.get("data", {}))
            else:
                continue
            results.append({"subject_id": subj_id, "status": res.status.value, "confidence": res.confidence})
        return results


verification_service = VerificationService()
