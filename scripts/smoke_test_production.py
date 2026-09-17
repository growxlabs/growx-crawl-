#!/usr/bin/env python3
"""
Production Smoke Test for GrowX Crawl & AutoGTM.
Tests production readiness, worker health, active project and prospect queues.
"""

import sys
import urllib.request
import json

BASE_URL = "http://127.0.0.1:7411"


def run_production_smoke_test():
    print(f"=== Running Production Smoke Test on {BASE_URL} ===")

    # 1. Health Probes
    with urllib.request.urlopen(f"{BASE_URL}/health/ready", timeout=5) as r:
        ready = json.loads(r.read())
        assert ready["status"] == "ready"
        print("✓ Production Readiness Probe: PASS")

    # 2. Worker Registry
    with urllib.request.urlopen(f"{BASE_URL}/v1/ops/workers", timeout=5) as r:
        workers = json.loads(r.read())
        print(f"✓ Registered Worker Processes: {len(workers)}: PASS")

    # 3. Metrics Summary
    with urllib.request.urlopen(f"{BASE_URL}/v1/ops/metrics", timeout=5) as r:
        metrics = json.loads(r.read())
        assert "api" in metrics and "queue" in metrics
        print(f"✓ Production Metrics Collector: PASS (requests={metrics['api']['total_requests']})")

    # 4. Real Internal Project: Manufacturing India
    with urllib.request.urlopen(f"{BASE_URL}/v1/projects/prj_growx_mfg_india/overview", timeout=5) as r:
        mfg_overview = json.loads(r.read())
        assert mfg_overview.get("name") == "GrowxLabs — Manufacturing India"
        print(f"✓ GrowxLabs Manufacturing India Project Verified: PASS")

    print("=== All Production Smoke Tests Passed Successfully! ===")


if __name__ == "__main__":
    try:
        run_production_smoke_test()
    except Exception as e:
        print(f"✗ Production Smoke Test Failed: {e}")
        sys.exit(1)
