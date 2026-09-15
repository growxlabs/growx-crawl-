"""
Unit tests for GrowX Crawl Anti-Bot Bypass & Stealth Subsystems.
"""

import pytest
from growx_crawl.crawler.stealth.fingerprint import get_stealth_init_script
from growx_crawl.crawler.stealth.behavior import _generate_bezier_curve
from growx_crawl.crawler.proxies import ProxyPoolManager, ProxyTier
from growx_crawl.crawler.stealth.solver import CaptchaSolverManager


def test_stealth_init_script_generation():
    """Verify stealth script injects required anti-detection hooks."""
    script = get_stealth_init_script(
        gpu_profile={"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, RTX 3080)"},
        hardware_concurrency=16,
        device_memory=16,
    )
    assert "navigator.webdriver" in script
    assert "UNMASKED_VENDOR_WEBGL" in script
    assert "RTX 3080" in script
    assert "AudioBuffer" in script
    assert "getImageData" in script
    assert "window.chrome" in script


def test_bezier_curve_generation():
    """Verify cubic Bezier curve math generates smooth, non-linear mouse paths."""
    start = (100.0, 100.0)
    end = (500.0, 400.0)
    steps = 20

    points = _generate_bezier_curve(start, end, steps=steps)
    assert len(points) == steps
    # Last point must reach the destination
    final_x, final_y = points[-1]
    assert pytest.approx(final_x, abs=1.0) == 500.0
    assert pytest.approx(final_y, abs=1.0) == 400.0

    # Intermediate points should not be purely collinear due to Bezier curvature
    mid_x, mid_y = points[10]
    linear_mid_x = (start[0] + end[0]) / 2.0
    linear_mid_y = (start[1] + end[1]) / 2.0
    # Difference exists due to perpendicular control point offset
    assert (mid_x, mid_y) != (linear_mid_x, linear_mid_y)


def test_proxy_pool_escalation():
    """Verify proxy tier escalation from Direct to Datacenter/Residential."""
    pm = ProxyPoolManager()
    tier, proxy = pm.escalate_tier(ProxyTier.DIRECT)
    assert tier == ProxyTier.DATACENTER

    tier_2, _ = pm.escalate_tier(ProxyTier.DATACENTER)
    assert tier_2 == ProxyTier.RESIDENTIAL

    # Record 403 failure and verify cooldown calculation
    test_proxy = "http://test-proxy:8080"
    pm.record_result(test_proxy, 403)
    assert test_proxy in pm.health
    assert pm.health[test_proxy]["failures"] == 1
    assert pm.health[test_proxy]["cooldown_until"] > 0


def test_captcha_solver_manager_initialization():
    """Verify captcha solver manager initializes without throwing."""
    manager = CaptchaSolverManager()
    assert isinstance(manager.has_active_provider, bool)


def test_session_aging_manager_persistence(tmp_path):
    """Verify session aging manager persists and retrieves cookies."""
    from growx_crawl.crawler.stealth.warmer import SessionAgingManager
    manager = SessionAgingManager(profiles_dir=str(tmp_path))
    test_domain = "example.org"
    sample_cookies = [{"name": "cf_clearance", "value": "test_token_123"}]

    manager.save_session(test_domain, sample_cookies, "TestUA/1.0", ttl_seconds=3600)
    retrieved = manager.get_session(test_domain)
    assert retrieved is not None
    assert retrieved[0]["value"] == "test_token_123"


def test_ghost_engine_instantiation():
    """Verify GhostEngine instance is ready."""
    from growx_crawl.crawler.stealth.ghost import GhostEngine
    engine = GhostEngine()
    assert hasattr(engine, "fetch")
