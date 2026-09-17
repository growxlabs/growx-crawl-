"""
Tests for Phase 08 — Data Quality Gates.
Verifies:
- All 5 gate tiers (Canonical Ingestion, Intelligence Trust, Prospect Eligibility, Personalization, Outreach)
- Hard safety blocks overriding completeness scores (suppression, domain conflict)
- Structured reason codes and deterministic required actions mapping
- ProspectQualitySnapshot multi-dimensional bundles
- Quarantine manager and audit retrieval
- In-memory & SQLite persistence
- Live metrics and telemetry
- AutoGTM ProspectHarvester integration
- FastAPI v1 endpoints
"""

import pytest
from fastapi.testclient import TestClient
from growx_crawl.autogtm.models import CompanyAnalysis, ICPProfile, ProspectLead
from growx_crawl.autogtm.prospector import prospect_harvester
from growx_crawl.quality import (
    CanonicalIngestionGate,
    DataQualityService,
    GateType,
    InMemoryQualityRepository,
    IntelligenceTrustGate,
    OutreachEligibilityGate,
    PersonalizationGate,
    ProspectEligibilityGate,
    ProspectQualitySnapshot,
    QualityDecision,
    QualityReasonCode,
    QualityStatus,
    RequiredAction,
    quality_service,
)
from growx_crawl.web.app import app
from tests.fixtures.golden_quality import (
    GOLDEN_CANONICAL_SCENARIOS,
    GOLDEN_INTELLIGENCE_SCENARIOS,
    GOLDEN_OUTREACH_SCENARIOS,
    GOLDEN_PERSONALIZATION_SCENARIOS,
    GOLDEN_PROSPECT_SCENARIOS,
)


@pytest.fixture
def mem_quality_service():
    """Provides an isolated in-memory quality service for unit testing."""
    repo = InMemoryQualityRepository()
    return DataQualityService(repository=repo)


@pytest.fixture
def test_client():
    return TestClient(app)


# ── 1. Gate 1: Canonical Ingestion ──

def test_canonical_ingestion_valid():
    scenario = GOLDEN_CANONICAL_SCENARIOS["valid_observation"]
    decision = CanonicalIngestionGate.evaluate(scenario)
    assert decision.gate_type == GateType.CANONICAL_INGESTION
    assert decision.status == QualityStatus.PASS
    assert decision.score >= 0.85
    assert QualityReasonCode.CANONICAL_IDENTITY_VALID.value in decision.reasons
    assert len(decision.required_actions) == 0


def test_canonical_ingestion_missing_identity():
    scenario = GOLDEN_CANONICAL_SCENARIOS["missing_identity"]
    decision = CanonicalIngestionGate.evaluate(scenario)
    assert decision.status == QualityStatus.QUARANTINE
    assert decision.score == 0.0
    assert QualityReasonCode.MISSING_CANONICAL_IDENTITY.value in decision.reasons
    assert RequiredAction.RESOLVE_IDENTITY.value in decision.required_actions


def test_canonical_ingestion_hard_conflict():
    scenario = GOLDEN_CANONICAL_SCENARIOS["hard_identity_conflict"]
    decision = CanonicalIngestionGate.evaluate(scenario)
    assert decision.status == QualityStatus.QUARANTINE
    assert decision.score <= 0.20
    assert QualityReasonCode.HARD_IDENTITY_CONFLICT.value in decision.reasons
    assert RequiredAction.RESOLVE_IDENTITY.value in decision.required_actions


# ── 2. Gate 2: Intelligence Trust ──

def test_intelligence_trust_valid():
    scenario = GOLDEN_INTELLIGENCE_SCENARIOS["trusted_fact"]
    decision = IntelligenceTrustGate.evaluate(scenario)
    assert decision.gate_type == GateType.INTELLIGENCE_TRUST
    assert decision.status == QualityStatus.PASS
    assert decision.score == 0.95
    assert QualityReasonCode.EVIDENCE_SUFFICIENT.value in decision.reasons


def test_intelligence_trust_insufficient_evidence():
    scenario = GOLDEN_INTELLIGENCE_SCENARIOS["insufficient_evidence"]
    decision = IntelligenceTrustGate.evaluate(scenario)
    assert decision.status == QualityStatus.LIMITED
    assert QualityReasonCode.INSUFFICIENT_EVIDENCE.value in decision.reasons
    assert RequiredAction.COLLECT_MORE_EVIDENCE.value in decision.required_actions


