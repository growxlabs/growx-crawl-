"""
Phase 13 Test Suite: Prospect Ranking Engine.
Tests multidimensional separation, account/person scoring, recency decay,
hard blocks, workflow states (REVERIFY, RESEARCH_MORE), confidence calibration,
pairwise ranking, ranking profiles, account-first queue, and API endpoints.
"""

import os
import tempfile
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from growx_crawl.scoring.models import (
    ProspectStatus,
    RankingReasonCode,
    RankingStatus,
    ScoreComponentType,
)
from growx_crawl.scoring.profiles import BUILTIN_PROFILES, RankingProfileConfig
from growx_crawl.scoring.prospect_ranker import ProspectRanker
from growx_crawl.scoring.repository import SqliteRankingRepository
from growx_crawl.scoring.service import ProspectRankingService
from growx_crawl.scoring.account_score import AccountScoreCalculator
from growx_crawl.scoring.person_score import PersonScoreCalculator
from growx_crawl.scoring.signal_score import SignalScoreCalculator
from growx_crawl.scoring.timing_score import TimingScoreCalculator
from growx_crawl.scoring.contactability import ContactabilityCalculator
from growx_crawl.scoring.freshness_score import FreshnessScoreCalculator
from growx_crawl.shared.time import utc_iso_now


@pytest.fixture
def temp_repo():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    repo = SqliteRankingRepository(db_path=db_path)
    yield repo
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def ranking_service(temp_repo):
    service = ProspectRankingService(repository=temp_repo)
    return service


@pytest.fixture
def ranker():
    return ProspectRanker()


# ── Test 1: Multidimensional Component Separation ──
def test_multidimensional_component_separation(ranker):
    """Verifies account, person, signal, timing, contactability, and penalties are calculated separately."""
    company_data = {
        "id": "cmp_acme",
        "company_name": "Acme Corp",
        "industry": "Software",
        "employee_count": 250,
        "is_verified": True,
        "quality_gate_passed": True,
    }
    person_data = {
        "id": "prs_jane",
        "name": "Jane Doe",
        "title": "VP of Engineering",
        "seniority": "vp",
        "email": "jane@acme.com",
        "is_suppressed": False,
        "employment_confidence": 0.95,
    }
    signals = [
        {"signal_type": "expansion", "name": "Hiring surge", "confidence": 0.9, "detected_at": utc_iso_now()}
    ]

    score, explanations = ranker.rank_prospect(
        prospect_id="prsp_001",
        company_data=company_data,
        person_data=person_data,
        signals=signals,
        icp_score=0.85,
    )

    # Multi-dimensional separation
    assert score.account_score > 0.0
    assert score.person_score > 0.0
    assert score.signal_score > 0.0
    assert score.timing_score > 0.0
    assert score.contactability_score > 0.0
    assert score.raw_score > 0.0
    assert score.final_score > 0.0
    assert len(explanations) > 0


# ── Test 2: Account Score Calculation ──
def test_account_score_calculation():
    """Verifies account score incorporates ICP fit, verification, quality, and momentum."""
    calc = AccountScoreCalculator()
    high_acc = calc.calculate(
        company_data={
            "id": "cmp_1",
            "is_verified": True,
            "quality_gate_passed": True,
            "growth_rate": 0.25,
        },
        icp_score=0.9,
    )
    low_acc = calc.calculate(
        company_data={
            "id": "cmp_2",
            "is_verified": False,
            "quality_gate_passed": False,
        },
        icp_score=0.4,
    )

    assert high_acc.score > low_acc.score
    assert high_acc.icp_fit == 0.9
    assert high_acc.verification_score > low_acc.verification_score
    assert RankingReasonCode.HIGH_ICP_FIT.value in high_acc.reason_codes


