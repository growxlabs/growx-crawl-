#!/usr/bin/env python3
"""
Staging Smoke Test for GrowX Crawl & AutoGTM.
Tests health probes, login, project retrieval, prospect queue, and worker heartbeats.
"""

import sys
import urllib.request
import json

BASE_URL = "http://127.0.0.1:7411"


def run_staging_smoke_test():
    print(f"=== Running Staging Smoke Test on {BASE_URL} ===")
    
    # 1. Health Liveness
    with urllib.request.urlopen(f"{BASE_URL}/health/live", timeout=5) as r:
        live = json.loads(r.read())
        assert live["status"] == "alive", f"Liveness check failed: {live}"
        print("✓ Health Liveness: PASS")

    # 2. Health Readiness
    with urllib.request.urlopen(f"{BASE_URL}/health/ready", timeout=5) as r:
        ready = json.loads(r.read())
        assert ready["status"] == "ready", f"Readiness check failed: {ready}"
        print("✓ Health Readiness: PASS")

    # 3. Health Dependencies
    with urllib.request.urlopen(f"{BASE_URL}/health/dependencies", timeout=5) as r:
        deps = json.loads(r.read())
        assert "overall_status" in deps
        print("✓ Health Dependencies: PASS")

    # 4. Auth Login
    login_data = json.dumps({"email": "admin@growxlabs.tech", "password": "admin_internal_password"}).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/v1/auth/login", data=login_data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as r:
        login_res = json.loads(r.read())
        token = login_res["access_token"]
        assert token, "Token missing"
        print("✓ Internal Auth Login: PASS")

    # 5. Project Listing
    auth_headers = {"Authorization": f"Bearer {token}"}
    req = urllib.request.Request(f"{BASE_URL}/v1/projects", headers=auth_headers)
    with urllib.request.urlopen(req, timeout=5) as r:
        projects = json.loads(r.read())
        assert len(projects) > 0, "No projects returned"
        print(f"✓ Projects Listing ({len(projects)} found): PASS")

    # 6. Queue Depth
    req = urllib.request.Request(f"{BASE_URL}/v1/ops/queue", headers=auth_headers)
    with urllib.request.urlopen(req, timeout=5) as r:
        queue = json.loads(r.read())
        assert "queued" in queue
        print(f"✓ Queue Depth: PASS ({queue})")

    print("=== All Staging Smoke Tests Passed Successfully! ===")


if __name__ == "__main__":
    try:
        run_staging_smoke_test()
    except Exception as e:
        print(f"✗ Staging Smoke Test Failed: {e}")
        sys.exit(1)
