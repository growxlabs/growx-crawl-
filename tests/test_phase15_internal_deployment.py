"""
Phase 15 — Internal Deployment Test Suite.
Tests environment separation, persistent job queue, worker lifecycle & heartbeats,
atomic leasing, migration locks, internal auth/RBAC, health probes, and operator feedback.
"""

from datetime import datetime, timezone
import os
import pytest
from fastapi.testclient import TestClient

from growx_crawl.auth.models import Role, UserStatus
from growx_crawl.auth.service import auth_service
from growx_crawl.config.environments import (
    AppEnvironmentConfig,
    EnvironmentType,
    get_active_config,
    get_active_environment,
)
from growx_crawl.config.environments.validator import EnvironmentValidationError, validate_environment
from growx_crawl.feedback.models import FeedbackType
from growx_crawl.feedback.service import operator_feedback_service
from growx_crawl.jobs.models import (
    JobEntity,
    PersistentJobStatus,
    PersistentJobType,
    WorkerEntity,
    WorkerStatus,
    WorkerType,
)
from growx_crawl.jobs.queue import job_queue_service
from growx_crawl.ops.alerts import alert_manager
from growx_crawl.ops.health import check_dependencies, check_liveness, check_readiness
from growx_crawl.ops.metrics import metrics_collector
from growx_crawl.storage.migrations.runner import migration_runner
from growx_crawl.web.app import app
from growx_crawl.workers.crawler import CrawlerWorker
from growx_crawl.workers.intelligence import IntelligenceWorker
from growx_crawl.workers.verification import VerificationWorker

client = TestClient(app)


# ── 1. Environment Configuration & Validation ──

def test_environment_configuration_and_validation():
    env = get_active_environment()
    assert env in (EnvironmentType.DEVELOPMENT, EnvironmentType.STAGING, EnvironmentType.PRODUCTION)

    cfg = get_active_config()
    assert cfg.workers.crawler_concurrency >= 1
    assert cfg.workers.lease_timeout_seconds >= 10

    # Test validator catches missing production database
    invalid_prod_cfg = AppEnvironmentConfig(
        environment=EnvironmentType.PRODUCTION,
        database={"database_url": None},
        auth={"jwt_secret": "growx_insecure_dev_secret_change_in_prod"},
    )
    errors = validate_environment(invalid_prod_cfg)
    assert any("Missing canonical PostgreSQL DATABASE_URL" in e for e in errors)
    assert any("Default insecure JWT secret" in e for e in errors)


# ── 2. Persistent Job Queue & Atomic Leasing ──

def test_persistent_job_queue_and_leasing():
    # 1. Enqueue job
    job = job_queue_service.enqueue(
        job_type=PersistentJobType.CRAWL_BATCH.value,
        payload={"urls": ["https://example.com/about", "https://example.com/team"]},
        priority=80,
    )
    assert job.id.startswith("job_")
    assert job.status == PersistentJobStatus.QUEUED

    # 2. Worker claims job
    worker_id = "wrk_test_crawler_01"
    claimed = job_queue_service.claim(
        worker_id=worker_id,
        accepted_types=[PersistentJobType.CRAWL_BATCH.value],
        lease_seconds=60,
    )
    assert claimed is not None
    assert claimed.id == job.id
    assert claimed.status == PersistentJobStatus.CLAIMED
    assert claimed.claimed_by_worker_id == worker_id
    assert claimed.lease_expires_at is not None

    # 3. Heartbeat lease renewal
    hb_ok = job_queue_service.heartbeat(job.id, worker_id, lease_seconds=120)
    assert hb_ok is True

    # 4. Complete job
    res = job_queue_service.complete(job.id, worker_id, result={"urls_fetched": 2, "status": "ok"})
    assert res is not None
    assert res.status == PersistentJobStatus.COMPLETED
    assert res.result_json["urls_fetched"] == 2


