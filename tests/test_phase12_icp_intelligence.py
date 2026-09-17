"""
Phase 12 — ICP Intelligence Tests.
Comprehensive test suite verifying structured ICP generation, multi-ICP support, seller snapshot immutability,
hard exclusions, missing data as unknown, separation of fit vs confidence, must-have constraints,
historical signal criteria, persona matching, explainability, versioning, AutoGTM adapter,
caching fingerprints, and API endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from growx_crawl.autogtm.icp import ICPSynthesizer
from growx_crawl.autogtm.models import CompanyAnalysis, ICPProfile
from growx_crawl.intelligence.icp import (
    CriterionCategory,
    CriterionOperator,
    ExclusionType,
    FitStatus,
    ICPBuilder,
    ICPCompanyScoreEntity,
    ICPCriterionEntity,
    ICPEntity,
    ICPEvidenceEntity,
    ICPEvidenceLinker,
    ICPExclusionEntity,
    ICPExplainer,
    ICPIntelligenceService,
    ICPPersonaEntity,
    ICPPersonScoreEntity,
    ICPReasonCode,
    ICPRefreshEngine,
    ICPScorer,
    ICPStatus,
    ICPType,
    ICPVersionEntity,
    ICPVersionManager,
    PersonaCategory,
    PersonaMatcher,
    RequirementType,
    SellerSnapshotEntity,
    SqliteICPRepository,
)
from growx_crawl.storage.db import get_db
from growx_crawl.storage.sqlite.canonical import init_sqlite_canonical_tables
from growx_crawl.web.app import app


@pytest.fixture
def tmp_db(tmp_path):
    db_file = str(tmp_path / "test_phase12.db")
    with get_db(db_file) as conn:
        init_sqlite_canonical_tables(conn)
    return db_file


@pytest.fixture
def repo(tmp_db):
    return SqliteICPRepository(db_path=tmp_db)


@pytest.fixture
def service(repo):
    return ICPIntelligenceService(repository=repo)


# ── Test 1: Structured ICP Generation ──

def test_structured_icp_generation(service):
    """Builds a structured versioned ICP with firmographics, technographics, geography, and personas."""
    seller_data = {
        "company_name": "GrowX Labs",
        "domain": "growxlabs.com",
        "industry": "Sales Tech",
        "tech_stack": ["Python", "React", "PostgreSQL"],
    }
    icp, version = service.create_icp(
        seller_company_id="comp_growx",
        name="Primary SaaS ICP",
        description="Targeting B2B software companies",
        target_industries=["Software", "B2B SaaS"],
        target_geographies=["United States", "Canada"],
        target_employee_range=(50, 500),
        seller_data=seller_data,
        custom_criteria=[
            {
                "category": CriterionCategory.TECHNOGRAPHIC.value,
                "field": "tech_stack",
                "operator": CriterionOperator.CONTAINS.value,
                "value_json": "Salesforce",
                "weight": 1.2,
            }
        ],
    )

    assert icp.id.startswith("icp_")
    assert version.id.startswith("icpv_")
    assert version.version == 1
    assert version.status == ICPStatus.ACTIVE.value

    details = service.get_version_details(version.id)
    assert len(details["criteria"]) >= 4  # industry, geography, employee_count, tech_stack
    assert len(details["personas"]) >= 3  # technical, executive, operational
    assert details["snapshot"] is not None
    assert details["snapshot"].seller_company_id == "comp_growx"


# ── Test 2: Multiple ICPs per Seller ──

def test_multiple_icps_per_seller(service):
    """Verifies a single seller can have multiple active or distinct ICP definitions."""
    icp1, _ = service.create_icp(
        seller_company_id="comp_acme",
        name="Enterprise Healthcare ICP",
        target_industries=["Healthcare", "MedTech"],
        target_employee_range=(500, 5000),
    )
    icp2, _ = service.create_icp(
        seller_company_id="comp_acme",
        name="Mid-Market Fintech ICP",
        target_industries=["Fintech", "Banking"],
        target_employee_range=(50, 250),
    )

    seller_icps = service.list_icps(seller_company_id="comp_acme")
    assert len(seller_icps) == 2
    names = {i.name for i in seller_icps}
    assert "Enterprise Healthcare ICP" in names
    assert "Mid-Market Fintech ICP" in names


# ── Test 3: Seller Snapshot Preservation ──

def test_seller_snapshot_preservation(service):
    """Verifies SellerSnapshotEntity immutably captures seller state at generation time."""
    initial_seller_data = {
        "company_name": "CloudScale",
        "primary_offering": "Cloud Optimization",
        "headcount": 120,
    }
    _, version = service.create_icp(
        seller_company_id="comp_cloudscale",
        name="CloudScale ICP",
        seller_data=initial_seller_data,
    )

    details = service.get_version_details(version.id)
    snapshot = details["snapshot"]
    assert snapshot is not None
    assert snapshot.fact_snapshot_json["seller_data"]["headcount"] == 120

    # Even if outside state changes, snapshot in DB retains historical state
    retrieved_snapshot = service.repo.get_snapshot(snapshot.id)
    assert retrieved_snapshot.fact_snapshot_json["seller_data"]["headcount"] == 120


# ── Test 4: Hard Exclusions Override Fit ──

def test_hard_exclusions_override_fit(service):
    """Verifies that an account with 100% positive fit is excluded if matching an exclusion rule."""
    icp, version = service.create_icp(
        seller_company_id="comp_seller",
        name="B2B Targeting",
        target_industries=["Software"],
        target_employee_range=(50, 200),
        target_geographies=["United States"],
        custom_exclusions=[
            {
                "rule_type": ExclusionType.BAD_FIT.value,
                "field": "business_model",
                "operator": CriterionOperator.EQUALS.value,
                "value_json": "b2c",
                "reason": "We do not sell to B2C companies",
            }
        ],
    )

    # 1. Prospect matching competitor ID
    competitor_prospect = {
        "id": "comp_rival",
        "company_name": "Rival Inc",
        "industry": "Software",
        "employee_count": 100,
        "country": "United States",
    }
    score_comp = service.score_company(
        icp_id=icp.id,
        company_data=competitor_prospect,
        seller_competitor_ids=["comp_rival"],
    )
    assert score_comp.status == FitStatus.EXCLUDED.value
    assert score_comp.fit_score == 0.0
    assert "COMPETITOR_EXCLUDED" in score_comp.explanation_json["reason_codes"]

    # 2. Prospect matching custom exclusion rule
    b2c_prospect = {
        "id": "comp_b2c_app",
        "company_name": "Consumer Mobile App",
        "industry": "Software",
        "employee_count": 100,
        "country": "United States",
        "business_model": "b2c",
    }
    score_b2c = service.score_company(
        icp_id=icp.id,
        company_data=b2c_prospect,
    )
    assert score_b2c.status == FitStatus.EXCLUDED.value
    assert score_b2c.fit_score == 0.0
    assert "HARD_EXCLUSION" in score_b2c.explanation_json["reason_codes"]


# ── Test 5: Missing Data is Unknown ──

def test_missing_data_is_unknown(service):
    """Verifies missing fields are treated as unknown, lowering confidence rather than zeroing fit."""
    icp, _ = service.create_icp(
        seller_company_id="comp_seller",
        name="Tech Focused ICP",
        target_industries=["Software"],
        target_employee_range=(50, 500),
        custom_criteria=[
            {
                "category": CriterionCategory.TECHNOGRAPHIC.value,
                "field": "cloud_provider",
                "operator": CriterionOperator.EQUALS.value,
                "value_json": "AWS",
                "weight": 1.0,
            }
        ],
    )

    # Company with known industry/size, but missing cloud_provider
    partial_company = {
        "id": "comp_partial",
        "industry": "Software",
        "employee_count": 150,
        # cloud_provider is omitted
    }

    score = service.score_company(icp_id=icp.id, company_data=partial_company)
    # Fit score should still be positive because known criteria matched
    assert score.fit_score > 0.5
    # Data confidence should be reduced due to unknown criterion
    assert score.data_confidence < 1.0
    assert "cloud_provider" in score.explanation_json["unknown_factors"]


# ── Test 6: Separation of Fit vs Confidence vs Verification ──

def test_separation_of_fit_vs_confidence_vs_verification(service):
    """Verifies fit score, data confidence, and fact verification are distinct independent metrics."""
    icp, version = service.create_icp(
        seller_company_id="comp_seller",
        name="Metric Separation Test",
        target_industries=["Fintech"],
        target_geographies=["United Kingdom"],
    )

    # Add evidence link for a criterion
    details = service.get_version_details(version.id)
    first_crit = details["criteria"][0]
    linker = ICPEvidenceLinker()
    ev = linker.link_seller_fact(
        icp_version_id=version.id,
        criterion_id=first_crit.id,
        fact_id="fact_12345",
        confidence=0.95,
    )
    service.repo.save_evidence(ev)

    ev_list = service.repo.list_evidence(version.id, first_crit.id)
    assert len(ev_list) == 1
    assert ev_list[0].confidence == 0.95

    # Evaluating a prospect
    prospect = {
        "id": "comp_london_fintech",
        "industry": "Fintech",
        "country": "United Kingdom",
        "employee_count": 150,
    }
    score = service.score_company(icp_id=icp.id, company_data=prospect)
    assert score.fit_score >= 0.8
    assert score.data_confidence >= 0.5
    assert score.fit_score != score.data_confidence



# ── Test 7: Must-Have Conditions Enforcement ──

def test_must_have_conditions_enforcement(service):
    """A failed must-have required condition caps fit score and flags weak fit."""
    icp, _ = service.create_icp(
        seller_company_id="comp_seller",
        name="Strict Size ICP",
        target_industries=["Software"],
        target_employee_range=(100, 500),
        custom_criteria=[
            {
                "category": CriterionCategory.FIRMOGRAPHIC.value,
                "field": "employee_count",
                "operator": CriterionOperator.RANGE.value,
                "value_json": [100, 500],
                "requirement_type": RequirementType.REQUIRED.value,  # Must-have
            }
        ],
    )

    small_company = {
        "id": "comp_startup",
        "industry": "Software",
        "employee_count": 15,  # Fails required condition
    }

    score = service.score_company(icp_id=icp.id, company_data=small_company)
    assert score.status == FitStatus.WEAK_FIT.value
    assert score.fit_score <= 0.49
    assert "MUST_HAVE_FAILED" in score.explanation_json["reason_codes"]


# ── Test 8: Operational and Historical Signal Criteria ──

def test_operational_and_historical_signal_criteria(service):
    """Verifies operational signals (growth rate, hiring) evaluate and attach reason codes."""
    icp, _ = service.create_icp(
        seller_company_id="comp_seller",
        name="High Growth Signals ICP",
        target_industries=["Technology"],
        custom_criteria=[
            {
                "category": CriterionCategory.OPERATIONAL.value,
                "field": "growth_rate",
                "operator": CriterionOperator.GTE.value,
                "value_json": 20.0,
                "weight": 1.5,
            }
        ],
    )

    growing_company = {
        "id": "comp_fast_grower",
        "industry": "Technology",
        "country": "United States",
        "employee_count": 100,
        "growth_rate": 35.0,
    }

    score = service.score_company(icp_id=icp.id, company_data=growing_company)
    assert score.fit_score >= 0.8
    assert "RECENT_EXPANSION" in score.explanation_json["reason_codes"]



# ── Test 9: Buyer Persona Matching ──

def test_buyer_persona_matching():
    """Verifies title normalization and role matching to buyer personas."""
    matcher = PersonaMatcher()
    personas = [
        ICPPersonaEntity(
            id="prn_cto",
            icp_version_id="icpv_test",
            name="VP Engineering / CTO",
            department="Engineering",
            seniority="Executive",
            title_patterns=["cto", "chief technology officer", "vp of engineering", "head of engineering"],
            persona_category=PersonaCategory.TECHNICAL_BUYER.value,
        ),
        ICPPersonaEntity(
            id="prn_cro",
            icp_version_id="icpv_test",
            name="VP Sales / CRO",
            department="Sales",
            seniority="Executive",
            title_patterns=["cro", "vp of sales", "head of sales", "director of sales"],
            persona_category=PersonaCategory.ECONOMIC_BUYER.value,
        ),
    ]

    person1 = {"name": "Alice Smith", "title": "Vice President of Engineering"}
    matched, p_score, role, reasons = matcher.match_person(personas, person1)
    assert matched is not None
    assert matched.id == "prn_cto"
    assert p_score >= 0.8
    assert "PERSONA_TITLE_MATCH" in reasons

    person2 = {"name": "Bob Jones", "title": "VP of Sales"}
    matched2, p_score2, role2, _ = matcher.match_person(personas, person2)
    assert matched2 is not None
    assert matched2.id == "prn_cro"
    assert p_score2 >= 0.8


# ── Test 10: Person Fit Scoring ──

def test_person_fit_scoring(service):
    """Evaluates an individual person against target buyer personas with employment confidence."""
    icp, _ = service.create_icp(
        seller_company_id="comp_seller",
        name="Person Evaluation ICP",
    )

    person_data = {
        "id": "per_1001",
        "name": "Jane Doe",
        "title": "Head of Engineering",
        "employment_confidence": 0.9,
    }

    person_score = service.score_person(
        icp_id=icp.id,
        person_data=person_data,
        company_id="comp_target",
    )

    assert person_score.person_id == "per_1001"
    assert person_score.fit_score >= 0.7
    assert person_score.employment_confidence == 0.9
    assert person_score.role_matched is not None


# ── Test 11: Explainability and Reason Codes ──

def test_explainability_and_reason_codes(service):
    """Verifies stored score contains positive drivers, negative drivers, and standardized reason codes."""
    icp, _ = service.create_icp(
        seller_company_id="comp_seller",
        name="Explainable ICP",
        target_industries=["Cybersecurity"],
        target_geographies=["United States"],
        target_employee_range=(50, 200),
    )

    company = {
        "id": "comp_cyber_us",
        "industry": "Cybersecurity",
        "country": "United States",
        "employee_count": 25,  # Outside size range
    }

    score = service.score_company(icp_id=icp.id, company_data=company)
    exp = score.explanation_json
    assert "positive_drivers" in exp
    assert "negative_drivers" in exp
    assert "reason_codes" in exp
    assert "INDUSTRY_MATCH" in exp["reason_codes"]
    assert "GEOGRAPHY_MATCH" in exp["reason_codes"]
    assert "TOO_SMALL" in exp["reason_codes"]


# ── Test 12: Version Immutability and Activation ──

def test_version_immutability_and_activation(service):
    """Verifies draft creation, activation, and superseding of old versions."""
    icp, v1 = service.create_icp(
        seller_company_id="comp_seller",
        name="Versioned Profile",
        target_industries=["Healthcare"],
    )
    assert v1.status == ICPStatus.ACTIVE.value

    # Create draft v2
    v2 = service.create_version(
        icp_id=icp.id,
        target_industries=["Healthcare", "Biotech"],
    )
    assert v2.version == 2
    assert v2.status == ICPStatus.DRAFT.value

    # Activate v2
    activated_v2 = service.activate_version(icp.id, v2.id)
    assert activated_v2.status == ICPStatus.ACTIVE.value

    # Check that v1 is now superseded
    refreshed_v1 = service.get_version(v1.id)
    assert refreshed_v1.status == ICPStatus.SUPERSEDED.value

    # Check ICP current_version_id points to v2
    refreshed_icp = service.get_icp(icp.id)
    assert refreshed_icp.current_version_id == v2.id


# ── Test 13: Version Comparison ──

def test_version_comparison(service):
    """Compares two versions and identifies added/modified criteria."""
    icp, v1 = service.create_icp(
        seller_company_id="comp_seller",
        name="Comparison ICP",
        target_industries=["Retail"],
    )

    v2 = service.create_version(
        icp_id=icp.id,
        target_industries=["Retail", "eCommerce"],
        custom_criteria=[
            {
                "category": CriterionCategory.TECHNOGRAPHIC.value,
                "field": "ecommerce_platform",
                "operator": CriterionOperator.EQUALS.value,
                "value_json": "Shopify",
            }
        ],
    )

    diff = service.compare_versions(v1.id, v2.id)
    assert "criteria" in diff
    assert len(diff["criteria"]["added"]) >= 1


# ── Test 14: AutoGTM Adapter Compatibility ──

def test_autogtm_adapter_compatibility(service):
    """Verifies existing autogtm/icp.py continues working seamlessly via the ICPSynthesizer adapter."""
    synthesizer = ICPSynthesizer(service=service)
    analysis = CompanyAnalysis(
        domain="growx.ai",
        company_name="GrowX AI",
        primary_offer="AI Crawler & Lead Enrichment Pipeline",
        value_proposition="Automate B2B prospecting with verified signals",
        summary="Next-gen crawler and sales outreach platform",
        target_audience=["B2B SaaS Founders", "VPs of Sales"],
    )

    profile = synthesizer.synthesize(analysis)
    assert isinstance(profile, ICPProfile)
    assert len(profile.target_industries) > 0
    assert len(profile.target_roles) > 0
    assert len(profile.pain_points) > 0
    assert len(profile.search_dorks) > 0


# ── Test 15: Fit Fingerprint and Idempotency ──

def test_fit_fingerprint_and_idempotency(service):
    """Verifies stable cache fingerprints prevent redundant rescoring."""
    icp, _ = service.create_icp(
        seller_company_id="comp_seller",
        name="Cache ICP",
        target_industries=["Logistics"],
    )

    company = {
        "id": "comp_logistics_1",
        "company_name": "Freight Logistics",
        "industry": "Logistics",
    }

    score1 = service.score_company(icp_id=icp.id, company_data=company)
    score2 = service.score_company(icp_id=icp.id, company_data=company)

    assert score1.fingerprint == score2.fingerprint
    refresh_engine = ICPRefreshEngine()
    should_rescore = refresh_engine.should_rescore_company(score1, score2.fingerprint)
    assert not should_rescore


# ── Test 16: API Routes Verification ──

def test_api_routes_verification(tmp_db, monkeypatch):
    """Validates FastAPI endpoints for ICP creation, activation, and prospect scoring."""
    client = TestClient(app)

    # 1. Create ICP
    create_payload = {
        "seller_company_id": "comp_api_seller",
        "name": "API Test ICP",
        "description": "Created via FastAPI router",
        "target_industries": ["Finance", "Insurance"],
        "target_geographies": ["United States"],
        "target_employee_range": [50, 500],
        "activate": True,
    }
    resp = client.post("/v1/icps", json=create_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    icp_id = data["icp"]["id"]
    v1_id = data["version"]["id"]

    # 2. Get ICP
    get_resp = client.get(f"/v1/icps/{icp_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["icp"]["name"] == "API Test ICP"

    # 3. Create Draft Version
    ver_resp = client.post(
        f"/v1/icps/{icp_id}/versions",
        json={"target_industries": ["Finance", "Insurance", "Fintech"]},
    )
    assert ver_resp.status_code == 200
    v2_id = ver_resp.json()["id"]

    # 4. Activate Version
    act_resp = client.post(
        f"/v1/icps/{icp_id}/activate",
        json={"version_id": v2_id},
    )
    assert act_resp.status_code == 200
    assert act_resp.json()["status"] == ICPStatus.ACTIVE.value

    # 5. Score Company Fit
    score_resp = client.post(
        f"/v1/icps/{icp_id}/score/company/comp_fin_prospect",
        json={
            "company_data": {
                "id": "comp_fin_prospect",
                "industry": "Finance",
                "employee_count": 120,
                "country": "United States",
            }
        },
    )
    assert score_resp.status_code == 200
    score_data = score_resp.json()
    assert score_data["fit_score"] >= 0.7
    assert score_data["status"] in (FitStatus.STRONG_FIT.value, FitStatus.EXCELLENT_FIT.value)

    # 6. Query Matches
    matches_resp = client.get(f"/v1/icps/{icp_id}/matches?min_fit=0.5")
    assert matches_resp.status_code == 200
    matches = matches_resp.json()
    assert len(matches) >= 1

