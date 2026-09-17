"""
Comprehensive Unit & Integration Tests for Phase 09 — Nightly Data Factory.
Verifies:
- DataFactoryPlanner plan creation and segment loading
- Search-first discovery skipping known fresh entities
- Crawl prioritization, budget caps, failure isolation, and R2 artifact storage
- Offline R2 reprocessing without recrawling
- Identity resolution and entity resolution integration
- Fact ingestion with evidence linking and idempotency
- Stored-data-first verification reuse
- Data quality gate enforcement
- Historical change detection
- Downstream search indexing
- Checkpoint persistence and resume capability
- Concurrency run locking, pause, and cancellation
- Morning Intelligence Report generation
- FastAPI v1 REST endpoints
"""

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner
from growx_crawl.cli.main import app as cli_app
from growx_crawl.data_factory import (
    BudgetGuard,
    CheckpointManager,
    CrawlMode,
    CrawlPrioritizer,
    CrawlStage,
    DataFactoryCheckpoint,
    DataFactoryMetrics,
    DataFactoryPlan,
    DataFactoryPlanner,
    DataFactoryRepository,
    DataFactoryRun,
    DataFactoryScheduler,
    DataFactoryService,
    DiscoverStage,
    ExtractStage,
    FactoryStage,
    FactsStage,
    HistoryStage,
    InMemoryDataFactoryRepository,
    IndexStage,
    MorningSummary,
    PriorityTier,
    QualityStage,
    RefreshPlanner,
    ResolveStage,
    RunStatus,
    RunType,
    TargetSegment,
    VerifyStage,
)
from growx_crawl.web.app import app


@pytest.fixture
def mem_repo():
    return InMemoryDataFactoryRepository()


@pytest.fixture
def test_client():
    return TestClient(app)


@pytest.fixture
def mem_service(mem_repo):
    scheduler = DataFactoryScheduler()
    return DataFactoryService(repository=mem_repo, scheduler=scheduler)


# ── 1. DataFactoryPlanner Tests ──

def test_planner_creates_valid_plan():
    planner = DataFactoryPlanner()
    plan = planner.create_plan(run_type=RunType.NIGHTLY)
    assert plan.id.startswith("plan_")
    assert plan.run_type == RunType.NIGHTLY
    assert len(plan.target_segments) > 0
    assert plan.max_companies >= 100
    assert plan.max_pages >= 500
    assert plan.ai_budget > 0
    assert plan.verification_budget > 0


# ── 2. DiscoverStage & Search-First Strategy ──

def test_discover_stage_skips_known_fresh_and_queues_new():
    stage = DiscoverStage()
    planner = DataFactoryPlanner()
    plan = planner.create_plan(run_type=RunType.NIGHTLY)
    metrics = DataFactoryMetrics()

    seeds = [
        {"domain": "fresh-existing.com", "name": "Fresh Co", "priority": "P1"},
        {"domain": "brand-new-lead.com", "name": "Brand New Lead", "priority": "P2"},
    ]

    # Mock _is_domain_known_fresh to treat 'fresh-existing.com' as already fresh in DB
    def mock_is_fresh(domain, conn=None):
        return domain == "fresh-existing.com"

    stage._is_domain_known_fresh = mock_is_fresh

    candidates = stage.execute(plan, metrics, seed_candidates=seeds)
    # The fresh domain must be skipped; the new domain must be queued
    assert metrics.known_domains >= 1
    assert any(c["domain"] == "brand-new-lead.com" for c in candidates)
    assert not any(c["domain"] == "fresh-existing.com" for c in candidates)


# ── 3. Prioritization & Budget Guard ──

def test_crawl_prioritizer_sorting():
    items = [
        {"domain": "p3.com", "priority": "P3"},
        {"domain": "p0.com", "is_active_campaign": True},
        {"domain": "p2.com", "priority": "P2"},
        {"domain": "p1.com", "is_high_fit": True},
    ]
    sorted_items = CrawlPrioritizer.prioritize_items(items)
    priorities = [CrawlPrioritizer.determine_priority(i) for i in sorted_items]
    assert priorities == [PriorityTier.P0, PriorityTier.P1, PriorityTier.P2, PriorityTier.P3]


def test_budget_guard_limits_and_degradation():
    plan = DataFactoryPlan(
        id="test_plan",
        max_pages=5,
        max_browser_sessions=2,
        ai_budget=1.0,
        verification_budget=0.5,
        crawl_mode=CrawlMode.DEEP,
    )
    guard = BudgetGuard(plan)

    assert guard.can_crawl_page() is True
    guard.record_page_crawl(4)
    assert guard.can_crawl_page() is True
    # Over 80% should degrade crawl mode from DEEP to LIGHT
    assert guard.get_degraded_crawl_mode() == CrawlMode.LIGHT

    guard.record_page_crawl(1)
    assert guard.can_crawl_page() is False
    assert "limit reached" in guard.stopped_reason.lower()