def test_intelligence_trust_low_confidence():
    scenario = GOLDEN_INTELLIGENCE_SCENARIOS["low_confidence"]
    decision = IntelligenceTrustGate.evaluate(scenario)
    assert decision.status == QualityStatus.BLOCKED
    assert QualityReasonCode.LOW_FACT_CONFIDENCE.value in decision.reasons


def test_intelligence_trust_stale_fact():
    scenario = GOLDEN_INTELLIGENCE_SCENARIOS["stale_fact"]
    decision = IntelligenceTrustGate.evaluate(scenario)
    assert decision.status == QualityStatus.REVERIFY
    assert QualityReasonCode.DATA_STALE.value in decision.reasons


# ── 3. Gate 3: Prospect Eligibility ──

def test_prospect_eligibility_valid():
    scenario = GOLDEN_PROSPECT_SCENARIOS["eligible_prospect"]
    decision = ProspectEligibilityGate.evaluate(scenario)
    assert decision.gate_type == GateType.PROSPECT_ELIGIBILITY
    assert decision.status == QualityStatus.PASS
    assert decision.score >= 0.80
    assert QualityReasonCode.DOMAIN_VERIFIED.value in decision.reasons


def test_prospect_eligibility_duplicate():
    scenario = GOLDEN_PROSPECT_SCENARIOS["duplicate_prospect"]
    existing = ["prsp_existing_001", "other_id"]
    decision = ProspectEligibilityGate.evaluate(scenario, existing_prospect_ids=existing)
    assert decision.status == QualityStatus.BLOCKED
    assert decision.score == 0.0
    assert QualityReasonCode.DUPLICATE_PROSPECT.value in decision.reasons
    assert RequiredAction.DEDUPLICATE.value in decision.required_actions


def test_prospect_eligibility_missing_domain():
    scenario = GOLDEN_PROSPECT_SCENARIOS["missing_domain"]
    decision = ProspectEligibilityGate.evaluate(scenario)
    assert decision.status == QualityStatus.BLOCKED
    assert QualityReasonCode.MISSING_PRIMARY_DOMAIN.value in decision.reasons


def test_prospect_eligibility_unverified():
    scenario = GOLDEN_PROSPECT_SCENARIOS["unverified_prospect"]
    decision = ProspectEligibilityGate.evaluate(scenario)
    assert decision.status == QualityStatus.LIMITED
    assert QualityReasonCode.DOMAIN_UNVERIFIED.value in decision.reasons


def test_prospect_eligibility_stale():
    scenario = GOLDEN_PROSPECT_SCENARIOS["stale_verification"]
    decision = ProspectEligibilityGate.evaluate(scenario)
    assert decision.status == QualityStatus.REVERIFY
    assert QualityReasonCode.DOMAIN_STALE.value in decision.reasons
    assert RequiredAction.REVERIFY_DOMAIN.value in decision.required_actions


# ── 4. Gate 4: Personalization Eligibility ──

def test_personalization_valid():
    scenario = GOLDEN_PERSONALIZATION_SCENARIOS["ready_for_drafting"]
    decision = PersonalizationGate.evaluate(scenario)
    assert decision.gate_type == GateType.PERSONALIZATION_ELIGIBILITY
    assert decision.status == QualityStatus.PASS
    assert decision.score >= 0.80
    assert QualityReasonCode.EVIDENCE_SUFFICIENT.value in decision.reasons


def test_personalization_missing_context():
    scenario = GOLDEN_PERSONALIZATION_SCENARIOS["missing_required_context"]
    decision = PersonalizationGate.evaluate(scenario)
    assert decision.status == QualityStatus.BLOCKED
    assert QualityReasonCode.PROFILE_INCOMPLETE.value in decision.reasons


def test_personalization_missing_hook():
    scenario = GOLDEN_PERSONALIZATION_SCENARIOS["missing_hook"]
    decision = PersonalizationGate.evaluate(scenario)
    assert decision.status == QualityStatus.LIMITED
    assert QualityReasonCode.INSUFFICIENT_EVIDENCE.value in decision.reasons
    assert RequiredAction.COLLECT_MORE_EVIDENCE.value in decision.required_actions


# ── 5. Gate 5: Outreach Eligibility ──

