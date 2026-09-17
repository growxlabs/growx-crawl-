"""
GrowX Account Score Calculator.
Computes account-level priority combining ICP fit, company verification, data quality, and momentum.
"""

from typing import Any, Dict, List, Optional
from growx_crawl.scoring.models import AccountScoreResult, RankingReasonCode
from growx_crawl.scoring.policies import normalize_score


class AccountScoreCalculator:
    """Calculates account-level priority score and audit contributions."""

    def calculate(
        self,
        company_data: Dict[str, Any],
        icp_fit: Optional[float] = None,
        verification_score: Optional[float] = None,
        quality_score: Optional[float] = None,
        historical_summary: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> AccountScoreResult:
        reasons: List[str] = []
        contributions: Dict[str, float] = {}

        # 1. ICP Fit (Primary driver: 55% of account component)
        fit_raw = icp_fit if icp_fit is not None else kwargs.get("icp_score")
        fit = float(fit_raw) if fit_raw is not None else float(company_data.get("fit_score", 0.5))
        fit = normalize_score(fit)
        if fit >= 0.75:
            reasons.append(RankingReasonCode.HIGH_ICP_FIT.value)
        contributions["icp_fit"] = round(fit * 0.55, 3)

        # 2. Company Verification (20% of account component)
        if verification_score is not None:
            v_score = float(verification_score)
        elif "is_verified" in company_data:
            v_score = 1.0 if company_data["is_verified"] else 0.3
        else:
            v_status = str(company_data.get("verification_status", "verified")).lower()
            if v_status in ("verified", "pass", "active"):
                v_score = 1.0
            elif v_status in ("pending", "in_progress", "unknown"):
                v_score = 0.7
            else:
                v_score = 0.3
        v_score = normalize_score(v_score)
        if v_score >= 0.85:
            reasons.append(RankingReasonCode.VERIFIED_COMPANY.value)
        contributions["verification"] = round(v_score * 0.20, 3)

        # 3. Data Quality Score (15% of account component)
        if quality_score is not None:
            q_score = float(quality_score)
        elif "quality_gate_passed" in company_data:
            q_score = 0.95 if company_data["quality_gate_passed"] else 0.35
        elif "quality_status" in company_data:
            q_score = 0.95 if str(company_data["quality_status"]).lower() in ("passed", "pass") else 0.35
        else:
            q_score = float(company_data.get("quality_score", 0.90))
        q_score = normalize_score(q_score)
        contributions["quality"] = round(q_score * 0.15, 3)

        # 4. Historical Momentum (10% of account component)
        m_score = 0.5
        hist = historical_summary or {}
        growth = hist.get("employee_growth_90d") or company_data.get("growth_rate")
        if growth and float(growth) >= 20.0:
            m_score = 1.0
            reasons.append(RankingReasonCode.ACTIVE_GROWTH_PATTERN.value)
        elif hist.get("change_count_90d", 0) >= 3:
            m_score = 0.8
        contributions["momentum"] = round(m_score * 0.10, 3)

        total_account = sum(contributions.values())

        return AccountScoreResult(
            score=normalize_score(total_account),
            icp_fit=fit,
            verification_score=v_score,
            quality_score=q_score,
            momentum_score=m_score,
            reason_codes=reasons,
            contributions=contributions,
        )
