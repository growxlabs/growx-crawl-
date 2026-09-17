"""
GrowX Freshness Score Calculator.
Evaluates temporal currency of facts, employment, verification, and company records.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from growx_crawl.scoring.models import FreshnessResult, RankingReasonCode
from growx_crawl.scoring.policies import (
    STALE_COMPANY_FACT_DAYS,
    STALE_EMPLOYMENT_DAYS,
    normalize_score,
)


class FreshnessScoreCalculator:
    """Calculates data freshness and flags stale records requiring reverification."""

    def calculate(
        self,
        company_data: Dict[str, Any],
        person_data: Optional[Dict[str, Any]] = None,
    ) -> FreshnessResult:
        now = datetime.now(timezone.utc)
        reasons: List[str] = []
        penalties = 0.0

        # 1. Company fact freshness
        comp_date_str = company_data.get("updated_at") or company_data.get("last_verified_at")
        comp_age_days = 30  # Default assumption: 30 days
        if comp_date_str:
            try:
                dt = datetime.fromisoformat(str(comp_date_str).replace("Z", "+00:00"))
                comp_age_days = max(0, (now - dt).days)
            except Exception:
                pass

        is_stale_comp = comp_age_days > STALE_COMPANY_FACT_DAYS
        if is_stale_comp:
            reasons.append(RankingReasonCode.STALE_COMPANY_SIZE.value)
            penalties += 0.15

        # 2. Person employment freshness
        emp_age_days = 30
        is_stale_emp = False
        if person_data:
            emp_date_str = person_data.get("updated_at") or person_data.get("last_verified_at") or person_data.get("verified_at")
            if emp_date_str:
                try:
                    dt = datetime.fromisoformat(str(emp_date_str).replace("Z", "+00:00"))
                    emp_age_days = max(0, (now - dt).days)
                except Exception:
                    pass

            is_stale_emp = emp_age_days > STALE_EMPLOYMENT_DAYS
            if is_stale_emp:
                reasons.append(RankingReasonCode.STALE_EMPLOYMENT.value)
                penalties += 0.25

        # Freshness rating: 1.0 (fresh) down to 0.2 (very old)
        max_age = max(comp_age_days, emp_age_days)
        overall = max(0.2, 1.0 - (max_age / 365.0))

        return FreshnessResult(
            overall_freshness=normalize_score(overall),
            fact_freshness_days=comp_age_days,
            employment_freshness_days=emp_age_days,
            is_stale_employment=is_stale_emp,
            is_stale_company=is_stale_comp,
            reason_codes=reasons,
            penalties=penalties,
        )
