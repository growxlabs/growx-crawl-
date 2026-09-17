"""
Phase 11 — Competitor Graph Tests.
Tests candidate discovery, multi-dimensional scoring, direct vs adjacent differentiation,
blocking rules (parent/subsidiary, supplier/customer), evidence, rejection memory,
graph queries, and API routes.
"""

import pytest
from fastapi.testclient import TestClient

from growx_crawl.identity.models import CompanyRelationshipEntity
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
    EvidenceType,
    ReasonCode,
    RelationshipStatus,
    RelationshipType,
)
from growx_crawl.intelligence.competitors.policies import (
    CompetitorVerificationPolicy,
    canonical_pair,
)
from growx_crawl.intelligence.competitors.refresh import CompetitorRefreshEngine
from growx_crawl.intelligence.competitors.repository import SqliteCompetitorRepository
from growx_crawl.intelligence.competitors.scoring import (
    calculate_confidence,
    calculate_customer_overlap,
    calculate_geography_overlap,
    calculate_market_overlap,
    calculate_offering_overlap,
    calculate_strength,
    classify_relationship_type,
)
from growx_crawl.intelligence.competitors.service import CompetitorGraphService
from growx_crawl.intelligence.competitors.verification import CompetitorVerifier
from growx_crawl.intelligence.facts.models import FactEntity
from growx_crawl.storage.db import get_db
from growx_crawl.storage.sqlite.canonical import init_sqlite_canonical_tables
from growx_crawl.web.app import app


@pytest.fixture
def tmp_db(tmp_path):
    db_file = str(tmp_path / "test_phase11.db")
    with get_db(db_file) as conn:
        init_sqlite_canonical_tables(conn)
    return db_file


@pytest.fixture
def comp_repo(tmp_db):
    return SqliteCompetitorRepository(db_path=tmp_db)


@pytest.fixture
def comp_service(comp_repo, tmp_db):
    prof_builder = CompetitiveProfileBuilder()
    cand_gen = CompetitorCandidateGenerator(db_path=tmp_db, profile_builder=prof_builder)
    return CompetitorGraphService(
        repository=comp_repo,
        profile_builder=prof_builder,
        candidate_generator=cand_gen,
    )


# ── Test 1: Candidate Generation from Facts ──

def test_candidate_generation_from_facts(comp_service, tmp_db):
    """Builds CompetitiveProfile from facts and identifies candidate companies."""
    # Seed known companies
    companies = [
        {
            "id": "cmp_acme",
            "canonical_name": "Acme Retail Jewellers",
            "industry": "Jewellery",
            "city": "Hyderabad",
            "country_code": "IN",
        },
        {
            "id": "cmp_zenith",
            "canonical_name": "Zenith Diamond Jewellery",
            "industry": "Jewellery",
            "city": "Hyderabad",
            "country_code": "IN",
        },
        {
            "id": "cmp_forge",
            "canonical_name": "Forge Cloud Software",
            "industry": "Software",
            "city": "Bengaluru",
            "country_code": "IN",
        },
    ]

    target_profile = CompetitiveProfile(
        company_id="cmp_acme",
        company_name="Acme Retail Jewellers",
        industries=["Jewellery"],
        products=["Gold Ornaments", "Bridal Jewellery"],
        geographies=["Hyderabad", "IN"],
    )

    candidates = comp_service.candidate_generator.generate_candidates(
        target_profile=target_profile,
        known_companies=companies,
    )

    # Zenith should be a candidate, Forge should not match industry
    cand_ids = [c.company_id for c in candidates]
    assert "cmp_zenith" in cand_ids
    assert "cmp_acme" not in cand_ids  # self excluded


# ── Test 2: Similarity is Not Proof (Core Principle §2) ──

