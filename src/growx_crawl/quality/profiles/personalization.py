"""
GrowX Personalization Quality Profiles.
Ensures seller context, target facts, and evidence hooks meet quality standards before LLM copywriting.
"""

PERSONALIZATION_PROFILES = {
    "personalization_ready": {
        "required_fields": ["company_name", "lead_name", "sender_offer"],
        "recommended_fields": ["title", "company_domain", "personalization_hook", "value_proposition"],
        "min_completeness_ratio": 0.75,
        "max_fact_age_days": 180,
        "require_evidence_grounding": True,
        "min_fact_confidence": 0.70,
    },
}
