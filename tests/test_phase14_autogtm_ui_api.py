"""
Phase 14 Test Suite: AutoGTM Product UI Backend Engine.
Tests all Phase 14 REST API endpoints for:
- Projects CRUD, overview metrics, prospect queue, contacts, and activity stream
- Seller overview, capability analysis, competitor graph, and temporal history
- Prospect detail scorecards, why-reasons, signals, reverify, and deep research
- Manual fact correction override and evidence inspector queries
- Global intelligence explorer catalogs
- Background job tracking and seed environment
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from growx_crawl.api.v1.router import v1_router
from growx_crawl.autogtm.seed import seed_canonical_environment
from growx_crawl.autogtm.projects import project_service, ProjectEntity


@pytest.fixture(scope="module")
def api_client():
    app = FastAPI()
    app.include_router(v1_router, prefix="/v1")
    # Seed canonical test environment
    seed_canonical_environment()
    client = TestClient(app)
    return client


# ── Test 1: Seed Environment API ──
def test_seed_canonical_environment_endpoint(api_client):
    res = api_client.post("/v1/seed")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["seeded", "ok"]
    assert "seller_company_id" in data
    assert "project_id" in data
    assert data["prospects_count"] >= 5


# ── Test 2: Projects CRUD & Overview API ──
def test_projects_crud_and_metrics(api_client):
    # 1. Create a project
    create_res = api_client.post("/v1/projects", json={
        "name": "Fintech Outbound Q3",
        "description": "Targeting US mid-market payment gateways.",
        "seller_company_id": "cmp_seller_growxlabs",
        "icp_id": "icp_us_midmarket_saas",
    })
    assert create_res.status_code == 200
    proj_data = create_res.json()
    assert proj_data["id"].startswith("prj_")
    assert proj_data["name"] == "Fintech Outbound Q3"
    proj_id = proj_data["id"]

    # 2. Get project by ID
    get_res = api_client.get(f"/v1/projects/{proj_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Fintech Outbound Q3"

    # 3. Patch project
    patch_res = api_client.patch(f"/v1/projects/{proj_id}", json={
        "name": "Fintech Outbound Q3 Updated",
        "status": "draft",
    })
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "Fintech Outbound Q3 Updated"
    assert patch_res.json()["status"] == "draft"

    # 4. List all projects
    list_res = api_client.get("/v1/projects")
    assert list_res.status_code == 200
    projs = list_res.json()
    assert any(p["id"] == proj_id for p in projs)

    # 5. Get project overview metrics
    metrics_res = api_client.get(f"/v1/projects/{proj_id}/overview")
    assert metrics_res.status_code == 200
    metrics = metrics_res.json()
    assert "total_accounts" in metrics
    assert "priority_accounts" in metrics
    assert "average_icp_fit" in metrics

    # 6. Get project prospects
    prospects_res = api_client.get(f"/v1/projects/{proj_id}/prospects")
    assert prospects_res.status_code == 200
    assert isinstance(prospects_res.json(), list)

    # 7. Get project people
    people_res = api_client.get(f"/v1/projects/{proj_id}/people")
    assert people_res.status_code == 200
    assert isinstance(people_res.json(), list)

    # 8. Get project activity stream
    act_res = api_client.get(f"/v1/projects/{proj_id}/activity")
    assert act_res.status_code == 200
    assert isinstance(act_res.json(), list)


# ── Test 3: Seller Intelligence API ──
def test_seller_endpoints(api_client):
    # 1. Overview
    overview_res = api_client.get("/v1/seller/overview")
    assert overview_res.status_code == 200
    ov = overview_res.json()
    assert "company_name" in ov
    assert "domain" in ov
    assert ov["verified_facts_count"] > 0

    # 2. Analysis
    analysis_res = api_client.get("/v1/seller/analysis")
    assert analysis_res.status_code == 200
    an = analysis_res.json()
    assert "positioning" in an
    assert len(an["value_props"]) >= 1
    assert len(an["target_buyer_roles"]) >= 1

    # 3. Trigger seller re-analysis job
    analyze_job_res = api_client.post("/v1/seller/analyze")
    assert analyze_job_res.status_code == 200
    job_data = analyze_job_res.json()
    assert "job_id" in job_data
    assert job_data["status"] in ["running", "completed", "started"]

    # 4. Competitors
    comp_res = api_client.get("/v1/seller/competitors")
    assert comp_res.status_code == 200
    comps = comp_res.json()
    assert len(comps) >= 2
    assert any("Apollo" in c["competitor_name"] or "ZoomInfo" in c["competitor_name"] for c in comps)

    # 5. History
    hist_res = api_client.get("/v1/seller/history")
    assert hist_res.status_code == 200
    events = hist_res.json()
    assert len(events) >= 1


# ── Test 4: Prospect Detail, Actions & Bulk API ──
def test_prospect_detail_and_actions(api_client):
    # 1. Retrieve prospect ID from seeded project
    prospects_res = api_client.get("/v1/projects/prj_us_saas_expansion/prospects")
    assert prospects_res.status_code == 200
    prospects = prospects_res.json()
    assert len(prospects) > 0
    target_p = prospects[0]
    prospect_id = target_p["prospect_id"]

    # 2. Detail
    detail_res = api_client.get(f"/v1/prospects/{prospect_id}/detail")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert "company_name" in detail
    assert detail["rank_tier"].lower() in ["priority", "strong", "possible", "reverify", "research_more", "research more"]
    assert detail["final_score"] > 0.0
    assert len(detail["why_reasons"]) > 0
    assert len(detail["people"]) >= 1
    assert len(detail["verified_facts"]) >= 1

    # 3. Fallback check using cmp_linear or psp_linear directly
    fallback_res = api_client.get("/v1/prospects/cmp_linear/detail")
    assert fallback_res.status_code == 200
    assert fallback_res.json()["company_name"] == "Linear"

    # 4. Trigger reverify
    reverify_res = api_client.post(f"/v1/prospects/{prospect_id}/reverify")
    assert reverify_res.status_code == 200
    rev_job = reverify_res.json()
    assert "job_id" in rev_job
    assert rev_job["status"] == "started"

    # 5. Trigger research
    research_res = api_client.post(f"/v1/prospects/{prospect_id}/research")
    assert research_res.status_code == 200
    res_job = research_res.json()
    assert "job_id" in res_job
    assert res_job["status"] == "started"

    # 6. Bulk action
    bulk_res = api_client.post("/v1/prospects/bulk-action", json={
        "action": "reverify",
        "prospect_ids": [prospect_id, "psp_retool"],
    })
    assert bulk_res.status_code == 200
    bulk_job = bulk_res.json()
    assert "job_id" in bulk_job
    assert bulk_job["action"] == "reverify"


# ── Test 5: Fact Override & Evidence API ──
def test_fact_correction_and_evidence(api_client):
    # 1. Fact correction
    correction_res = api_client.post("/v1/facts/correct", json={
        "company_id": "cmp_linear",
        "field_name": "employee_count_range",
        "corrected_value": "100-250",
        "reason": "Team page update shows headcount increase.",
        "source_url": "https://linear.app/about",
    })
    assert correction_res.status_code == 200
    corr_data = correction_res.json()
    assert corr_data["status"] == "applied"
    assert corr_data["field_name"] == "employee_count_range"

    # 2. Get evidence record
    evidence_res = api_client.get("/v1/evidence/evi_linear_hq")
    assert evidence_res.status_code == 200
    evi = evidence_res.json()
    assert evi["evidence_id"] == "evi_linear_hq"
    assert "San Francisco" in evi["raw_snippet"]


# ── Test 6: Global Intelligence Catalog API ──
def test_intelligence_catalog_endpoints(api_client):
    # 1. Intelligence Overview
    ov_res = api_client.get("/v1/intelligence/overview")
    assert ov_res.status_code == 200
    ov = ov_res.json()
    assert ov["total_companies"] >= 5
    assert ov["total_people"] >= 5
    assert ov["total_facts"] >= 10

    # 2. Search companies
    companies_res = api_client.get("/v1/intelligence/companies?query=Linear")
    assert companies_res.status_code == 200
    comps = companies_res.json()
    assert any(c["name"] == "Linear" for c in comps)

    # 3. Search people
    people_res = api_client.get("/v1/intelligence/people?query=Karri")
    assert people_res.status_code == 200
    people = people_res.json()
    assert any("Karri" in p["full_name"] for p in people)

    # 4. Search signals
    signals_res = api_client.get("/v1/intelligence/signals")
    assert signals_res.status_code == 200
    signals = signals_res.json()
    assert len(signals) >= 1


# ── Test 7: Background Jobs API ──
def test_jobs_list(api_client):
    res = api_client.get("/v1/jobs")
    assert res.status_code == 200
    data = res.json()
    jobs = data if isinstance(data, list) else data.get("jobs", [])
    assert isinstance(jobs, list)