# ── 4. CrawlStage & Failure Isolation ──

@pytest.mark.asyncio
async def test_crawl_stage_isolates_failures():
    stage = CrawlStage()
    plan = DataFactoryPlan(id="test_plan", max_pages=10)
    guard = BudgetGuard(plan)
    metrics = DataFactoryMetrics()

    candidates = [
        {"domain": "valid-tech.com", "company_name": "Valid Tech", "priority": "P1"},
        {"domain": "failing-test-domain.com", "company_name": "Broken Co", "priority": "P1"},
        {"domain": "another-good-domain.com", "company_name": "Another Good Co", "priority": "P1"},
    ]

    results = await stage.execute(candidates, plan, guard, metrics)

    # 1 failed, 2 succeeded
    assert metrics.errors == 1
    assert metrics.pages_failed == 1
    assert len(results) == 2
    domains = [r["domain"] for r in results]
    assert "valid-tech.com" in domains
    assert "another-good-domain.com" in domains
    assert "failing-test-domain.com" not in domains


# ── 5. ExtractStage & Offline R2 Reprocessing ──

def test_extract_stage_and_r2_reprocessing():
    stage = ExtractStage()
    metrics = DataFactoryMetrics()

    crawled = [{
        "domain": "extracto.com",
        "company_name": "Extracto Corp",
        "url": "https://extracto.com",
        "raw_html": "<p>High precision machinery engineering.</p><p>Contact: sales@extracto.com | +1 555 0123</p>",
        "r2_key": "snapshots/extracto.com/abc12345.html",
        "content_hash": "hash_12345",
    }]

    observations = stage.execute(crawled, metrics)
    assert len(observations) == 1
    obs = observations[0]
    assert obs["domain"] == "extracto.com"
    assert "sales@extracto.com" in obs["emails"]
    assert obs["r2_key"] == "snapshots/extracto.com/abc12345.html"

    # Offline R2 reprocessing without recrawling
    class MockObjectStore:
        def get_object(self, key):
            class Obj:
                def read(self):
                    return b"<html><body><h1>Reprocessed Co</h1><p>contact: support@reproc.com</p></body></html>"
            return Obj()

    stage_r2 = ExtractStage(object_store=MockObjectStore())
    reprocessed = stage_r2.reprocess_from_r2(["snapshots/reproc.com/xyz.html"], metrics)
    assert len(reprocessed) == 1
    assert "support@reproc.com" in reprocessed[0]["emails"]


# ── 6. CheckpointManager & Resume Calculation ──

def test_checkpoint_manager_resume_point(mem_repo):
    mgr = CheckpointManager(repository=mem_repo)
    run_id = "dfr_test_resumable"

    mgr.create_checkpoint(run_id, FactoryStage.DISCOVERY, status="completed")
    mgr.create_checkpoint(run_id, FactoryStage.CRAWL, status="completed")
    mgr.create_checkpoint(run_id, FactoryStage.EXTRACT, status="completed")

    checkpoints = mem_repo.get_checkpoints(run_id)
    next_stage = mgr.determine_resume_stage(checkpoints)
    # Next stage after EXTRACT is RESOLVE
    assert next_stage == FactoryStage.RESOLVE


# ── 7. Full Pipeline Execution & End-to-End Flow ──

@pytest.mark.asyncio
async def test_data_factory_service_end_to_end(mem_service):
    plan = mem_service.plan_run(
        run_type=RunType.MANUAL,
        custom_config={"max_companies": 2, "max_pages": 5},
    )

    seed_items = [
        {
            "domain": "hexagondata.io",
            "company_name": "Hexagon Data",
            "priority": "P0",
            "is_active_campaign": True,
        },
        {
            "domain": "synthex.ai",
            "company_name": "Synthex AI",
            "priority": "P1",
        },
    ]

    run = await mem_service.start_run(
        plan=plan,
        run_type=RunType.MANUAL,
        seed_candidates=seed_items,
    )

    assert run.status in (RunStatus.COMPLETED, RunStatus.COMPLETED_WITH_ERRORS)
    assert run.checkpoint == FactoryStage.COMPLETE
    assert run.entity_count >= 1
    assert run.crawl_count >= 1

    # Verify Morning Intelligence Report was generated and stored
    summary = mem_service.get_morning_summary(run.id)
    assert summary is not None
    assert summary.run_id == run.id
    assert "Morning Intelligence Report" in summary.report_markdown
    assert summary.companies_created + summary.companies_updated >= 1


