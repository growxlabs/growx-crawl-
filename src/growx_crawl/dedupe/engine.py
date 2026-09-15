from typing import Optional, Tuple
from growx_crawl.core.enums import MatchDecision
from growx_crawl.models.lead import Company, DedupeRecord
from growx_crawl.normalization.normalizer import Normalizer
from growx_crawl.storage.repository import LeadRepository


class DeduplicationEngine:
    def __init__(self, lead_repo: LeadRepository):
        self.lead_repo = lead_repo

    def evaluate(self, company: Company) -> Tuple[bool, Optional[DedupeRecord], Optional[str]]:
        """
        Evaluates a candidate company against existing database records.
        Returns:
            (is_duplicate, dedupe_record, canonical_company_id)
        """
        existing_companies = self.lead_repo.list_job_companies(company.job_id)

        for existing in existing_companies:
            if existing.id == company.id:
                continue

            signals = []
            confidence = 0.0

            # Signal 1: Same domain
            if company.domain and existing.domain and company.domain == existing.domain:
                signals.append("same_domain")
                confidence = 1.0

            # Signal 2: Same normalized email
            if not confidence:
                company_emails = {e.normalized_email for e in company.emails if e.normalized_email}
                existing_emails = {e.normalized_email for e in existing.emails if e.normalized_email}
                if company_emails and existing_emails and company_emails.intersection(existing_emails):
                    signals.append("same_normalized_email")
                    confidence = 0.95

            # Signal 3: Same normalized phone
            if not confidence:
                company_phones = {p.normalized_phone for p in company.phones if p.normalized_phone}
                existing_phones = {p.normalized_phone for p in existing.phones if p.normalized_phone}
                if company_phones and existing_phones and company_phones.intersection(existing_phones):
                    signals.append("same_normalized_phone")
                    confidence = 0.95

            # Signal 4: Same social profile URL
            if not confidence:
                company_soc = {s.normalized_url for s in company.social_profiles if s.normalized_url}
                existing_soc = {s.normalized_url for s in existing.social_profiles if s.normalized_url}
                if company_soc and existing_soc and company_soc.intersection(existing_soc):
                    signals.append("same_social_url")
                    confidence = 0.90

            # Signal 5: Same name + city
            if not confidence:
                k1 = Normalizer.normalize_company_name_key(company.name)
                k2 = Normalizer.normalize_company_name_key(existing.name)
                if k1 and k1 == k2 and company.city and existing.city and company.city.lower() == existing.city.lower():
                    signals.append("same_name_and_city")
                    confidence = 0.75

            if confidence >= 0.70:
                decision = MatchDecision.AUTO_MERGED if confidence >= 0.90 else MatchDecision.REVIEW_REQUIRED
                rec = DedupeRecord(
                    canonical_company_id=existing.id,
                    duplicate_company_id=company.id,
                    match_signals=signals,
                    confidence=confidence,
                    decision=decision,
                )
                return True, rec, existing.id

        return False, None, None
