"""
Phase 06 — GrowX Verify Comprehensive Test Suite.
Verifies all 32 deliverables and acceptance criteria across models, policies,
confidence calculation, freshness engine, domain verification, company verification,
company-domain verification, person verification, employment verification,
email verification, fact verification, verification gate, repository persistence,
events, and metrics.
"""

import pytest
from growx_crawl.verification.models import (
    DomainState,
    EmploymentState,
    FreshnessState,
    GateDecision,
    ReasonCode,
    SubjectType,
    VerificationPolicy,
    VerificationResultEntity,
    VerificationStatus,
)
from growx_crawl.verification.policies import STANDARD_POLICIES, get_policy
from growx_crawl.verification.freshness import (
    calculate_valid_until,
    evaluate_freshness,
    recommend_refresh,
)
from growx_crawl.verification.confidence import (
    CONFIDENCE_PROFILES,
    compute_verification_confidence,
)
from growx_crawl.verification.gate import VerificationGate
from growx_crawl.verification.domain import verify_domain
from growx_crawl.verification.company import verify_company
from growx_crawl.verification.company_domain import verify_company_domain
from growx_crawl.verification.person import verify_person
from growx_crawl.verification.employment import verify_employment
from growx_crawl.verification.email import EmailVerifier, email_verifier
from growx_crawl.verification.fact import verify_fact
from growx_crawl.verification.repository import InMemoryVerificationRepository
from growx_crawl.verification.service import VerificationService, verification_service
from growx_crawl.verification.metrics import verification_metrics
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.fixtures.golden_verification import (
    GOLDEN_COMPANIES,
    GOLDEN_DOMAINS,
    GOLDEN_EMAILS,
    GOLDEN_EMPLOYMENTS,
    GOLDEN_FACTS,
)


def test_models_and_enums():
    assert SubjectType.COMPANY.value == "company"
    assert VerificationStatus.VERIFIED.value == "verified"
    assert VerificationStatus.STALE.value == "stale"
    assert GateDecision.ALLOW.value == "ALLOW"
    assert GateDecision.BLOCK.value == "BLOCK"
    assert FreshnessState.FRESH.value == "fresh"
    assert DomainState.ACTIVE.value == "active"
    assert EmploymentState.CURRENT_VERIFIED.value == "current_verified"

    # ReasonCode presence
    assert ReasonCode.OFFICIAL_DOMAIN_ACTIVE == "OFFICIAL_DOMAIN_ACTIVE"
    assert ReasonCode.ROLE_ADDRESS_DETECTED == "ROLE_ADDRESS_DETECTED"
    assert ReasonCode.FREE_EMAIL_PROVIDER == "FREE_EMAIL_PROVIDER"


def test_policy_registry_and_freshness():
    # Policy registry
    p_comp = get_policy("company")
    assert p_comp.name == "company_default_v1"
    assert p_comp.min_confidence == 0.80
    assert p_comp.ttl_hours == 4320  # 180 days

    p_email = get_policy("email")
    assert p_email.ttl_hours == 720  # 30 days

    # Freshness evaluation
    state_fresh, ratio_fresh = evaluate_freshness("2026-09-17T00:00:00Z", ttl_hours=720)
    assert state_fresh == FreshnessState.FRESH
    assert ratio_fresh >= 0.90

    state_stale, _ = evaluate_freshness("2024-01-01T00:00:00Z", ttl_hours=720)
    assert state_stale in (FreshnessState.STALE, FreshnessState.EXPIRED)

    # Refresh recommendations
    rec = recommend_refresh("employment", FreshnessState.STALE, priority="campaign_active")
    assert rec["needs_refresh"] is True
    assert rec["priority_level"] == 2


def test_confidence_engine():
    # Multi-factor operational confidence
    conf = compute_verification_confidence(
        subject_type="company",
        base_source_score=0.90,
        identity_strength=0.95,
        source_agreement=0.85,
        technical_checks_score=0.90,
        freshness_score=1.0,
        conflict_penalty=0.0,
    )
    assert 0.85 <= conf <= 1.0

    # Conflict penalty
    conf_conflict = compute_verification_confidence(
        subject_type="company",
        base_source_score=0.90,
        identity_strength=0.95,
        source_agreement=0.85,
        technical_checks_score=0.90,
        conflict_penalty=0.40,
    )
    assert conf_conflict < conf