# ── Test 3: Person Score & Seniority Weighting ──
def test_person_score_and_seniority_weighting():
    """Verifies VP/Director scores higher than entry-level/intern under same persona fit."""
    calc = PersonScoreCalculator()
    vp_person = {
        "id": "prs_vp",
        "title": "Vice President of Sales",
        "seniority": "vp",
        "persona_match_score": 0.8,
        "employment_confidence": 0.9,
    }
    intern_person = {
        "id": "prs_intern",
        "title": "Sales Intern",
        "seniority": "intern",
        "persona_match_score": 0.8,
        "employment_confidence": 0.9,
    }

    vp_res = calc.calculate(vp_person)
    intern_res = calc.calculate(intern_person)

    assert vp_res.score > intern_res.score
    assert vp_res.seniority_score > intern_res.seniority_score


# ── Test 4: Signal Score Diminishing Returns & Conflicts ──
def test_signal_score_diminishing_returns():
    """Verifies multiple signals combine with diminishing returns without unbounded linear increase."""
    calc = SignalScoreCalculator()
    signals_one = [{"signal_type": "expansion", "confidence": 0.8}]
    signals_many = [
        {"signal_type": "expansion", "confidence": 0.8},
        {"signal_type": "funding", "confidence": 0.8},
        {"signal_type": "hiring_spike", "confidence": 0.8},
        {"signal_type": "tech_adoption", "confidence": 0.8},
    ]

    res_one = calc.calculate(signals_one)
    res_many = calc.calculate(signals_many)

    assert res_many.score > res_one.score
    assert res_many.score <= 1.0  # Normalized ceiling
    assert res_many.score < (res_one.score * 4)


# ── Test 5: Timing Recency Decay ──
def test_timing_recency_decay():
    """Verifies recent signals score significantly higher than aged signals (>90d, >180d)."""
    calc = TimingScoreCalculator()
    now = datetime.now(timezone.utc)
    fresh_date = (now - timedelta(days=5)).isoformat()
    old_date = (now - timedelta(days=120)).isoformat()
    ancient_date = (now - timedelta(days=250)).isoformat()

    fresh_signals = [{"detected_at": fresh_date, "confidence": 0.9}]
    old_signals = [{"detected_at": old_date, "confidence": 0.9}]
    ancient_signals = [{"detected_at": ancient_date, "confidence": 0.9}]

    fresh_res = calc.calculate(fresh_signals)
    old_res = calc.calculate(old_signals)
    ancient_res = calc.calculate(ancient_signals)

    assert fresh_res.score > old_res.score
    assert old_res.score > ancient_res.score


# ── Test 6: Contactability & Role Mailbox Penalties ──
def test_contactability_and_role_mailbox_penalty():
    """Verifies direct corporate email gets top score, while role mailbox and catch-all get penalized."""
    calc = ContactabilityCalculator()
    direct_person = {"email": "alex@company.com", "is_suppressed": False}
    role_person = {"email": "info@company.com", "is_suppressed": False}
    catchall_company = {"email": "alex@catchall.com", "is_catch_all": True}

    direct_res = calc.calculate(person_data=direct_person)
    role_res = calc.calculate(person_data=role_person)
    catchall_res = calc.calculate(person_data=catchall_company, company_data=catchall_company)

    assert direct_res.score > role_res.score
    assert RankingReasonCode.ROLE_MAILBOX_PENALTY.value in role_res.reason_codes
    assert RankingReasonCode.CATCH_ALL_PENALTY.value in catchall_res.reason_codes


# ── Test 7: Hard Block Suppression ──
def test_hard_block_suppression(ranker):
    """Verifies suppressed contact is hard-blocked to NOT_ELIGIBLE with score 0.0."""
    company_data = {"id": "cmp_1", "company_name": "Acme"}
    person_data = {"id": "prs_1", "email": "optout@acme.com", "is_suppressed": True}

    score, exps = ranker.rank_prospect(
        prospect_id="prsp_suppressed",
        company_data=company_data,
        person_data=person_data,
        icp_score=0.99,
    )

    assert score.status == RankingStatus.NOT_ELIGIBLE.value
    assert score.final_score == 0.0
    assert any(e.reason_code == RankingReasonCode.SUPPRESSED_CONTACT.value for e in exps)


