"""
GrowX Verification Gate.
Answers: 'Can downstream AutoGTM or GrowX Mail consume this prospect?'
Evaluates combined verification readiness into:
- ALLOW
- ALLOW_WITH_RISK
- REVERIFY
- BLOCK
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from growx_crawl.verification.models import (
    GateDecision,
    ReasonCode,
    VerificationResultEntity,
    VerificationStatus,
)


class GateEvaluation(BaseModel):
    decision: GateDecision
    confidence: float
    reasons: List[str] = Field(default_factory=list)
    blocking_reasons: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    refresh_recommended: bool = False


class VerificationGate:
    """The canonical trust gate safeguarding AutoGTM, campaigns, and outbound email."""

    @classmethod
    def evaluate(
        cls,
        company_res: Optional[VerificationResultEntity] = None,
        person_res: Optional[VerificationResultEntity] = None,
        employment_res: Optional[VerificationResultEntity] = None,
        email_res: Optional[VerificationResultEntity] = None,
    ) -> GateEvaluation:
        reasons: List[str] = []
        blocking: List[str] = []
        risks: List[str] = []
        refresh_needed = False

        # 1. Email Checks (Hardest Gate)
        if email_res:
            if email_res.status in (VerificationStatus.INVALID, VerificationStatus.FAILED):
                blocking.append("Email is invalid or undeliverable")
            elif email_res.status == VerificationStatus.SUPPRESSED:
                blocking.append("Email address is suppressed")
            elif email_res.details_json.get("role_address"):
                risks.append("Email is a generic role mailbox (e.g. info@, sales@)")
            elif email_res.details_json.get("catch_all"):
                risks.append("Domain is configured with catch-all acceptance")

        # 2. Company Checks
        if company_res:
            if company_res.status in (VerificationStatus.INVALID, VerificationStatus.FAILED):
                blocking.append("Company existence could not be verified")
            elif company_res.status == VerificationStatus.UNREACHABLE:
                blocking.append("Company official domain is unreachable")
            elif company_res.status == VerificationStatus.UNCERTAIN:
                risks.append("Company identity verification is uncertain")

        # 3. Employment Checks
        if employment_res:
            if employment_res.status == VerificationStatus.STALE:
                refresh_needed = True
                risks.append("Employment record is older than 365 days (stale)")
            elif employment_res.status == VerificationStatus.CONFLICTING:
                blocking.append("Conflicting employment records detected")
            elif employment_res.status in (VerificationStatus.UNVERIFIED, VerificationStatus.UNCERTAIN):
                refresh_needed = True
                risks.append("Employment association is unverified")

        # 4. Person Checks
        if person_res:
            if person_res.status in (VerificationStatus.INVALID, VerificationStatus.FAILED):
                blocking.append("Person identity record is malformed or invalid")
            elif person_res.status == VerificationStatus.UNCERTAIN:
                risks.append("Person public profile presence is limited")

        # Decision synthesis
        if blocking:
            decision = GateDecision.BLOCK
            reasons = blocking
        elif refresh_needed:
            decision = GateDecision.REVERIFY
            reasons = ["Re-verification required: " + "; ".join(risks)]
        elif risks:
            decision = GateDecision.ALLOW_WITH_RISK
            reasons = ["Allowed with operational risk: " + "; ".join(risks)]
        else:
            decision = GateDecision.ALLOW
            reasons = ["All critical entities (Company, Person, Employment, Email) verified"]

        # Aggregate composite confidence
        res_list = [r for r in (company_res, person_res, employment_res, email_res) if r]
        avg_conf = sum(r.confidence for r in res_list) / len(res_list) if res_list else 0.5

        return GateEvaluation(
            decision=decision,
            confidence=round(avg_conf, 2),
            reasons=reasons,
            blocking_reasons=blocking,
            risk_factors=risks,
            refresh_recommended=refresh_needed,
        )


verification_gate = VerificationGate()