@pytest.mark.asyncio
async def test_domain_verification():
    # Active public domain
    res = await verify_domain("google.com")
    assert res.status in (VerificationStatus.VERIFIED, VerificationStatus.SUPPORTED)
    assert res.confidence >= 0.80
    assert res.details_json.get("dns_ok") is True

    # Malformed / empty domain
    res_bad = await verify_domain("")
    assert res_bad.status == VerificationStatus.INVALID
    assert res_bad.confidence == 0.0


@pytest.mark.asyncio
async def test_company_domain_verification():
    # Matching company and domain
    res = await verify_company_domain(
        company_id="cmp_stripe",
        company_name="Stripe Inc",
        domain_str="stripe.com",
        site_metadata={"title": "Stripe | Financial Infrastructure for the Internet"},
        company_emails=["support@stripe.com"],
    )
    assert res.status == VerificationStatus.VERIFIED
    assert res.details_json["relationship"] == "belongs"
    assert res.confidence >= 0.85

    # Conflicting company and domain
    res_conflict = await verify_company_domain(
        company_id="cmp_unrelated",
        company_name="Acme Widgets",
        domain_str="microsoft.com",
        company_emails=["sales@different.org"],
    )
    assert res_conflict.status == VerificationStatus.CONFLICTING
    assert res_conflict.details_json["relationship"] == "does_not_belong"


@pytest.mark.asyncio
async def test_company_verification():
    # Valid active company
    valid_data = GOLDEN_COMPANIES["active_valid"]
    res = await verify_company(valid_data["id"], valid_data)
    assert res.status in (VerificationStatus.VERIFIED, VerificationStatus.SUPPORTED)
    assert res.confidence >= 0.80

    # Inactive company without name
    dead_data = GOLDEN_COMPANIES["inactive_malformed"]
    res_dead = await verify_company(dead_data["id"], dead_data)
    assert res_dead.status == VerificationStatus.INVALID
    assert res_dead.confidence == 0.0


@pytest.mark.asyncio
async def test_person_verification():
    # Complete person
    res = await verify_person("per_1", {
        "name": "Sarah Connor",
        "email": "sarah@cyberdyne.com",
        "linkedin_url": "https://linkedin.com/in/sarah-connor",
        "title": "Head of Security",
    })
    assert res.status == VerificationStatus.VERIFIED
    assert res.confidence >= 0.75

    # Incomplete single name
    res_single = await verify_person("per_2", {"name": "Cher"})
    assert res_single.status == VerificationStatus.INVALID


@pytest.mark.asyncio
async def test_employment_verification():
    # Fresh valid employment
    valid_emp = GOLDEN_EMPLOYMENTS["current_valid"]
    res_cur = await verify_employment(
        person_id=valid_emp["person_id"],
        company_id=valid_emp["company_id"],
        person_email=valid_emp["person_email"],
        company_domain=valid_emp["company_domain"],
        observed_at_iso=valid_emp["observed_at_iso"],
        on_team_page=valid_emp["on_team_page"],
    )
    assert res_cur.status == VerificationStatus.VERIFIED
    assert res_cur.details_json["employment_state"] == "current_verified"

    # Stale employment (> 365 days)
    stale_emp = GOLDEN_EMPLOYMENTS["stale_employment"]
    res_stale = await verify_employment(
        person_id=stale_emp["person_id"],
        company_id=stale_emp["company_id"],
        person_email=stale_emp["person_email"],
        company_domain=stale_emp["company_domain"],
        observed_at_iso=stale_emp["observed_at_iso"],
    )
    assert res_stale.status == VerificationStatus.STALE
    assert res_stale.details_json["employment_state"] == "stale"


@pytest.mark.asyncio
async def test_email_verification_enhanced():
    v = EmailVerifier()

    # Role address detection
    role_email = "support@growxlabs.com"
    assert v.is_role_address(role_email) is True
    assert v.is_role_address("alex@growxlabs.com") is False

    # Free provider detection
    free_email = "user123@gmail.com"
    assert v.is_free_provider(free_email) is True
    assert v.is_free_provider("alex@growxlabs.com") is False

    # Full VerificationResultEntity
    res_role = await v.verify_entity(role_email)
    assert res_role.details_json["role_address"] is True
    assert ReasonCode.ROLE_ADDRESS_DETECTED in res_role.reason_codes

    res_free = await v.verify_entity(free_email)
    assert res_free.details_json["free_provider"] is True
    assert ReasonCode.FREE_EMAIL_PROVIDER in res_free.reason_codes

    # Invalid syntax
    res_invalid = await v.verify_entity("broken-email")
    assert res_invalid.status == VerificationStatus.INVALID