def test_similarity_is_not_proof(comp_service):
    """Same industry alone with zero offering/customer overlap should NOT produce a verified competitor."""
    # Both in Jewellery, but one makes high-end bridal diamond rings, the other is an industrial gold refiner
    prof_a = CompetitiveProfile(
        company_id="cmp_retail_jewel",
        company_name="Retail Jeweller",
        industries=["Jewellery"],
        products=["Diamond Rings", "Necklaces"],
        target_customers=["Consumers", "Bridal Shoppers"],
        geographies=["Hyderabad"],
    )
    prof_b = CompetitiveProfile(
        company_id="cmp_gold_refiner",
        company_name="Industrial Gold Bullion Refiner",
        industries=["Jewellery"],
        products=["Raw Gold Ingots", "Assay Services"],
        target_customers=["Bullion Banks", "Minting Houses"],
        geographies=["Zurich"],
    )

    rel = comp_service.score_pair(
        company_a_id=prof_a.company_id,
        company_b_id=prof_b.company_id,
        profile_a=prof_a,
        profile_b=prof_b,
    )

    # Must NOT be verified
    assert rel.status != RelationshipStatus.VERIFIED.value
    # Strength should be low because customer and offering overlap are low/zero
    assert rel.strength < 0.40


# ── Test 3: Strength vs Confidence Separation (§18–19) ──

def test_strength_vs_confidence_separation():
    """Strength (overlap intensity) and Confidence (evidence certainty) are calculated separately."""
    prof_a = CompetitiveProfile(
        company_id="cmp_a",
        company_name="CRM Alpha",
        industries=["Software"],
        products=["Sales CRM", "Pipeline Management"],
        target_customers=["SMB Sales Teams"],
        geographies=["global"],
    )
    prof_b = CompetitiveProfile(
        company_id="cmp_b",
        company_name="CRM Beta",
        industries=["Software"],
        products=["Sales CRM", "Pipeline Management"],
        target_customers=["SMB Sales Teams"],
        geographies=["global"],
    )

    # High overlap
    m_overlap = calculate_market_overlap(prof_a, prof_b)
    o_overlap = calculate_offering_overlap(prof_a, prof_b)
    c_overlap = calculate_customer_overlap(prof_a, prof_b)
    g_overlap = calculate_geography_overlap(prof_a, prof_b)

    # 1. Zero external evidence
    strength_no_ev = calculate_strength(m_overlap, o_overlap, c_overlap, g_overlap, explicit_evidence_count=0)
    confidence_no_ev = calculate_confidence(evidence_list=[], profile_a_quality=1.0, profile_b_quality=1.0)

    assert strength_no_ev > 0.70  # Strong competitive overlap
    assert confidence_no_ev < 0.50  # But low confidence because unverified by external evidence

    # 2. With rich diverse evidence
    evidence = [
        CompetitorEvidenceEntity(
            id="cpe_001",
            relationship_id="cpr_test",
            evidence_type=EvidenceType.COMPARISON_PAGE.value,
            confidence=0.95,
        ),
        CompetitorEvidenceEntity(
            id="cpe_002",
            relationship_id="cpr_test",
            evidence_type=EvidenceType.REVIEW_PLATFORM.value,
            confidence=0.90,
        ),
    ]
    confidence_with_ev = calculate_confidence(evidence_list=evidence, profile_a_quality=1.0, profile_b_quality=1.0)
    assert confidence_with_ev > 0.75  # High confidence with multiple independent sources


# ── Test 4: Direct vs Adjacent Differentiation (§8) ──