def test_job_failure_and_retry_budget():
    job = job_queue_service.enqueue(
        job_type="http_fetch",
        payload={"url": "https://flaky-endpoint.com"},
        priority=50,
        max_retries=2,
    )
    worker_id = "wrk_retry_worker"
    claimed = job_queue_service.claim(worker_id, accepted_types=["http_fetch"])
    assert claimed is not None

    # Fail job (first retry)
    failed = job_queue_service.fail(job.id, worker_id, reason="Connection timeout", can_retry=True)
    assert failed.status == PersistentJobStatus.RETRYING
    assert failed.retry_count == 1
    assert failed.claimed_by_worker_id is None

    # Claim again and fail past max_retries
    claimed2 = job_queue_service.claim(worker_id, accepted_types=["http_fetch"])
    assert claimed2 is not None
    job_queue_service.fail(job.id, worker_id, reason="Connection timeout 2", can_retry=True)
    claimed3 = job_queue_service.claim(worker_id, accepted_types=["http_fetch"])
    if claimed3:
        final_fail = job_queue_service.fail(job.id, worker_id, reason="Connection timeout 3", can_retry=True)
        assert final_fail.status == PersistentJobStatus.FAILED


def test_lease_expiry_reclaim():
    # Enqueue job with already expired lease simulation
    job = job_queue_service.enqueue(job_type="test_abandoned", payload={})
    worker_id = "wrk_dead_process"
    claimed = job_queue_service.claim(worker_id, accepted_types=["test_abandoned"], lease_seconds=-10)
    assert claimed is not None

    # Reclaim expired leases
    reclaimed_count = job_queue_service.reclaim_expired_leases()
    assert reclaimed_count >= 1

    # Verify job status reverted to retrying/queued
    reclaimed_job = job_queue_service.get_job(job.id)
    assert reclaimed_job.status in (PersistentJobStatus.RETRYING, PersistentJobStatus.QUEUED)
    assert reclaimed_job.claimed_by_worker_id is None


# ── 3. Worker Lifecycle & Heartbeat Registry ──

def test_worker_registration_and_heartbeats():
    wrk_id = "wrk_live_test_01"
    worker = job_queue_service.register_worker(
        worker_id=wrk_id,
        worker_type=WorkerType.CRAWLER.value,
        hostname="test-host",
        process_id=9999,
        version="1.0.0",
    )
    assert worker.id == wrk_id
    assert worker.status == WorkerStatus.ACTIVE

    # Heartbeat update
    ok = job_queue_service.heartbeat_worker(wrk_id, current_job_id="job_dummy_01")
    assert ok is True

    # List workers
    all_workers = job_queue_service.list_workers()
    assert any(w.id == wrk_id for w in all_workers)


# ── 4. Dedicated Worker Implementations ──

@pytest.mark.asyncio
async def test_dedicated_worker_processing():
    # Crawler Worker
    crawler = CrawlerWorker()
    job_c = JobEntity(
        job_type=PersistentJobType.CRAWL_BATCH.value,
        payload_json={"domain": "example.com", "urls": ["https://example.com/page1"]},
    )
    res_c = await crawler.process_job(job_c)
    assert res_c["status"] == "success"
    assert res_c["urls_fetched"] == 1

    # Intelligence Worker
    intel = IntelligenceWorker()
    job_i = JobEntity(
        job_type=PersistentJobType.ICP_EVALUATION.value,
        payload_json={"icp_id": "icp_test", "company_id": "cmp_test"},
    )
    res_i = await intel.process_job(job_i)
    assert res_i["overall_fit_score"] >= 0.80

    # Verification Worker
    verifier = VerificationWorker()
    job_v = JobEntity(
        job_type=PersistentJobType.VERIFY_COMPANY.value,
        payload_json={"subject_id": "cmp_test_co"},
    )
    res_v = await verifier.process_job(job_v)
    assert res_v["verification_status"] == "Verified"


# ── 5. Database Migration Runner & Lock ──

