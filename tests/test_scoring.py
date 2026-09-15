from growx_crawl.core.enums import PriorityLevel
from growx_crawl.models import Company, Email, Phone, SocialProfile
from growx_crawl.scoring import LeadScorer


def test_jewellery_lead_scoring():
    company = Company(
        job_id="job1",
        name="Royal Jewellers",
        normalized_name="royal jewellers",
        domain="royaljewellers.com",
        website="https://royaljewellers.com",
        industry="Jewellery",
        city="Hyderabad",
        source_url="https://royaljewellers.com",
        emails=[Email(company_id="", email="info@royaljewellers.com", normalized_email="info@royaljewellers.com", source_url="")],
        phones=[Phone(company_id="", phone="+914023456789", normalized_phone="+914023456789", raw_phone="+914023456789", source_url="")],
        social_profiles=[SocialProfile(company_id="", platform="instagram", url="https://instagram.com/royaljewellers", normalized_url="https://instagram.com/royaljewellers", source_url="")],
    )

    scorer = LeadScorer(profile_name="jewellery")
    lead = scorer.score_lead(company, target_location="Hyderabad")

    assert lead.score >= 60
    assert lead.priority in [PriorityLevel.HIGH, PriorityLevel.MEDIUM]
    assert len(lead.score_reasons) >= 4
