"""
Health check endpoints logic for GrowX.
Supports /health/live, /health/ready, and /health/dependencies.
"""

from datetime import datetime, timezone
import os
import time
from typing import Any, Dict

from growx_crawl.config.environments import get_active_config
from growx_crawl.jobs.queue import job_queue_service
from growx_crawl.storage.postgres.db import PostgresPool

START_TIME = time.time()


def check_liveness() -> Dict[str, Any]:
    """Lightweight liveness probe answering: is the process alive?"""
    return {
        "status": "alive",
        "uptime_seconds": round(time.time() - START_TIME, 2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def check_readiness() -> Dict[str, Any]:
    """Readiness probe answering: can the process accept work?"""
    cfg = get_active_config()
    db_ok = True
    db_details = "sqlite_active"

    # If PostgreSQL configured, check pool health
    if cfg.database.database_url or os.environ.get("DATABASE_URL"):
        pool = PostgresPool.get_instance()
        db_ok = pool.check_health()
        db_details = "postgres_connected" if db_ok else "postgres_disconnected"

    ready = db_ok

    return {
        "status": "ready" if ready else "not_ready",
        "environment": cfg.environment.value,
        "database": db_details,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def check_dependencies() -> Dict[str, Any]:
    """Deep dependency health evaluation across Postgres, Object Store, Queue, and Workers."""
    cfg = get_active_config()

    # Database
    db_status = "ok"
    if cfg.database.database_url or os.environ.get("DATABASE_URL"):
        pool = PostgresPool.get_instance()
        if not pool.check_health():
            db_status = "degraded"

    # Queue & Workers
    queue_depth = job_queue_service.get_queue_depth()
    workers = job_queue_service.list_workers()
    active_workers = len([w for w in workers if w.status.value == "active"])
    workers_status = "ok" if active_workers > 0 or len(workers) == 0 else "no_active_workers"

    # Object store
    obj_status = "ok"
    try:
        from growx_crawl.object_store.factory import get_object_store
        store = get_object_store()
        obj_status = "ok" if store else "unconfigured"
    except Exception:
        obj_status = "degraded"

    overall = "healthy" if db_status == "ok" and obj_status == "ok" else "degraded"

    return {
        "overall_status": overall,
        "environment": cfg.environment.value,
        "components": {
            "database": {"status": db_status, "type": "postgres" if (cfg.database.database_url or os.environ.get("DATABASE_URL")) else "sqlite"},
            "object_store": {"status": obj_status, "provider": cfg.object_store.provider},
            "job_queue": {"status": "ok", "depth": queue_depth},
            "workers": {"status": workers_status, "registered": len(workers), "active": active_workers},
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
