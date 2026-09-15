from typing import Any, Dict, List, Optional
import yaml
from growx_crawl.core.config import settings
from growx_crawl.core.enums import PriorityLevel
from growx_crawl.core.industry import IndustryProfileRegistry
from growx_crawl.models.lead import Company, LeadCandidate


class LeadScorer:
    def __init__(self, profile_name: str = "general"):
        self.profile_name = profile_name
        self.industry_profile = IndustryProfileRegistry.get_profile(profile_name)
        self.config = {"priority_thresholds": {"high": 75, "medium": 50}}

    def score_lead(self, company: Company, target_location: Optional[str] = None) -> LeadCandidate:
        reasons: List[str] = []

        # 1. Target Fit (Max 30)
        target_fit = 0
        comp_ind = (company.industry or "").lower()
        if any(term in comp_ind for term in [self.industry_profile.name.lower()] + [a.lower() for a in self.industry_profile.aliases]):
            target_fit += 20
            reasons.append(f"+ Target industry '{self.industry_profile.name}' matched (+20)")
        elif comp_ind:
            target_fit += 10
            reasons.append("+ Industry present (+10)")

        if target_location and company.city and target_location.lower() in company.city.lower():
            target_fit += 10
            reasons.append(f"+ Target location '{target_location}' matched (+10)")

        # 2. Contactability (Max 25)
        contactability = 0
        if company.phones:
            contactability += 15
            reasons.append("+ Public phone number found (+15)")
        if company.emails:
            contactability += 10
            reasons.append("+ Public email found (+10)")

        # 3. Decision Maker (Max 20)
        dm_score = 0
        if company.contacts:
            top_contact = company.contacts[0]
            tier = top_contact.decision_maker_tier or "Tier 3"
            if tier == "Tier 1":
                dm_score = 20
                reasons.append(f"+ Tier 1 Decision Maker ({top_contact.title}) identified (+20)")
            elif tier == "Tier 2":
                dm_score = 15
                reasons.append(f"+ Tier 2 Decision Maker ({top_contact.title}) identified (+15)")
            else:
                dm_score = 10
                reasons.append(f"+ Contact person ({top_contact.title}) identified (+10)")

        # 4. Data Quality & Completeness (Max 15)
        data_quality = 0
        if company.address:
            data_quality += 5
            reasons.append("+ Address info available (+5)")
        if company.description:
            data_quality += 5
            reasons.append("+ Company description available (+5)")
        if company.rating:
            data_quality += 5
            reasons.append(f"+ Customer rating {company.rating}⭐ available (+5)")

        # 5. Digital Presence (Max 10)
        digital_presence = 0
        if company.website and not company.website_missing:
            digital_presence += 5
            reasons.append("+ Official website present (+5)")
        if company.social_profiles:
            digital_presence += 5
            reasons.append("+ Social profile present (+5)")

        total_score = min(target_fit + contactability + dm_score + data_quality + digital_presence, 100)

        thresholds = self.config.get("priority_thresholds", {"high": 75, "medium": 50})

        if total_score >= thresholds.get("high", 75):
            priority = PriorityLevel.HIGH
        elif total_score >= thresholds.get("medium", 50):
            priority = PriorityLevel.MEDIUM
        else:
            priority = PriorityLevel.LOW

        return LeadCandidate(
            company_id=company.id,
            job_id=company.job_id,
            score=total_score,
            priority=priority,
            score_reasons=reasons,
        )