def test_database_migration_runner_and_lock():
    # Acquire lock
    locked = migration_runner.acquire_lock()
    assert locked is True

    # Second acquisition should fail
    locked_again = migration_runner.acquire_lock()
    assert locked_again is False

    # Apply test migration
    v = f"v15_test_{int(datetime.now(timezone.utc).timestamp())}"
    applied = migration_runner.apply_migration(
        version=v,
        name="test_phase15_migration",
        sql="CREATE TABLE IF NOT EXISTS _test_migration_tbl (id TEXT PRIMARY KEY);",
    )
    assert applied is True

    # Duplicate migration should not re-run
    applied_dup = migration_runner.apply_migration(
        version=v,
        name="test_phase15_migration",
        sql="CREATE TABLE IF NOT EXISTS _test_migration_tbl (id TEXT PRIMARY KEY);",
    )
    assert applied_dup is False

    # Release lock
    migration_runner.release_lock()


# ── 6. Health & Observability Probes ──

def test_health_endpoints():
    r_live = client.get("/health/live")
    assert r_live.status_code == 200
    assert r_live.json()["status"] == "alive"

    r_ready = client.get("/health/ready")
    assert r_ready.status_code == 200
    assert r_ready.json()["status"] == "ready"

    r_deps = client.get("/health/dependencies")
    assert r_deps.status_code == 200
    assert "components" in r_deps.json()


def test_metrics_and_alerting():
    metrics_collector.record_request(45.2, is_error=False)
    summary = metrics_collector.get_summary()
    assert "api" in summary
    assert summary["api"]["total_requests"] >= 1

    # Alert dispatcher test
    sent = alert_manager.dispatch(
        alert_key="test_stuck_queue",
        title="Stuck Queue Test",
        message="Simulated alert dispatch for test",
        severity="warning",
    )
    assert sent is True
    # Throttling test
    throttled = alert_manager.dispatch(
        alert_key="test_stuck_queue",
        title="Stuck Queue Test 2",
        message="Should be throttled",
        severity="warning",
    )
    assert throttled is False


# ── 7. Internal Auth, RBAC & Audit Trail ──

def test_internal_auth_and_rbac():
    # Login as admin
    r_login = client.post("/v1/auth/login", json={"email": "admin@growxlabs.tech", "password": "admin_internal_password"})
    assert r_login.status_code == 200
    token = r_login.json()["access_token"]
    assert token

    # Check /v1/auth/me
    r_me = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r_me.status_code == 200
    assert r_me.json()["email"] == "admin@growxlabs.tech"
    assert r_me.json()["role"] == "admin"

    # List users (admin required)
    r_users = client.get("/v1/auth/users", headers={"Authorization": f"Bearer {token}"})
    assert r_users.status_code == 200
    assert len(r_users.json()) >= 2

    # Audit events
    r_audit = client.get("/v1/auth/audit", headers={"Authorization": f"Bearer {token}"})
    assert r_audit.status_code == 200
    assert len(r_audit.json()) >= 1


# ── 8. Operator Feedback Ground-Truth ──

def test_operator_feedback_capture():
    # Submit feedback
    r_fb = client.post(
        "/v1/feedback",
        json={
            "subject_type": "prospect",
            "subject_id": "cmp_linear",
            "feedback_type": "correct",
            "notes": "Verified verified headcount matches linear.app about page.",
        },
    )
    assert r_fb.status_code == 200
    assert r_fb.json()["feedback_type"] == "correct"

    # Summary
    r_summary = client.get("/v1/feedback/summary")
    assert r_summary.status_code == 200
    assert r_summary.json()["total_feedback_count"] >= 1
    assert "correct" in r_summary.json()["breakdown_by_type"]


# ── 9. Real Internal Project: Manufacturing India ──

def test_manufacturing_india_seed_project():
    from growx_crawl.autogtm.seed import seed_canonical_environment
    seed_canonical_environment()

    r = client.get("/v1/projects/prj_growx_mfg_india/overview")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "GrowxLabs — Manufacturing India"
    assert "India" in data["target_geography"]
