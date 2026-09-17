"""
GrowX Data Factory Budget Guard.
Enforces resource quotas, runtime limits, AI/verification cost caps,
and graceful degradation modes.
"""

from datetime import datetime, timezone
from typing import Any, Dict
from growx_crawl.data_factory.models import CrawlMode, DataFactoryPlan
from growx_crawl.shared.time import parse_iso, utc_now


class BudgetGuard:
    """Live resource quota monitor and degradation controller for a Data Factory run."""

    def __init__(self, plan: DataFactoryPlan):
        self.plan = plan
        self.pages_crawled: int = 0
        self.browser_sessions: int = 0
        self.ai_spend: float = 0.0
        self.verification_spend: float = 0.0
        self.bytes_downloaded: int = 0
        self.stopped_reason: str = ""

    @property
    def total_cost(self) -> float:
        # Bandwidth estimated at $0.09 / GB
        bandwidth_cost = (self.bytes_downloaded / (1024 * 1024 * 1024)) * 0.09
        # Browser sessions estimated at $0.005 / session
        browser_cost = self.browser_sessions * 0.005
        return round(self.ai_spend + self.verification_spend + bandwidth_cost + browser_cost, 4)

    def can_crawl_page(self) -> bool:
        if self.pages_crawled >= self.plan.max_pages:
            self.stopped_reason = f"Max pages limit reached ({self.plan.max_pages})"
            return False
        return True

    def can_use_browser(self) -> bool:
        if self.browser_sessions >= self.plan.max_browser_sessions:
            return False
        return True

    def can_spend_ai(self, amount: float = 0.01) -> bool:
        if self.ai_spend + amount > self.plan.ai_budget:
            self.stopped_reason = f"AI budget limit reached (${self.plan.ai_budget:.2f})"
            return False
        return True

    def can_spend_verification(self, amount: float = 0.01) -> bool:
        if self.verification_spend + amount > self.plan.verification_budget:
            self.stopped_reason = f"Verification budget limit reached (${self.plan.verification_budget:.2f})"
            return False
        return True

    def is_runtime_exceeded(self, started_at_iso: str) -> bool:
        started_at = parse_iso(started_at_iso)
        if not started_at:
            return False
        elapsed_minutes = (utc_now() - started_at).total_seconds() / 60.0
        if elapsed_minutes >= self.plan.max_runtime_minutes:
            self.stopped_reason = f"Max runtime limit exceeded ({self.plan.max_runtime_minutes} mins)"
            return True
        return False

    def is_budget_exhausted(self, started_at_iso: str) -> bool:
        if not self.can_crawl_page():
            return True
        if self.is_runtime_exceeded(started_at_iso):
            return True
        if self.ai_spend >= self.plan.ai_budget and self.verification_spend >= self.plan.verification_budget:
            self.stopped_reason = "Both AI and verification budgets exhausted"
            return True
        return False

    def get_degraded_crawl_mode(self) -> CrawlMode:
        """Determines appropriate crawl mode based on consumption pressure."""
        page_ratio = self.pages_crawled / max(1, self.plan.max_pages)
        browser_ratio = self.browser_sessions / max(1, self.plan.max_browser_sessions)

        if page_ratio >= 0.80 or browser_ratio >= 0.80:
            return CrawlMode.LIGHT
        elif page_ratio >= 0.60 or browser_ratio >= 0.60:
            return CrawlMode.STANDARD
        return self.plan.crawl_mode

    def record_page_crawl(self, count: int = 1) -> None:
        self.pages_crawled += count

    def record_browser_session(self, count: int = 1) -> None:
        self.browser_sessions += count

    def record_ai_spend(self, amount: float) -> None:
        self.ai_spend = round(self.ai_spend + amount, 4)

    def record_verification_spend(self, amount: float) -> None:
        self.verification_spend = round(self.verification_spend + amount, 4)

    def record_bytes(self, byte_count: int) -> None:
        self.bytes_downloaded += byte_count

    def get_summary(self) -> Dict[str, Any]:
        return {
            "pages_crawled": self.pages_crawled,
            "max_pages": self.plan.max_pages,
            "browser_sessions": self.browser_sessions,
            "max_browser_sessions": self.plan.max_browser_sessions,
            "ai_spend": self.ai_spend,
            "ai_budget": self.plan.ai_budget,
            "verification_spend": self.verification_spend,
            "verification_budget": self.plan.verification_budget,
            "total_estimated_cost": self.total_cost,
            "stopped_reason": self.stopped_reason,
        }