# ── Test 8: Hard Block Competitor Exclusion ──
def test_hard_block_competitor_exclusion(ranker):
    """Verifies seller competitor is hard-blocked regardless of high ICP fit."""
    company_data = {"id": "cmp_rival", "company_name": "Rival Tech", "is_competitor": True}

    score, exps = ranker.rank_prospect(
        prospect_id="prsp_comp",
        company_data=company_data,
        is_competitor=True,
        icp_score=0.95,
    )

    assert score.status == RankingStatus.NOT_ELIGIBLE.value
    assert score.final_score == 0.0
    assert any(e.reason_code == RankingReasonCode.COMPETITOR_EXCLUDED.value for e in exps)


# ── Test 9: Hard Block Invalid Email ──
def test_hard_block_invalid_email(ranker):
    """Verifies invalid email format yields NOT_ELIGIBLE and score 0.0."""
    company_data = {"id": "cmp_1"}
    person_data = {"id": "prs_1", "email": "not-an-email"}

    score, exps = ranker.rank_prospect(
        prospect_id="prsp_invalid_email",
        company_data=company_data,
        person_data=person_data,
        icp_score=0.85,
    )

    assert score.status == RankingStatus.NOT_ELIGIBLE.value
    assert score.final_score == 0.0
    assert any(e.reason_code == RankingReasonCode.INVALID_EMAIL.value for e in exps)


# ── Test 10: Workflow State REVERIFY ──
def test_workflow_state_reverify(ranker):
    """Verifies high fit with stale data (>180d employment or >270d company) sets status to REVERIFY."""
    company_data = {
        "id": "cmp_1",
        "company_name": "Stale Corp",
        "last_verified_at": (datetime.now(timezone.utc) - timedelta(days=300)).isoformat(),
        "is_verified": True,
    }
    person_data = {
        "id": "prs_1",
        "name": "Old Hire",
        "email": "hire@stale.com",
        "employment_verified_at": (datetime.now(timezone.utc) - timedelta(days=200)).isoformat(),
    }

    score, _ = ranker.rank_prospect(
        prospect_id="prsp_stale",
        company_data=company_data,
        person_data=person_data,
        icp_score=0.85,
    )

    assert score.status == RankingStatus.REVERIFY.value
    assert score.final_score > 0.0


# ── Test 11: Workflow State RESEARCH_MORE ──
def test_workflow_state_research_more(ranker):
    """Verifies promising fit but sparse data / unverified role yields RESEARCH_MORE."""
    company_data = {
        "id": "cmp_sparse",
        "company_name": "Sparse Inc",
        "is_verified": False,
        "quality_gate_passed": False,
    }
    person_data = {
        "id": "prs_sparse",
        "name": "Unknown Person",
        "employment_confidence": 0.4,
    }

    score, _ = ranker.rank_prospect(
        prospect_id="prsp_sparse",
        company_data=company_data,
        person_data=person_data,
        icp_score=0.65,
        signals=[],
    )

    assert score.status in (RankingStatus.RESEARCH_MORE.value, RankingStatus.POSSIBLE.value)


# ── Test 12: Confidence Factor Calibration ──
def test_confidence_factor_calibration(ranker):
    """Verifies low verification confidence attenuates final_score while preserving raw_score."""
    company_verified = {
        "id": "cmp_v",
        "company_name": "Verified Co",
        "is_verified": True,
        "quality_gate_passed": True,
    }
    company_unverified = {
        "id": "cmp_u",
        "company_name": "Unverified Co",
        "is_verified": False,
        "quality_gate_passed": False,
    }

    score_v, _ = ranker.rank_prospect("prsp_v", company_data=company_verified, icp_score=0.8)
    score_u, _ = ranker.rank_prospect("prsp_u", company_data=company_unverified, icp_score=0.8)

    assert score_v.confidence_factor > score_u.confidence_factor
    assert score_v.final_score > score_u.final_score
    assert score_u.raw_score > 0.0
    assert score_u.final_score == pytest.approx(score_u.raw_score * score_u.confidence_factor, abs=1e-2)


