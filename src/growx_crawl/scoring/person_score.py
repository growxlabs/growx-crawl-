"""
GrowX Person Score Calculator.
Computes buyer-level priority combining persona fit, seniority tier, role relevance, and employment confidence.
"""

from typing import Any, Dict, List, Optional
from growx_crawl.scoring.models import PersonScoreResult, RankingReasonCode
from growx_crawl.scoring.policies import SENIORITY_TIER_SCORES, normalize_score


class PersonScoreCalculator:
    """Calculates buyer/contact-level priority score and audit contributions."""

    def calculate(
        self,
        person_data: Optional[Dict[str, Any]] = None,
        persona_score: Optional[float] = None,
        matched_role: Optional[str] = None,
    ) -> PersonScoreResult:
        if not person_data and persona_score is None:
            # Default baseline when scoring company prior to contact selection
            return PersonScoreResult(
                score=0.5,
                persona_fit=0.5,
                seniority_score=0.5,
                role_relevance=0.5,
                employment_confidence=1.0,
                contributions={"baseline": 0.5},
            )

        data = person_data or {}
        reasons: List[str] = []
        contributions: Dict[str, float] = {}

        # 1. Persona Fit (45% of person component)
        p_fit = float(persona_score) if persona_score is not None else float(data.get("fit_score", 0.6))
        p_fit = normalize_score(p_fit)
        if p_fit >= 0.75:
            reasons.append(RankingReasonCode.STRONG_PERSONA_MATCH.value)
        contributions["persona_fit"] = round(p_fit * 0.45, 3)

        # 2. Seniority Tier (30% of person component)
        title = str(data.get("title", "")).lower()
        seniority = self._resolve_seniority(title)
        contributions["seniority"] = round(seniority * 0.30, 3)

        # 3. Role Relevance / Buyer Category (15% of person component)
        role = matched_role or data.get("role_matched") or self._infer_role(title)
        role_rel = self._evaluate_role_relevance(role)
        contributions["role_relevance"] = round(role_rel * 0.15, 3)

        # 4. Employment Confidence (10% of person component)
        emp_conf = float(data.get("employment_confidence", 1.0))
        emp_conf = normalize_score(emp_conf)
        if emp_conf >= 0.85:
            reasons.append(RankingReasonCode.CURRENT_EMPLOYMENT.value)
        contributions["employment_confidence"] = round(emp_conf * 0.10, 3)

        total_person = sum(contributions.values())

        return PersonScoreResult(
            score=normalize_score(total_person),
            persona_fit=p_fit,
            seniority_score=seniority,
            role_relevance=role_rel,
            employment_confidence=emp_conf,
            matched_role=role,
            reason_codes=reasons,
            contributions=contributions,
        )

    def _resolve_seniority(self, title: str) -> float:
        if not title:
            return 0.5
        t = title.lower()
        if any(w in t for w in ["chief", "cto", "ceo", "cro", "cmo", "cfo", "founder", "co-founder", "president"]):
            return SENIORITY_TIER_SCORES["c_suite"]
        if any(w in t for w in ["vp", "vice president"]):
            return SENIORITY_TIER_SCORES["vp"]
        if any(w in t for w in ["director", "head"]):
            return SENIORITY_TIER_SCORES["director"]
        if any(w in t for w in ["manager", "lead", "supervisor"]):
            return SENIORITY_TIER_SCORES["manager"]
        return SENIORITY_TIER_SCORES["individual_contributor"]

    def _infer_role(self, title: str) -> str:
        t = title.lower()
        if any(w in t for w in ["tech", "engineer", "dev", "cto", "architect"]):
            return "technical_buyer"
        if any(w in t for w in ["sales", "cro", "revenue", "commercial"]):
            return "economic_buyer"
        if any(w in t for w in ["ops", "operations", "coo"]):
            return "operational_buyer"
        return "champion"

    def _evaluate_role_relevance(self, role: str) -> float:
        r = str(role).lower()
        if "economic" in r:
            return 1.0
        if "technical" in r:
            return 0.95
        if "operational" in r:
            return 0.85
        return 0.75
