"""
Golden test fixtures for GrowX Data Quality Gates (Phase 08).
Provides structured scenarios for all 5 quality gate tiers:
1. Canonical Ingestion
2. Intelligence Trust
3. Prospect Eligibility
4. Personalization Eligibility
5. Outreach Eligibility
"""

from typing import Any, Dict

GOLDEN_CANONICAL_SCENARIOS = {
    "valid_observation": {
        "subject_type": "company",
        "subject_id": "cmp_acme_001",
        "name": "Acme Corp",
        "domain": "acme.com",
        "primary_domain": "acme.com",
        "source": "crawl_engine",
    },
    "missing_identity": {
        # missing subject_type and subject_id
        "name": "Ghost Entity",
    },
    "hard_identity_conflict": {
        "subject_type": "company",
        "subject_id": "cmp_conflict_001",
        "has_hard_conflict": True,
        "conflict_type": "domain_clash",
    },
}

GOLDEN_INTELLIGENCE_SCENARIOS = {
    "trusted_fact": {
        "subject_type": "fact",
        "subject_id": "fct_rev_2025",
        "predicate": "revenue_estimate",
        "value": "$50M",
        "confidence": 0.95,
        "evidence_count": 3,
        "status": "active",
    },
    "insufficient_evidence": {
        "subject_type": "fact",
        "subject_id": "fct_unproven",
        "predicate": "employee_count",
        "value": 500,
        "confidence": 0.85,
        "evidence_count": 0,
        "status": "active",
    },
    "low_confidence": {
        "subject_type": "fact",
        "subject_id": "fct_rumor",
        "predicate": "funding_series_b",
        "value": "$15M",
        "confidence": 0.35,
        "evidence_count": 1,
        "status": "active",
    },
    "stale_fact": {
        "subject_type": "fact",
        "subject_id": "fct_old_data",
        "predicate": "headquarters",
        "value": "Austin, TX",
        "confidence": 0.90,
        "evidence_count": 2,
        "status": "stale",
    },
}

GOLDEN_PROSPECT_SCENARIOS = {
    "eligible_prospect": {
        "id": "prsp_marcus_vance",
        "name": "Hexagon Data",
        "domain": "hexagondata.io",
        "industry": "Enterprise Software",
        "description": "Cloud data warehouse modern pipeline orchestrator",
        "city": "Austin",
        "verification_status": "verified",
        "verification_confidence": 0.95,
    },
    "duplicate_prospect": {
        "id": "prsp_existing_001",
        "name": "Hexagon Data",
        "domain": "hexagondata.io",
    },
    "missing_domain": {
        "id": "prsp_no_domain",
        "name": "Nameless Venture",
        # missing domain
    },
    "unverified_prospect": {
        "id": "prsp_unverified_co",
        "name": "Unverified Stealth",
        "domain": "stealthmode.xyz",
        "verification_status": "unverified",
        "verification_confidence": 0.40,
    },
    "stale_verification": {
        "id": "prsp_stale_co",
        "name": "Aging Systems",
        "domain": "agingsystems.com",
        "verification_status": "stale",
        "verification_confidence": 0.60,
    },
}

GOLDEN_PERSONALIZATION_SCENARIOS = {
    "ready_for_drafting": {
        "company_name": "Synthex AI",
        "lead_name": "Elena Rostova",
        "sender_offer": "Autonomous sales prospect discovery and verification",
        "personalization_hook": "Recent launch of enterprise agent orchestration and expanding European GTM",
    },
    "missing_required_context": {
        "company_name": "Synthex AI",
        # missing lead_name and sender_offer
    },
    "missing_hook": {
        "company_name": "Synthex AI",
        "lead_name": "Elena Rostova",
        "sender_offer": "GrowX Crawl platform",
        "personalization_hook": "",  # empty hook
    },
}

GOLDEN_OUTREACH_SCENARIOS = {
    "outreach_ready": {
        "email": "elena.rostova@synthex.ai",
        "email_status": "verified",
        "employment_status": "verified",
        "is_role": False,
        "is_catchall": False,
    },
    "suppressed_recipient": {
        "email": "do-not-contact@competitor.com",
        "email_status": "verified",
    },
    "stale_employment": {
        "email": "david.sterling@cloudforge.tech",
        "email_status": "verified",
        "employment_status": "stale",
    },
    "role_account": {
        "email": "info@cloudforge.tech",
        "email_status": "verified",
        "is_role": True,
    },
    "catchall_domain": {
        "email": "contact@velocesystems.com",
        "email_status": "verified",
        "is_catchall": True,
    },
    "unverified_email": {
        "email": "unknown@apexmetrics.io",
        "email_status": "unverified",
    },
    "missing_email": {
        "email": "",
    },
}
