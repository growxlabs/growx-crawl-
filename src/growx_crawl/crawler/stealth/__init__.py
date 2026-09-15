"""
GrowX Crawl Stealth & Anti-Bot Bypass Subsystem.
Provides deep browser anti-detection, behavioral emulation, Turnstile solving, and proxy tiering.
"""

from growx_crawl.crawler.stealth.fingerprint import (
    STEALTH_INIT_SCRIPT,
    get_stealth_init_script,
    apply_stealth_to_page,
    apply_stealth_to_context,
)
from growx_crawl.crawler.stealth.behavior import (
    HumanBehavior,
    human_move,
    human_click,
    human_scroll,
    random_dwell,
)
from growx_crawl.crawler.stealth.turnstile import (
    TurnstileDetector,
    solve_turnstile_if_present,
)
from growx_crawl.crawler.stealth.solver import (
    CaptchaSolverManager,
    captcha_solver,
)
from growx_crawl.crawler.stealth.warmer import (
    SessionAgingManager,
    session_aging_manager,
)
from growx_crawl.crawler.stealth.ghost import (
    GhostEngine,
    ghost_engine,
)

__all__ = [
    "STEALTH_INIT_SCRIPT",
    "get_stealth_init_script",
    "apply_stealth_to_page",
    "apply_stealth_to_context",
    "HumanBehavior",
    "human_move",
    "human_click",
    "human_scroll",
    "random_dwell",
    "TurnstileDetector",
    "solve_turnstile_if_present",
    "CaptchaSolverManager",
    "captcha_solver",
    "SessionAgingManager",
    "session_aging_manager",
    "GhostEngine",
    "ghost_engine",
]