def test_direct_vs_adjacent_differentiation():
    """Identifies direct vs adjacent competition accurately."""
    # Direct competitors: both sell jewelry ERP
    prof_erp1 = CompetitiveProfile(
        company_id="cmp_erp1",
        company_name="JewelERP Pro",
        industries=["Software", "Jewellery"],
        products=["Jewellery ERP", "Inventory Control"],
        target_customers=["Jewellery Retailers"],
        geographies=["global"],
    )
    prof_erp2 = CompetitiveProfile(
        company_id="cmp_erp2",
        company_name="GemsCloud ERP",
        industries=["Software", "Jewellery"],
        products=["Jewellery ERP", "Accounting and Stock"],
        target_customers=["Jewellery Retailers"],
        geographies=["global"],
    )

    m = calculate_market_overlap(prof_erp1, prof_erp2)
    o = calculate_offering_overlap(prof_erp1, prof_erp2)
    c = calculate_customer_overlap(prof_erp1, prof_erp2)
    g = calculate_geography_overlap(prof_erp1, prof_erp2)
    s = calculate_strength(m, o, c, g)
    rel_type_direct = classify_relationship_type(s, m, o, c, g)

    assert rel_type_direct == RelationshipType.DIRECT.value

    # Adjacent: same industry, but one sells ERP and the other sells Security Cameras
    prof_sec = CompetitiveProfile(
        company_id="cmp_sec",
        company_name="JewelVault Surveillance",
        industries=["Security", "Jewellery"],
        products=["Jewellery Store Cameras", "Safe Alarms"],
        target_customers=["Jewellery Retailers"],
        geographies=["global"],
    )

    m2 = calculate_market_overlap(prof_erp1, prof_sec)
    o2 = calculate_offering_overlap(prof_erp1, prof_sec)
    c2 = calculate_customer_overlap(prof_erp1, prof_sec)
    g2 = calculate_geography_overlap(prof_erp1, prof_sec)
    s2 = calculate_strength(m2, o2, c2, g2)
    rel_type_adjacent = classify_relationship_type(s2, m2, o2, c2, g2)

    assert rel_type_adjacent == RelationshipType.ADJACENT.value


# ── Test 5: Parent / Subsidiary Blocking Guard (§27–28) ──

def test_parent_subsidiary_blocking_guard(comp_service, tmp_db):
    """Existing parent/subsidiary relationship blocks competitor classification."""
    # Seed corporate relationship in identity table
    with get_db(tmp_db) as conn:
        conn.execute(
            """
            INSERT INTO canonical_companies (id, canonical_name, normalized_name, first_seen_at, last_seen_at, created_at, updated_at)
            VALUES (?, ?, ?, '2025-01-01T00:00:00Z', '2025-01-01T00:00:00Z', '2025-01-01T00:00:00Z', '2025-01-01T00:00:00Z')
            """,
            ("cmp_titan", "Titan Company Limited", "titan company limited"),
        )
        conn.execute(
            """
            INSERT INTO canonical_companies (id, canonical_name, normalized_name, first_seen_at, last_seen_at, created_at, updated_at)
            VALUES (?, ?, ?, '2025-01-01T00:00:00Z', '2025-01-01T00:00:00Z', '2025-01-01T00:00:00Z', '2025-01-01T00:00:00Z')
            """,
            ("cmp_tanishq", "Tanishq", "tanishq"),
        )
        conn.execute(
            """
            INSERT INTO canonical_company_relationships (id, from_company_id, to_company_id, relationship_type, first_seen_at, last_seen_at)
            VALUES (?, ?, ?, ?, '2025-01-01T00:00:00Z', '2025-01-01T00:00:00Z')
            """,
            ("rel_corp_001", "cmp_titan", "cmp_tanishq", "subsidiary"),
        )

    prof_titan = CompetitiveProfile(
        company_id="cmp_titan",
        company_name="Titan Company Limited",
        industries=["Jewellery", "Watches"],
        products=["Jewellery", "Watches"],
    )
    prof_tanishq = CompetitiveProfile(
        company_id="cmp_tanishq",
        company_name="Tanishq",
        industries=["Jewellery"],
        products=["Gold Jewellery", "Diamond Jewellery"],
    )

    rel = comp_service.score_pair(
        company_a_id="cmp_titan",
        company_b_id="cmp_tanishq",
        profile_a=prof_titan,
        profile_b=prof_tanishq,
    )

    # Must be rejected due to parent/subsidiary
    assert rel.status == RelationshipStatus.REJECTED.value
    assert ReasonCode.PARENT_RELATIONSHIP_CONFLICT.value in rel.reasons


