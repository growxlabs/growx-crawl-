"""
GrowX Contactability Calculator.
Evaluates email validity, corporate deliverability, role mailbox penalties, and suppression status.
"""

from typing import Any, Dict, List, Optional
from growx_crawl.scoring.models import ContactabilityResult, RankingReasonCode
from growx_crawl.scoring.policies import normalize_score

ROLE_MAILBOX_PREFIXES = {
    "info", "sales", "support", "contact", "admin", "team", "help",
    "marketing", "billing", "careers", "jobs", "office", "general"
}

GENERIC_MAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com", "aol.com"
}


class ContactabilityCalculator:
    """Calculates outreach deliverability and contact accessibility."""

    def calculate(
        self,
        person_data: Optional[Dict[str, Any]] = None,
        company_data: Optional[Dict[str, Any]] = None,
    ) -> ContactabilityResult:
        if not person_data:
            # When scoring account without contact attached
            return ContactabilityResult(
                score=0.5,
                is_suppressed=False,
                is_valid_email=True,
                email_type="unknown",
                reason_codes=[],
                contributions={"baseline": 0.5},
            )

        reasons: List[str] = []
        contributions: Dict[str, float] = {}

        # 1. Suppression check (Section 71)
        is_suppressed = bool(person_data.get("suppressed") or person_data.get("is_suppressed"))
        if is_suppressed:
            reasons.append(RankingReasonCode.SUPPRESSED_CONTACT.value)
            return ContactabilityResult(
                score=0.0,
                is_suppressed=True,
                is_valid_email=True,
                email_type="suppressed",
                reason_codes=reasons,
                contributions={"suppressed": -1.0},
            )

        # 2. Email verification & deliverability
        email = str(person_data.get("email") or "").strip().lower()
        if not email:
            reasons.append(RankingReasonCode.MISSING_EMAIL.value)
            reasons.append(RankingReasonCode.WEAK_CONTACTABILITY.value)
            return ContactabilityResult(
                score=0.20,
                is_suppressed=False,
                is_valid_email=False,
                email_type="missing",
                reason_codes=reasons,
                contributions={"missing_email": -0.5},
            )

        # Basic format sanity check
        if "@" not in email or "." not in email.split("@")[-1]:
            reasons.append(RankingReasonCode.INVALID_EMAIL.value)
            return ContactabilityResult(
                score=0.0,
                is_suppressed=False,
                is_valid_email=False,
                email_type="invalid",
                reason_codes=reasons,
                contributions={"invalid_email": -1.0},
            )

        user_part, domain_part = email.split("@", 1)

        # Check explicit verification status
        ver_status = str(person_data.get("email_verification_status", "valid")).lower()
        if ver_status in ("invalid", "bounced", "undeliverable"):
            reasons.append(RankingReasonCode.INVALID_EMAIL.value)
            return ContactabilityResult(
                score=0.0,
                is_suppressed=False,
                is_valid_email=False,
                email_type="invalid",
                reason_codes=reasons,
                contributions={"invalid_email": -1.0},
            )

        # Base valid email score
        score = 1.0
        email_type = "corporate"
        reasons.append(RankingReasonCode.EMAIL_VALID.value)

        # 3. Role mailbox penalty
        if user_part in ROLE_MAILBOX_PREFIXES:
            score -= 0.35
            email_type = "role_mailbox"
            reasons.append(RankingReasonCode.ROLE_MAILBOX_PENALTY.value)

        # 4. Personal/generic mailbox penalty
        if domain_part in GENERIC_MAIL_DOMAINS:
            score -= 0.30
            email_type = "personal"

        # 5. Catch-all domain penalty
        if person_data.get("is_catch_all"):
            score -= 0.15
            reasons.append(RankingReasonCode.CATCH_ALL_PENALTY.value)

        final_score = normalize_score(max(0.1, score))
        contributions["deliverability"] = final_score

        return ContactabilityResult(
            score=final_score,
            is_suppressed=False,
            is_valid_email=True,
            email_type=email_type,
            reason_codes=reasons,
            contributions=contributions,
        )
