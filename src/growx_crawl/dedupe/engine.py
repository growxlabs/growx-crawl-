"""
GrowX Deduplication Engine (Compatibility Adapter).
Migrated to delegate matching logic to entity_resolution/ and normalization/.
Preserves 100% backward-compatible API for existing job and pipeline callers.
"""

from typing import Optional, Tuple
from growx_crawl.core.enums import MatchDecision
from growx_crawl.entity_resolution.company.matcher import CompanyMatcher
from growx_crawl.entity_resolution.thresholds import AUTO_MERGE_THRESHOLD, REVIEW_THRESHOLD
from growx_crawl.models.lead import Company, DedupeRecord
from growx_crawl.storage.repository import LeadRepository


class DeduplicationEngine:
    """Compatibility adapter forwarding deduplication requests to the Entity Resolution Subsystem."""

    def __init__(self, lead_repo: LeadRepository):
        self.lead_repo = lead_repo
        self.matcher = CompanyMatcher()

    def evaluate(self, company: Company) -> Tuple[bool, Optional[DedupeRecord], Optional[str]]:
        """
        Evaluates a candidate company against existing database records.
        Returns:
            (is_duplicate, dedupe_record, canonical_company_id)
        """
        existing_companies = self.lead_repo.list_job_companies(company.job_id)

        c1_dict = {
            "name": company.name,
            "domain": company.domain,
            "emails": company.emails,
            "phones": company.phones,
            "social_profiles": company.social_profiles,
            "city": company.city,
        }

        for existing in existing_companies:
            if existing.id == company.id:
                continue

            c2_dict = {
                "name": existing.name,
                "domain": existing.domain,
                "emails": existing.emails,
                "phones": existing.phones,
                "social_profiles": existing.social_profiles,
                "city": existing.city,
            }

            confidence, explanation = self.matcher.match(c1_dict, c2_dict)

            if confidence >= REVIEW_THRESHOLD:
                decision = (
                    MatchDecision.AUTO_MERGED
                    if confidence >= AUTO_MERGE_THRESHOLD
                    else MatchDecision.REVIEW_REQUIRED
                )
                signals = [s.name for s in explanation.signals]
                rec = DedupeRecord(
                    canonical_company_id=existing.id,
                    duplicate_company_id=company.id,
                    match_signals=signals,
                    confidence=confidence,
                    decision=decision,
                )
                return True, rec, existing.id

        return False, None, None