# ── Test 6: Supplier / Customer Blocking Guard (§29) ──

def test_supplier_customer_blocking_guard(comp_service, tmp_db):
    """Supplier/customer relationship blocks competitor classification."""
    with get_db(tmp_db) as conn:
        conn.execute(
            """
            INSERT INTO canonical_companies (id, canonical_name, normalized_name, first_seen_at, last_seen_at, created_at, updated_at)
            VALUES (?, ?, ?, '2025-01-01T00:00:00Z', '2025-01-01T00:00:00Z', '2025-01-01T00:00:00Z', '2025-01-01T00:00:00Z')
            """,
            ("cmp_vendor", "Vendor Tools", "vendor tools"),
        )
        conn.execute(
            """
            INSERT INTO canonical_companies (id, canonical_name, normalized_name, first_seen_at, last_seen_at, created_at, updated_at)
            VALUES (?, ?, ?, '2025-01-01T00:00:00Z', '2025-01-01T00:00:00Z', '2025-01-01T00:00:00Z', '2025-01-01T00:00:00Z')
            """,
            ("cmp_client", "Client Co", "client co"),
        )
        conn.execute(
            """
            INSERT INTO canonical_company_relationships (id, from_company_id, to_company_id, relationship_type, first_seen_at, last_seen_at)
            VALUES (?, ?, ?, ?, '2025-01-01T00:00:00Z', '2025-01-01T00:00:00Z')
            """,
            ("rel_corp_002", "cmp_vendor", "cmp_client", "supplier"),
        )

    prof_vendor = CompetitiveProfile(company_id="cmp_vendor", company_name="Vendor Tools", industries=["Software"])
    prof_client = CompetitiveProfile(company_id="cmp_client", company_name="Client Co", industries=["Software"])

    rel = comp_service.score_pair(
        company_a_id="cmp_vendor",
        company_b_id="cmp_client",
        profile_a=prof_vendor,
        profile_b=prof_client,
    )

    assert rel.status == RelationshipStatus.REJECTED.value
    assert ReasonCode.SUPPLIER_RELATIONSHIP_CONFLICT.value in rel.reasons


# ── Test 7: Regional Competitor Detection (§8, §17) ──

def test_regional_competitor_detection():
    """Identifies competition confined to specific regions."""
    prof_hyd = CompetitiveProfile(
        company_id="cmp_hyd",
        company_name="Hyderabad Sweets",
        industries=["Food"],
        products=["Traditional Sweets", "Namkeen"],
        geographies=["Hyderabad"],
    )
    prof_del = CompetitiveProfile(
        company_id="cmp_del",
        company_name="Delhi Sweets",
        industries=["Food"],
        products=["Traditional Sweets", "Namkeen"],
        geographies=["Delhi"],
    )

    m = calculate_market_overlap(prof_hyd, prof_del)
    o = calculate_offering_overlap(prof_hyd, prof_del)
    c = calculate_customer_overlap(prof_hyd, prof_del)
    g = calculate_geography_overlap(prof_hyd, prof_del)  # 0.0 or disjoint
    s = calculate_strength(m, o, c, g)

    # In different regions with high offering overlap
    # If geography is localized and disjoint
    assert g == 0.0


# ── Test 8: Explicit Evidence Boost (§22) ──

