"""
GrowX Outreach Eligibility Profiles.
The highest-stakes gate: ensures email validity, suppression status, role checks, and freshness.
"""

OUTREACH_PROFILES = {
    "outreach_eligible": {
        "required_fields": ["email", "company_id"],
        "recommended_fields": ["person_id", "first_name", "title", "company_domain"],
        "min_completeness_ratio": 0.80,
        "allow_role_address": False,
        "allow_catchall": False,
        "require_verified_email": True,
        "min_email_confidence": 0.80,
        "suppression_check_mandatory": True,
        "max_email_age_hours": 168,  # 7 days max email verification age
    },
    "outreach_risk_tolerant": {
        "required_fields": ["email"],
        "recommended_fields": ["first_name", "company_domain"],
        "min_completeness_ratio": 0.60,
        "allow_role_address": True,
        "allow_catchall": True,
        "require_verified_email": False,
        "min_email_confidence": 0.50,
        "suppression_check_mandatory": True,
    },
}