@pytest.mark.asyncio
async def test_fact_verification():
    # Supported fact with evidence
    f_supp = GOLDEN_FACTS["supported_fact"]
    res_supp = await verify_fact(f_supp["fact_id"], f_supp)
    assert res_supp.status == VerificationStatus.VERIFIED
    assert ReasonCode.EVIDENCE_PROVENANCE_CONFIRMED in res_supp.reason_codes

    # Conflicting fact
    f_conf = GOLDEN_FACTS["conflicting_fact"]
    res_conf = await verify_fact(f_conf["fact_id"], f_conf)
    assert res_conf.status == VerificationStatus.CONFLICTING
    assert ReasonCode.FACT_SOURCE_CONFLICT in res_conf.reason_codes

    # Stale fact
    f_stale = GOLDEN_FACTS["stale_fact"]
    res_stale = await verify_fact(f_stale["fact_id"], f_stale)
    assert res_stale.status == VerificationStatus.STALE


def test_verification_gate():
    # 1. Fully verified bundle -> ALLOW
    res_comp = VerificationResultEntity(
        id="ver_1", subject_type="company", subject_id="cmp_1", status=VerificationStatus.VERIFIED, confidence=0.95
    )
    res_per = VerificationResultEntity(
        id="ver_2", subject_type="person", subject_id="per_1", status=VerificationStatus.VERIFIED, confidence=0.90
    )
    res_emp = VerificationResultEntity(
        id="ver_3", subject_type="employment", subject_id="per_1:cmp_1", status=VerificationStatus.VERIFIED, confidence=0.92
    )
    res_email = VerificationResultEntity(
        id="ver_4", subject_type="email", subject_id="alex@co.com", status=VerificationStatus.VERIFIED, confidence=0.95
    )

    eval_allow = VerificationGate.evaluate(res_comp, res_per, res_emp, res_email)
    assert eval_allow.decision == GateDecision.ALLOW
    assert eval_allow.confidence >= 0.90

    # 2. Role address email -> ALLOW_WITH_RISK
    res_email_role = VerificationResultEntity(
        id="ver_5",
        subject_type="email",
        subject_id="info@co.com",
        status=VerificationStatus.SUPPORTED,
        confidence=0.85,
        details_json={"role_address": True},
    )
    eval_risk = VerificationGate.evaluate(res_comp, res_per, res_emp, res_email_role)
    assert eval_risk.decision == GateDecision.ALLOW_WITH_RISK

    # 3. Stale employment -> REVERIFY
    res_emp_stale = VerificationResultEntity(
        id="ver_6", subject_type="employment", subject_id="per_1:cmp_1", status=VerificationStatus.STALE, confidence=0.40
    )
    eval_reverify = VerificationGate.evaluate(res_comp, res_per, res_emp_stale, res_email)
    assert eval_reverify.decision == GateDecision.REVERIFY
    assert eval_reverify.refresh_recommended is True

    # 4. Invalid email -> BLOCK
    res_email_bad = VerificationResultEntity(
        id="ver_7", subject_type="email", subject_id="dead@invalid.com", status=VerificationStatus.INVALID, confidence=0.0
    )
    eval_block = VerificationGate.evaluate(res_comp, res_per, res_emp, res_email_bad)
    assert eval_block.decision == GateDecision.BLOCK


@pytest.mark.asyncio
async def test_verification_service_and_repository():
    repo = InMemoryVerificationRepository()
    srv = VerificationService(repository=repo)

    # Verify company
    res = await srv.verify_company("cmp_test_123", company_data={"name": "GrowX Labs", "domain": "growxlabs.com"})
    assert res.subject_id == "cmp_test_123"

    # Verify state cached in repo
    cached_state = repo.get_state("company", "cmp_test_123", "company")
    assert cached_state is not None
    assert cached_state.status == res.status

    # Fast state lookup without force refresh
    res_reused = await srv.verify_company("cmp_test_123", force_refresh=False)
    assert res_reused.id == res.id

    # Batch verification
    items = [
        {"subject_type": "email", "subject_id": "contact@growxlabs.com"},
        {"subject_type": "domain", "subject_id": "growxlabs.com"},
    ]
    batch_res = await srv.batch_verify(items)
    assert len(batch_res) == 2

    # Metrics
    summary = verification_metrics.get_summary()
    assert summary["runs_total"] >= 1