def test_explicit_evidence_boost(comp_service):
    """Presence of comparison page evidence elevates status and adds reasons."""
    prof_a = CompetitiveProfile(
        company_id="cmp_soft1",
        company_name="AppOne",
        industries=["CRM"],
        products=["Lead Management"],
        geographies=["global"],
    )
    prof_b = CompetitiveProfile(
        company_id="cmp_soft2",
        company_name="AppTwo",
        industries=["CRM"],
        products=["Lead Management"],
        geographies=["global"],
    )

    evidence = [
        CompetitorEvidenceEntity(
            id="cpe_comp_page",
            relationship_id="",
            evidence_type=EvidenceType.COMPARISON_PAGE.value,
            confidence=0.95,
        )
    ]

    rel = comp_service.score_pair(
        company_a_id="cmp_soft1",
        company_b_id="cmp_soft2",
        profile_a=prof_a,
        profile_b=prof_b,
        evidence_list=evidence,
    )

    assert rel.status == RelationshipStatus.VERIFIED.value
    assert ReasonCode.EXPLICIT_COMPARISON.value in rel.reasons
    assert rel.evidence_count == 1


# ── Test 9: Pair Canonicalization and Idempotency (§54–56) ──

def test_pair_canonicalization_and_idempotency(comp_service):
    """canonical_pair is symmetric and repeated scoring updates rather than duplicates."""
    assert canonical_pair("cmp_aaa", "cmp_bbb") == "cmp_aaa:cmp_bbb"
    assert canonical_pair("cmp_bbb", "cmp_aaa") == "cmp_aaa:cmp_bbb"

    prof_a = CompetitiveProfile(company_id="cmp_aaa", company_name="AAA Co", industries=["Tech"])
    prof_b = CompetitiveProfile(company_id="cmp_bbb", company_name="BBB Co", industries=["Tech"])

    rel1 = comp_service.score_pair("cmp_aaa", "cmp_bbb", prof_a, prof_b)
    rel2 = comp_service.score_pair("cmp_bbb", "cmp_aaa", prof_a, prof_b)

    # Should have same ID and canonical pair
    assert rel1.id == rel2.id
    assert rel1.canonical_pair == "cmp_aaa:cmp_bbb"

    # In database, only one record should exist for this canonical pair
    stored = comp_service.repository.get_relationship_by_pair("cmp_aaa:cmp_bbb")
    assert stored is not None
    assert stored.id == rel1.id


# ── Test 10: Rejection Memory (§57) ──

def test_rejection_memory(comp_service, tmp_db):
    """Explicitly rejected pairs are stored in competitor_rejections and skipped."""
    pair_key = canonical_pair("cmp_rej1", "cmp_rej2")
    comp_service.repository.save_rejection(
        CompetitorRejectionEntity(
            canonical_pair=pair_key,
            company_a="cmp_rej1",
            company_b="cmp_rej2",
            reason_code=ReasonCode.PARENT_RELATIONSHIP_CONFLICT.value,
        )
    )

    assert comp_service.repository.is_rejected(pair_key) is True

    # Candidate generator should skip rejected pairs
    target = CompetitiveProfile(company_id="cmp_rej1", company_name="Rej One", industries=["Retail"])
    pool = [{"id": "cmp_rej2", "canonical_name": "Rej Two", "industry": "Retail"}]
    candidates = comp_service.candidate_generator.generate_candidates(
        target_profile=target,
        rejection_check_fn=comp_service.repository.is_rejected,
        known_companies=pool,
    )
    assert len(candidates) == 0


# ── Test 11: Machine-Readable Explanations (§59–60) ──

def test_machine_readable_explanations():
    """Generates expected machine-readable ReasonCodes."""
    reasons = CompetitorExplainer.generate_reasons(
        market_overlap=0.8,
        offering_overlap=0.7,
        customer_overlap=0.6,
        geography_overlap=0.9,
    )
    assert ReasonCode.SAME_MARKET.value in reasons
    assert ReasonCode.OFFERING_OVERLAP.value in reasons
    assert ReasonCode.SAME_CUSTOMER_SEGMENT.value in reasons
    assert ReasonCode.GEOGRAPHY_OVERLAP.value in reasons


# ── Test 12: Graph Traversal Depth 1 and 2 (§36–37) ──

