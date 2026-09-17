"""
GrowX Competitor Refresh Engine.
Governs incremental refresh policies, fact-change impact detection, and staleness.
"""

from datetime import timedelta
from typing import Any, List, Optional
from growx_crawl.intelligence.competitors.models import CompanyCompetitorSummary, RelationshipStatus
from growx_crawl.intelligence.competitors.repository import BaseCompetitorRepository
from growx_crawl.shared.time import parse_iso, utc_now


class CompetitorRefreshEngine:
    """Manages incremental refresh cycles triggered by time staleness or fact changes."""

    COMPETITION_IMPACTING_PREDICATES = {
        "company.industry",
        "company.product",
        "company.service",
        "company.location",
        "company.employee_range",
        "company.revenue_range",
    }

    def __init__(self, repository: BaseCompetitorRepository):
        self.repo = repository

    def should_refresh(
        self,
        summary: Optional[CompanyCompetitorSummary],
        max_age_days: int = 90,
    ) -> bool:
        """Determines if a company's competitor graph should be refreshed due to age."""
        if not summary or not summary.last_refreshed_at:
            return True

        last_ref = parse_iso(summary.last_refreshed_at)
        if not last_ref:
            return True

        return (utc_now() - last_ref) > timedelta(days=max_age_days)

    def fact_change_impacts_competition(self, predicate: str) -> bool:
        """Checks whether a newly updated fact predicate justifies re-evaluating competitors."""
        return predicate in self.COMPETITION_IMPACTING_PREDICATES
