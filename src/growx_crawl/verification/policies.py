"""
GrowX Verification Policy Registry.
Manages subject-specific verification policies, required checks, and validity TTLs.
"""

from typing import Dict, Optional
from growx_crawl.verification.models import VerificationPolicy

STANDARD_POLICIES: Dict[str, VerificationPolicy] = {
    "company_default_v1": VerificationPolicy(
        id="pol_comp_v1",
        name="company_default_v1",
        subject_type="company",
        version="v1",
        min_confidence=0.80,
        required_checks=["name_exists", "domain_active"],
        ttl_hours=4320,  # 180 days
    ),
    "domain_default_v1": VerificationPolicy(
        id="pol_dom_v1",
        name="domain_default_v1",
        subject_type="domain",
        version="v1",
        min_confidence=0.80,
        required_checks=["dns_resolves", "http_reachable"],
        ttl_hours=720,  # 30 days
    ),
    "company_domain_default_v1": VerificationPolicy(
        id="pol_compdom_v1",
        name="company_domain_default_v1",
        subject_type="company_domain",
        version="v1",
        min_confidence=0.85,
        required_checks=["domain_ownership", "name_match"],
        ttl_hours=2160,  # 90 days
    ),
    "person_default_v1": VerificationPolicy(
        id="pol_per_v1",
        name="person_default_v1",
        subject_type="person",
        version="v1",
        min_confidence=0.75,
        required_checks=["name_valid", "profile_presence"],
        ttl_hours=2160,  # 90 days
    ),
    "employment_default_v1": VerificationPolicy(
        id="pol_emp_v1",
        name="employment_default_v1",
        subject_type="employment",
        version="v1",
        min_confidence=0.80,
        required_checks=["email_domain_match"],
        ttl_hours=2160,  # 90 days
    ),
    "email_default_v1": VerificationPolicy(
        id="pol_email_v1",
        name="email_default_v1",
        subject_type="email",
        version="v1",
        min_confidence=0.85,
        required_checks=["syntax", "mx_dns"],
        ttl_hours=720,  # 30 days
    ),
    "fact_default_v1": VerificationPolicy(
        id="pol_fact_v1",
        name="fact_default_v1",
        subject_type="fact",
        version="v1",
        min_confidence=0.75,
        required_checks=["evidence_provenance"],
        ttl_hours=2160,  # 90 days
    ),
}

# Legacy aliases
POLICIES: Dict[str, VerificationPolicy] = {
    "strict": STANDARD_POLICIES["email_default_v1"],
    "standard": STANDARD_POLICIES["company_default_v1"],
    "permissive": STANDARD_POLICIES["fact_default_v1"],
    **STANDARD_POLICIES,
}


def get_policy(name_or_subject: str = "standard") -> VerificationPolicy:
    """Retrieves policy by exact policy name, subject type, or fallback standard."""
    key = name_or_subject.lower().strip()
    if key in POLICIES:
        return POLICIES[key]

    # Map subject type to default policy
    subject_key = f"{key}_default_v1"
    if subject_key in POLICIES:
        return POLICIES[subject_key]

    return POLICIES["standard"]
