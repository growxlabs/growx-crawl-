"""
GrowX Canonical Ingestion Profiles.
Defines required attributes and minimum sanity checks before raw data enters canonical storage.
"""

from typing import Dict, List


CANONICAL_INGESTION_PROFILES = {
    "company_minimal": {
        "required_fields": ["name"],
        "recommended_fields": ["domain", "industry", "city", "country_code"],
        "min_completeness_ratio": 0.50,
        "allow_unverified": True,
    },
    "fact_minimal": {
        "required_fields": ["subject_type", "subject_id", "predicate", "observed_at", "source_id"],
        "recommended_fields": ["raw_value", "extractor_name", "evidence_ids"],
        "min_completeness_ratio": 0.80,
    },
}