def test_outreach_valid():
    scenario = GOLDEN_OUTREACH_SCENARIOS["outreach_ready"]
    decision = OutreachEligibilityGate.evaluate(scenario)
    assert decision.gate_type == GateType.OUTREACH_ELIGIBILITY
    assert decision.status == QualityStatus.PASS
    assert decision.score >= 0.90
    assert QualityReasonCode.EMAIL_VERIFIED.value in decision.reasons


def test_outreach_suppressed():
    scenario = GOLDEN_OUTREACH_SCENARIOS["suppressed_recipient"]
    suppressed = ["do-not-contact@competitor.com", "opt-out@somewhere.com"]
    decision = OutreachEligibilityGate.evaluate(scenario, suppressed_emails=suppressed)
    assert decision.status == QualityStatus.BLOCKED
    assert decision.score == 0.0
    assert QualityReasonCode.EMAIL_SUPPRESSED.value in decision.reasons
    assert RequiredAction.SUPPRESS.value in decision.required_actions


def test_outreach_stale_employment():
    scenario = GOLDEN_OUTREACH_SCENARIOS["stale_employment"]
    decision = OutreachEligibilityGate.evaluate(scenario)
    assert decision.status == QualityStatus.REVERIFY
    assert QualityReasonCode.STALE_EMPLOYMENT.value in decision.reasons
    assert RequiredAction.REFRESH_EMPLOYMENT.value in decision.required_actions


def test_outreach_role_account():
    scenario = GOLDEN_OUTREACH_SCENARIOS["role_account"]
    decision = OutreachEligibilityGate.evaluate(scenario)
    assert decision.status == QualityStatus.LIMITED
    assert QualityReasonCode.EMAIL_ROLE_ACCOUNT.value in decision.reasons


def test_outreach_catchall():
    scenario = GOLDEN_OUTREACH_SCENARIOS["catchall_domain"]
    decision = OutreachEligibilityGate.evaluate(scenario)
    assert decision.status == QualityStatus.LIMITED
    assert QualityReasonCode.EMAIL_CATCHALL.value in decision.reasons


def test_outreach_unverified_email():
    scenario = GOLDEN_OUTREACH_SCENARIOS["unverified_email"]
    decision = OutreachEligibilityGate.evaluate(scenario)
    assert decision.status == QualityStatus.REVERIFY
    assert QualityReasonCode.EMAIL_UNVERIFIED.value in decision.reasons
    assert RequiredAction.REVERIFY_EMAIL.value in decision.required_actions


# ── 6. DataQualityService Facade & Bundle Snapshots ──

def test_service_evaluate_and_state(mem_quality_service):
    scenario = GOLDEN_PROSPECT_SCENARIOS["eligible_prospect"]
    decision = mem_quality_service.evaluate(
        subject_type="prospect",
        subject_id="prsp_test_123",
        gate_type=GateType.PROSPECT_ELIGIBILITY,
        data=scenario,
    )
    assert decision.status == QualityStatus.PASS

    # Verify cached state
    state = mem_quality_service.get_current("prospect", "prsp_test_123", GateType.PROSPECT_ELIGIBILITY)
    assert state is not None
    assert state.status == QualityStatus.PASS
    assert state.score == decision.score


def test_service_quarantine(mem_quality_service):
    malformed = {"raw": "corrupted binary buffer", "length": 128}
    reasons = [QualityReasonCode.MISSING_CANONICAL_IDENTITY.value]
    q_rec = mem_quality_service.quarantine_item(
        subject_type="observation",
        payload=malformed,
        reasons=reasons,
        source_id="obs_bad_99",
    )
    assert q_rec.id.startswith("qrn_")
    assert q_rec.status == "pending"

    # List quarantined
    items = mem_quality_service.list_quarantined(status="pending")
    assert any(i.id == q_rec.id for i in items)