# ── Test 13: Pairwise Ranking Deterministic ──
def test_pairwise_ranking_deterministic(ranker):
    """Candidate A (High ICP, direct email, strong signals) ranks above Candidate B (Low ICP, stale)."""
    cand_a = {
        "prospect_id": "prsp_alpha",
        "company_data": {"id": "cmp_a", "is_verified": True, "quality_gate_passed": True},
        "person_data": {"id": "prs_a", "email": "a@cmp.com", "seniority": "vp", "title": "VP"},
        "signals": [{"signal_type": "funding", "confidence": 0.9, "detected_at": utc_iso_now()}],
        "icp_score": 0.92,
    }
    cand_b = {
        "prospect_id": "prsp_beta",
        "company_data": {"id": "cmp_b", "is_verified": False},
        "person_data": {"id": "prs_b", "email": "b@other.com", "seniority": "intern"},
        "signals": [],
        "icp_score": 0.35,
    }

    scored_batch = ranker.rank_batch([cand_b, cand_a])

    assert len(scored_batch) == 2
    first_score, _ = scored_batch[0]
    second_score, _ = scored_batch[1]

    assert first_score.prospect_id == "prsp_alpha"
    assert first_score.rank_position == 1
    assert second_score.prospect_id == "prsp_beta"
    assert second_score.rank_position == 2
    assert first_score.final_score > second_score.final_score


# ── Test 14: Profile Sensitivity and Comparison ──
def test_profile_sensitivity_and_comparison(ranking_service):
    """Compares default_v1 vs high_intent_v1 profiles for intent-heavy prospect."""
    company_data = {"id": "cmp_intent", "company_name": "Intent Heavy Co", "is_verified": True}
    signals = [
        {"signal_type": "high_intent", "confidence": 0.95, "detected_at": utc_iso_now()},
        {"signal_type": "expansion", "confidence": 0.90, "detected_at": utc_iso_now()},
    ]

    diff = ranking_service.compare_profiles(
        prospect_id="prsp_intent_test",
        company_data=company_data,
        signals=signals,
        icp_score=0.75,
        profile_a="default_v1",
        profile_b="high_intent_v1",
    )

    assert "profile_a" in diff
    assert "profile_b" in diff
    assert diff["profile_b"]["final_score"] >= diff["profile_a"]["final_score"]
    assert "score_delta" in diff


# ── Test 15: Account-First Queue Generation ──
def test_account_first_queue_generation(ranking_service):
    """Verifies account-first ranking limits top contacts per account and properly groups."""
    candidates = [
        {
            "prospect_id": "p_a1",
            "company_data": {"id": "cmp_a", "company_name": "Company A", "is_verified": True},
            "person_data": {"id": "prs_a1", "title": "VP Sales", "seniority": "vp", "email": "a1@a.com"},
            "icp_score": 0.9,
        },
        {
            "prospect_id": "p_a2",
            "company_data": {"id": "cmp_a", "company_name": "Company A", "is_verified": True},
            "person_data": {"id": "prs_a2", "title": "Director Eng", "seniority": "director", "email": "a2@a.com"},
            "icp_score": 0.9,
        },
        {
            "prospect_id": "p_a3",
            "company_data": {"id": "cmp_a", "company_name": "Company A", "is_verified": True},
            "person_data": {"id": "prs_a3", "title": "Lead Dev", "seniority": "lead", "email": "a3@a.com"},
            "icp_score": 0.9,
        },
        {
            "prospect_id": "p_a4",
            "company_data": {"id": "cmp_a", "company_name": "Company A", "is_verified": True},
            "person_data": {"id": "prs_a4", "title": "Intern", "seniority": "intern", "email": "a4@a.com"},
            "icp_score": 0.9,
        },
        {
            "prospect_id": "p_b1",
            "company_data": {"id": "cmp_b", "company_name": "Company B", "is_verified": True},
            "person_data": {"id": "prs_b1", "title": "VP Product", "seniority": "vp", "email": "b1@b.com"},
            "icp_score": 0.8,
        },
    ]

    ranked_queue = ranking_service.rank_account_first(
        candidates=candidates,
        profile_id="account_first_v1",
        max_people_per_account=2,
    )

    assert len(ranked_queue) == 3
    cmp_a_scores = [s for s in ranked_queue if s.company_id == "cmp_a"]
    cmp_b_scores = [s for s in ranked_queue if s.company_id == "cmp_b"]
    assert len(cmp_a_scores) == 2
    assert len(cmp_b_scores) == 1


