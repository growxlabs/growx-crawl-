"""
GrowX Verification Policies.
Standard rules governing data trustworthiness before AutoGTM or outreach consumption.
"""

from typing import Dict
from growx_crawl.verification.models import VerificationPolicy

POLICIES: Dict[str, VerificationPolicy] = {
    "strict": VerificationPolicy(
        name="strict",
        min_confidence=0.90,
        required_checks=["syntax", "mx_dns", "smtp_deliverable"],
        ttl_hours=72,
    ),
    "standard": VerificationPolicy(
        name="standard",
        min_confidence=0.80,
        required_checks=["syntax", "mx_dns"],
        ttl_hours=168,
    ),
    "permissive": VerificationPolicy(
        name="permissive",
        min_confidence=0.60,
        required_checks=["syntax"],
        ttl_hours=720,
    ),
}


def get_policy(name: str = "standard") -> VerificationPolicy:
    return POLICIES.get(name.lower(), POLICIES["standard"])
