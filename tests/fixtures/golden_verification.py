"""
GrowX Golden Verification Dataset.
Provides standardized, labeled fixture records across all subject types:
- active company vs inactive company
- active domain vs parked domain
- valid employment vs ended/stale employment
- valid email vs catch-all email vs invalid email
- supported fact vs conflicting fact vs stale fact
"""

GOLDEN_COMPANIES = {
    "active_valid": {
        "id": "cmp_golden_active",
        "name": "Stripe Inc",
        "domain": "stripe.com",
        "emails": ["support@stripe.com"],
        "phones": ["+18889262289"],
        "description": "Financial infrastructure for the internet",
        "expected_status": "verified",
        "min_confidence": 0.85,
    },
    "inactive_malformed": {
        "id": "cmp_golden_dead",
        "name": "",  # Missing name
        "domain": "nonexistent-xyz-987654321-dead.org",
        "expected_status": "invalid",
        "max_confidence": 0.20,
    },
}

GOLDEN_DOMAINS = {
    "active_domain": {
        "domain": "google.com",
        "expected_status": "verified",
        "dns_ok": True,
        "http_ok": True,
        "parking_detected": False,
    },
    "parked_domain": {
        "domain": "buy-this-domain-now-example-parking.com",
        "mock_body": "This domain is for sale. Buy this domain on Sedo domain parking.",
        "expected_status": "uncertain",
        "parking_detected": True,
    },
    "unreachable_domain": {
        "domain": "unreachable-fake-tld-999888777.xyzinvalid",
        "expected_status": "unreachable",
        "dns_ok": False,
    },
}

GOLDEN_EMPLOYMENTS = {
    "current_valid": {
        "person_id": "per_rahul",
        "company_id": "cmp_growx",
        "person_email": "rahul@growxlabs.com",
        "company_domain": "growxlabs.com",
        "on_team_page": True,
        "observed_at_iso": "2026-08-01T00:00:00Z",  # Recent (~45 days)
        "expected_status": "verified",
        "expected_state": "current_verified",
    },
    "stale_employment": {
        "person_id": "per_old",
        "company_id": "cmp_growx",
        "person_email": "old@growxlabs.com",
        "company_domain": "growxlabs.com",
        "on_team_page": False,
        "observed_at_iso": "2024-01-01T00:00:00Z",  # > 900 days ago
        "expected_status": "stale",
        "expected_state": "stale",
    },
    "domain_mismatched": {
        "person_id": "per_wrong",
        "company_id": "cmp_growx",
        "person_email": "wrong@othercompany.com",
        "company_domain": "growxlabs.com",
        "on_team_page": False,
        "expected_status": "uncertain",
    },
}

GOLDEN_EMAILS = {
    "valid_corporate": {
        "email": "patrick@stripe.com",
        "expected_syntax": True,
        "is_role": False,
        "is_free": False,
    },
    "role_address": {
        "email": "support@stripe.com",
        "expected_syntax": True,
        "is_role": True,
        "is_free": False,
    },
    "free_provider": {
        "email": "john.doe@gmail.com",
        "expected_syntax": True,
        "is_role": False,
        "is_free": True,
    },
    "invalid_syntax": {
        "email": "not-an-email",
        "expected_syntax": False,
        "expected_status": "invalid",
    },
}

GOLDEN_FACTS = {
    "supported_fact": {
        "fact_id": "fct_golden_emp_count",
        "predicate": "company.employee_count",
        "confidence": 0.90,
        "has_evidence": True,
        "evidence_ids": ["evd_1", "evd_2"],
        "expected_status": "verified",
    },
    "conflicting_fact": {
        "fact_id": "fct_golden_conflict",
        "predicate": "company.founded_year",
        "confidence": 0.60,
        "status": "conflicting",
        "has_conflict": True,
        "expected_status": "conflicting",
    },
    "stale_fact": {
        "fact_id": "fct_golden_stale",
        "predicate": "person.job_title",
        "confidence": 0.85,
        "has_evidence": True,
        "created_at": "2024-01-01T00:00:00Z",
        "expected_status": "stale",
    },
}