def test_graph_traversal(comp_service):
    """Graph traversal returns nodes and edges at specified depth."""
    # Seed A-B and B-C
    prof_a = CompetitiveProfile(company_id="cmp_g_a", company_name="Node A", industries=["SaaS"], products=["App"])
    prof_b = CompetitiveProfile(company_id="cmp_g_b", company_name="Node B", industries=["SaaS"], products=["App"])
    prof_c = CompetitiveProfile(company_id="cmp_g_c", company_name="Node C", industries=["SaaS"], products=["App"])

    comp_service.score_pair("cmp_g_a", "cmp_g_b", prof_a, prof_b)
    comp_service.score_pair("cmp_g_b", "cmp_g_c", prof_b, prof_c)

    # Depth 1 from A: should contain A and B
    g1 = comp_service.get_graph("cmp_g_a", depth=1)
    node_ids_1 = {n["id"] for n in g1["nodes"]}
    assert "cmp_g_a" in node_ids_1
    assert "cmp_g_b" in node_ids_1
    assert "cmp_g_c" not in node_ids_1

    # Depth 2 from A: should expand through B to include C
    g2 = comp_service.get_graph("cmp_g_a", depth=2)
    node_ids_2 = {n["id"] for n in g2["nodes"]}
    assert "cmp_g_c" in node_ids_2


# ── Test 13: Substitute Competition Type (§8) ──

def test_substitute_competition_type():
    """Different offering solving same buying problem classified as substitute."""
    rel_type = classify_relationship_type(
        strength=0.35,
        market_overlap=0.50,
        offering_overlap=0.10,
        customer_overlap=0.30,
        geography_overlap=0.80,
    )
    assert rel_type == RelationshipType.SUBSTITUTE.value


# ── Test 14: Company Competitor Summary (§44) ──

def test_company_competitor_summary(comp_service):
    """Denormalized summary is correctly saved and retrieved."""
    comp_service.discover(
        company_id="cmp_sum_target",
        company_data={"canonical_name": "Sum Target", "industry": "Jewellery"},
        known_companies=[
            {"id": "cmp_sum_c1", "canonical_name": "Comp 1", "industry": "Jewellery"},
            {"id": "cmp_sum_c2", "canonical_name": "Comp 2", "industry": "Jewellery"},
        ],
    )

    summary = comp_service.get_company_summary("cmp_sum_target")
    assert summary is not None
    assert summary.company_id == "cmp_sum_target"
    assert summary.competitor_count == 2
    assert summary.last_refreshed_at is not None


# ── Test 15: Refresh Engine Staleness (§40) ──

def test_refresh_engine_staleness(comp_service):
    """RefreshEngine detects when facts or age require refresh."""
    ref_engine = comp_service.refresh_engine
    assert ref_engine.fact_change_impacts_competition("company.product") is True
    assert ref_engine.fact_change_impacts_competition("company.email") is False

    # Stale summary
    stale_summary = CompanyCompetitorSummary(
        company_id="cmp_stale",
        last_refreshed_at="2025-01-01T00:00:00Z",
    )
    assert ref_engine.should_refresh(stale_summary, max_age_days=90) is True


# ── Test 16: API Endpoints Verification (§61) ──

def test_competitor_api_endpoints():
    """Validates FastAPI competitor routes."""
    client = TestClient(app)

    # 1. Discover endpoint
    resp = client.post(
        "/v1/companies/cmp_api_test/competitors/discover",
        json={"max_candidates": 10, "verify_top": 5},
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

    # 2. Competitors query endpoint
    resp2 = client.get("/v1/companies/cmp_api_test/competitors")
    assert resp2.status_code == 200
    assert isinstance(resp2.json(), list)

    # 3. Graph endpoint
    resp3 = client.get("/v1/companies/cmp_api_test/competitors/graph?depth=1")
    assert resp3.status_code == 200
    data = resp3.json()
    assert "nodes" in data
    assert "edges" in data