# ── Test 16: Idempotency & Caching ──
def test_idempotency_and_caching(ranker):
    """Rerunning ranking on identical input produces identical fingerprints and scores."""
    company_data = {"id": "cmp_idem", "company_name": "Identical Co", "revenue": 1000000}
    person_data = {"id": "prs_idem", "title": "CEO", "email": "ceo@idem.com"}

    score1, _ = ranker.rank_prospect("prsp_id_1", company_data=company_data, person_data=person_data, icp_score=0.88)
    score2, _ = ranker.rank_prospect("prsp_id_1", company_data=company_data, person_data=person_data, icp_score=0.88)

    assert score1.fingerprint == score2.fingerprint
    assert score1.final_score == score2.final_score
    assert score1.status == score2.status


# ── Test 17: FastAPI Endpoints ──
def test_fastapi_endpoints():
    """Validates FastAPI router routes for prospects, ranking, queue, and profiles."""
    from growx_crawl.api.v1.router import v1_router
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(v1_router, prefix="/v1")
    client = TestClient(app)

    import uuid
    uid = uuid.uuid4().hex[:8]
    test_prj = f"prj_{uid}"
    test_cmp = f"cmp_{uid}"
    test_prs = f"prs_{uid}"

    # 1. Create prospect
    res_create = client.post("/v1/prospects", json={
        "project_id": test_prj,
        "company_id": test_cmp,
        "person_id": test_prs,
        "metadata": {"source": "unit_test"}
    })
    assert res_create.status_code == 200
    p_data = res_create.json()
    prospect_id = p_data["id"]

    # 2. List prospects
    res_list = client.get(f"/v1/prospects?project_id={test_prj}")
    assert res_list.status_code == 200
    assert any(p["id"] == prospect_id for p in res_list.json())

    # 3. Rank prospect
    res_rank = client.post(f"/v1/prospects/{prospect_id}/rank", json={
        "company_data": {"id": test_cmp, "company_name": "API Test Co", "is_verified": True},
        "person_data": {"id": test_prs, "email": "test@api.com", "seniority": "vp"},
        "icp_score": 0.85,
        "ranking_profile_id": "default_v1",
    })
    assert res_rank.status_code == 200
    rank_json = res_rank.json()
    assert "score" in rank_json
    assert "explanations" in rank_json
    score_id = rank_json["score"]["id"]

    # 4. Get latest score
    res_score = client.get(f"/v1/prospects/{prospect_id}/score")
    assert res_score.status_code == 200
    assert res_score.json()["id"] == score_id

    # 5. Get score explanations
    res_exps = client.get(f"/v1/prospect-scores/{score_id}/explanations")
    assert res_exps.status_code == 200
    assert len(res_exps.json()) > 0

    # 6. Get score history
    res_hist = client.get(f"/v1/prospects/{prospect_id}/history")
    assert res_hist.status_code == 200
    assert len(res_hist.json()) >= 1

    # 7. List profiles
    res_profiles = client.get("/v1/ranking-profiles")
    assert res_profiles.status_code == 200
    assert len(res_profiles.json()) >= 4