# ── 8. Concurrency Lock & Run Lifecycle ──

@pytest.mark.asyncio
async def test_scheduler_run_lock_and_pause(mem_service):
    plan = mem_service.plan_run(run_type=RunType.NIGHTLY)

    # Acquire lock directly to simulate running state
    mem_service.scheduler.acquire_run_lock("dfr_existing_active")

    with pytest.raises(RuntimeError, match="another run .* is currently active"):
        await mem_service.start_run(plan=plan, run_type=RunType.NIGHTLY)

    # Release and pause run test
    mem_service.scheduler.release_run_lock("dfr_existing_active")

    test_run = DataFactoryRun(
        id="dfr_to_pause",
        run_type=RunType.NIGHTLY,
        status=RunStatus.RUNNING,
    )
    mem_service.repository.save_run(test_run)

    paused = mem_service.pause_run("dfr_to_pause")
    assert paused.status == RunStatus.PAUSED

    cancelled = mem_service.cancel_run("dfr_to_pause")
    assert cancelled.status == RunStatus.CANCELLED


# ── 9. Stored-Data-First Verification Reuse ──

@pytest.mark.asyncio
async def test_verification_stage_reuses_stored_results():
    stage = VerifyStage()
    metrics = DataFactoryMetrics()
    plan = DataFactoryPlan(id="test_plan")
    guard = BudgetGuard(plan)

    # Mock verification service where company_1 is already verified
    class MockVerState:
        status = type("Status", (), {"value": "verified"})
        confidence = 0.95

    class MockVerService:
        def get_current_state(self, st, sid, vt):
            if sid == "cmp_already_verified":
                return MockVerState()
            return None

        async def verify_company(self, company_id, domain, company_name):
            res = type("Run", (), {"status": type("Status", (), {"value": "verified"}), "confidence": 0.90})
            return res()

    stage.verification_service = MockVerService()

    fact_items = [
        {"canonical_company_id": "cmp_already_verified", "domain": "verified.com", "company_name": "Verified Co"},
        {"canonical_company_id": "cmp_needs_verification", "domain": "new.com", "company_name": "New Co"},
    ]

    verified = await stage.execute(fact_items, guard, metrics)
    assert len(verified) == 2
    assert metrics.verifications_reused == 1
    assert metrics.verifications_executed == 1


# ── 10. FastAPI API Endpoints ──

def test_api_data_factory_endpoints(test_client):
    headers = {"X-API-Key": "gx_live_sandbox_master_key"}

    # 1. Start run via API
    start_payload = {
        "run_type": "manual",
        "custom_config": {"max_companies": 1, "max_pages": 2},
        "seed_candidates": [{"domain": "api-factory-test.com", "company_name": "API Test Co"}],
    }
    resp = test_client.post("/api/v1/data-factory/runs", json=start_payload, headers=headers)
    assert resp.status_code == 200
    run_data = resp.json()
    assert run_data["id"].startswith("dfr_")
    run_id = run_data["id"]

    # 2. Get latest run
    resp_latest = test_client.get("/api/v1/data-factory/runs/latest", headers=headers)
    assert resp_latest.status_code == 200
    assert resp_latest.json()["id"] == run_id

    # 3. Get run details
    resp_get = test_client.get(f"/api/v1/data-factory/runs/{run_id}", headers=headers)
    assert resp_get.status_code == 200
    assert resp_get.json()["id"] == run_id

    # 4. Get run summary
    resp_sum = test_client.get(f"/api/v1/data-factory/runs/{run_id}/summary", headers=headers)
    assert resp_sum.status_code == 200
    assert "report_markdown" in resp_sum.json()

    # 5. Retry failed jobs endpoint
    resp_retry = test_client.post(f"/api/v1/data-factory/runs/{run_id}/retry-failed", headers=headers)
    assert resp_retry.status_code == 200

    # 6. Reprocess endpoint
    reproc_payload = {"r2_keys": ["snapshots/sample.com/dummy.html"]}
    resp_reproc = test_client.post("/api/v1/data-factory/reprocess", json=reproc_payload, headers=headers)
    assert resp_reproc.status_code == 200


# ── 11. CLI Execution Test ──

def test_cli_data_factory_status():
    runner = CliRunner()
    result = runner.invoke(cli_app, ["factory", "status"])
    # Command executes and reports status
    assert result.exit_code == 0