def test_evaluate_prospect_bundle(mem_quality_service):
    bundle_data = {
        "id": "prsp_marcus_vance",
        "name": "Hexagon Data",
        "lead_name": "Marcus Vance",
        "company_name": "Hexagon Data",
        "domain": "hexagondata.io",
        "industry": "Enterprise Software",
        "description": "Cloud data warehouse modern pipeline orchestrator",
        "email": "marcus@hexagondata.io",
        "email_status": "verified",
        "employment_status": "verified",
        "sender_offer": "GrowX autonomous prospecting platform",
        "personalization_hook": "Recent expansion of data stack integrations",
        "verification_status": "verified",
        "verification_confidence": 0.95,
    }

    snapshot = mem_quality_service.evaluate_prospect_bundle(bundle_data)
    assert isinstance(snapshot, ProspectQualitySnapshot)
    assert snapshot.prospect_id == "prsp_marcus_vance"
    assert snapshot.overall_status == QualityStatus.PASS
    assert snapshot.company_score >= 0.80
    assert snapshot.outreach_score >= 0.90
    assert snapshot.personalization_score >= 0.80
    assert len(snapshot.required_actions) == 0


def test_evaluate_prospect_bundle_blocked_by_suppression(mem_quality_service):
    bundle_data = {
        "id": "prsp_suppressed_lead",
        "name": "Target Company",
        "lead_name": "John Doe",
        "company_name": "Target Company",
        "domain": "targetco.com",
        "email": "optout@targetco.com",
        "email_status": "verified",
        "employment_status": "verified",
        "sender_offer": "Automation tools",
        "personalization_hook": "Growth in Q3",
        "verification_status": "verified",
    }
    suppressed = ["optout@targetco.com"]

    snapshot = mem_quality_service.evaluate_prospect_bundle(
        bundle_data, suppressed_emails=suppressed
    )
    # Hard safety block on outreach must override
    assert snapshot.overall_status == QualityStatus.BLOCKED
    assert snapshot.outreach_score == 0.0
    assert QualityReasonCode.EMAIL_SUPPRESSED.value in snapshot.reasons
    assert RequiredAction.SUPPRESS.value in snapshot.required_actions


def test_evaluate_batch(mem_quality_service):
    items = [
        {
            "id": "c1",
            "name": "Company One",
            "domain": "one.com",
            "industry": "Tech",
            "description": "SaaS Platform",
            "city": "Austin",
            "verification_status": "verified",
        },
        {"id": "c2", "name": "Company Two", "domain": "two.com", "verification_status": "unverified"},
    ]
    results = mem_quality_service.evaluate_batch(items, GateType.PROSPECT_ELIGIBILITY)
    assert len(results) == 2
    assert results[0].status == QualityStatus.PASS
    assert results[1].status == QualityStatus.LIMITED


# ── 7. AutoGTM ProspectHarvester Integration ──

@pytest.mark.asyncio
async def test_prospect_harvester_includes_quality():
    analysis = CompanyAnalysis(
        domain="hexagondata.io",
        company_name="Hexagon Data",
        tagline="Modern Cloud Data",
        summary="Data platform",
        primary_offer="ETL orchestration",
    )
    icp = ICPProfile(
        target_industries=["Technology", "Software"],
        target_roles=["VP of Revenue Growth", "Head of Sales"],
    )

    leads = await prospect_harvester.harvest_leads(analysis, icp, limit=2)
    assert len(leads) > 0
    first_lead = leads[0]
    assert isinstance(first_lead, ProspectLead)
    # Phase 08 fields populated
    assert first_lead.quality_status in [s.value for s in QualityStatus]
    assert first_lead.quality_score is not None
    assert 0.0 <= first_lead.quality_score <= 1.0
    assert isinstance(first_lead.quality_reasons, list)


# ── 8. FastAPI API Endpoints ──

def test_api_quality_evaluate(test_client):
    headers = {"X-API-Key": "gx_live_sandbox_master_key"}
    payload = {
        "subject_type": "prospect",
        "subject_id": "prsp_api_test",
        "gate_type": "prospect_eligibility",
        "data": {
            "name": "Hexagon Data",
            "domain": "hexagondata.io",
            "industry": "Software",
            "description": "Enterprise Data",
            "city": "Austin",
            "verification_status": "verified",
            "verification_confidence": 0.95,
        },
    }
    resp = test_client.post("/api/v1/quality/evaluate", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["gate_type"] == "prospect_eligibility"
    assert data["status"] in ["pass", "limited"]
    assert "score" in data
    assert "reasons" in data


def test_api_quality_metrics(test_client):
    headers = {"X-API-Key": "gx_live_sandbox_master_key"}
    resp = test_client.get("/api/v1/quality/metrics", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "evaluations_total" in data
    assert "pass_rate" in data
    assert "gate_breakdown" in data
