"""
GrowX Prospect Eligibility Profiles.
Defines required fields, verification bars, and completeness rules before entering prospect pipeline.
"""

PROSPECT_PROFILES = {
    "company_research_ready": {
        "required_fields": ["name", "domain"],
        "recommended_fields": ["industry", "description", "target_audience", "city", "country_code"],
        "min_completeness_ratio": 0.60,
        "require_company_verification": True,
        "min_verification_confidence": 0.75,
    },
    "prospect_eligible": {
        "required_fields": ["name", "domain"],
        "recommended_fields": ["industry", "description", "emails", "phones", "address"],
        "min_completeness_ratio": 0.70,
        "require_company_verification": True,
        "min_verification_confidence": 0.80,
    },
}
