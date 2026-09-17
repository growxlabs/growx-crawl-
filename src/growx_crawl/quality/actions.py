"""
GrowX Quality Required Actions.
Defines explicit remediation actions returned when a data quality gate fails or requires reverification.
Enables efficient, targeted repair loops instead of repeating the entire pipeline.
"""

from enum import Enum
from typing import List


class RequiredAction(str, Enum):
    REVERIFY_EMAIL = "reverify_email"
    REFRESH_EMPLOYMENT = "refresh_employment"
    RESEARCH_COMPANY = "research_company"
    RESOLVE_IDENTITY = "resolve_identity"
    COLLECT_MORE_EVIDENCE = "collect_more_evidence"
    VERIFY_COMPANY = "verify_company"
    VERIFY_DOMAIN = "verify_domain"
    REVERIFY_DOMAIN = "reverify_domain"
    CHECK_SUPPRESSION = "check_suppression"
    SUPPRESS = "suppress"
    DEDUPLICATE = "deduplicate"
    REPROCESS_QUARANTINE = "reprocess_quarantine"
    UPDATE_CONTACT_INFO = "update_contact_info"


def map_reasons_to_actions(reasons: List[str]) -> List[str]:
    """Deterministically maps failure reason codes to recommended repair actions."""
    actions = []
    reason_set = set(reasons)

    if "EMAIL_UNVERIFIED" in reason_set or "EMAIL_CATCHALL" in reason_set:
        actions.append(RequiredAction.REVERIFY_EMAIL.value)
    if "EMAIL_SUPPRESSED" in reason_set:
        actions.append(RequiredAction.SUPPRESS.value)
    if "DUPLICATE_PROSPECT" in reason_set:
        actions.append(RequiredAction.DEDUPLICATE.value)
    if "STALE_EMPLOYMENT" in reason_set or "EMPLOYMENT_UNKNOWN" in reason_set:
        actions.append(RequiredAction.REFRESH_EMPLOYMENT.value)
    if "COMPANY_UNVERIFIED" in reason_set:
        actions.append(RequiredAction.VERIFY_COMPANY.value)
    if "DOMAIN_UNVERIFIED" in reason_set:
        actions.append(RequiredAction.VERIFY_DOMAIN.value)
    if "DOMAIN_STALE" in reason_set:
        actions.append(RequiredAction.REVERIFY_DOMAIN.value)
    if "MISSING_PRIMARY_DOMAIN" in reason_set or "DOMAIN_UNREACHABLE" in reason_set:
        actions.append(RequiredAction.VERIFY_DOMAIN.value)
    if "UNRESOLVED_ENTITY_CONFLICT" in reason_set or "HARD_IDENTITY_CONFLICT" in reason_set or "MISSING_CANONICAL_IDENTITY" in reason_set:
        actions.append(RequiredAction.RESOLVE_IDENTITY.value)
    if "INSUFFICIENT_EVIDENCE" in reason_set or "LOW_FACT_CONFIDENCE" in reason_set:
        actions.append(RequiredAction.COLLECT_MORE_EVIDENCE.value)
    if "PROFILE_INCOMPLETE" in reason_set:
        actions.append(RequiredAction.RESEARCH_COMPANY.value)
    if "MALFORMED_OBSERVATION" in reason_set or "QUARANTINE_RECORDED" in reason_set:
        actions.append(RequiredAction.REPROCESS_QUARANTINE.value)

    return list(dict.fromkeys(actions))
