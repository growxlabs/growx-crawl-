from growx_crawl.crawler.page_classifier import PageClassifier
from growx_crawl.enrichment.bde_brief import BDEBriefGenerator
from growx_crawl.extractors.digital_presence import DigitalPresenceExtractor
from growx_crawl.extractors.schema_org import SchemaOrgExtractor
from growx_crawl.models import Company, Contact, Email, FetchedPage, Phone, SocialProfile
from growx_crawl.scoring.scorer import LeadScorer


def test_page_classifier():
    p1 = FetchedPage(job_id="j1", target_id="t1", url="https://example.com/about-us", status_code=200, html_content="<html></html>")
    assert PageClassifier.classify(p1) == "about"

    p2 = FetchedPage(job_id="j1", target_id="t1", url="https://example.com/contact", status_code=200, html_content="<html></html>")
    assert PageClassifier.classify(p2) == "contact"

    p3 = FetchedPage(job_id="j1", target_id="t1", url="https://example.com/our-team", status_code=200, html_content="<html></html>")
    assert PageClassifier.classify(p3) == "leadership"


def test_digital_presence_extractor():
    p = FetchedPage(
        job_id="j1",
        target_id="t1",
        url="https://example.com/shop",
        status_code=200,
        html_content="<html><body><a href='https://wa.me/919876543210'>WhatsApp Us</a><button>Add to Cart</button></body></html>",
    )
    signals = DigitalPresenceExtractor.extract_signals(p)
    assert signals["has_ecommerce"] is True
    assert signals["has_whatsapp"] is True


def test_schema_org_extractor():
    html = """
    <html>
    <script type="application/ld+json">
    {
        "@type": "JewelryStore",
        "name": "Kundan Jewellers",
        "telephone": "+914012345678",
        "founder": {"name": "Rajesh Kumar"}
    }
    </script>
    </html>
    """
    p = FetchedPage(job_id="j1", target_id="t1", url="https://kundan.com", status_code=200, html_content=html)
    facts = SchemaOrgExtractor.extract_structured_data(p)
    assert facts["name"] == "Kundan Jewellers"
    assert facts["telephone"] == "+914012345678"
    assert "Rajesh Kumar" in facts["founders"]


def test_bde_brief_generator():
    comp = Company(
        job_id="j1",
        name="Royal Jewellers",
        normalized_name="royal jewellers",
        domain="royal.com",
        website="https://royal.com",
        source_url="https://royal.com",
        industry="Jewellery",
        city="Hyderabad",
        phones=[Phone(company_id="", phone="+914023456789", normalized_phone="+914023456789", raw_phone="+914023456789", source_url="def")],
        emails=[Email(company_id="", email="contact@royal.com", normalized_email="contact@royal.com", raw_email="contact@royal.com", source_url="def")],
        contacts=[Contact(company_id="", job_id="j1", name="Suresh Gupta", title="Owner", decision_maker_tier="Tier 1", source_url="def")],
        social_profiles=[SocialProfile(company_id="", platform="instagram", url="https://instagram.com/royal", normalized_url="https://instagram.com/royal", handle="royal", source_url="def")],
    )

    brief = BDEBriefGenerator.generate_brief(comp)
    assert brief.company_name == "Royal Jewellers"
    assert brief.primary_phone == "+914023456789"
    assert brief.primary_email == "contact@royal.com"
    assert brief.primary_decision_maker == "Suresh Gupta"
    assert brief.decision_maker_tier == "Tier 1"
    assert "Royal Jewellers is a Jewellery prospect in Hyderabad." in brief.research_summary


def test_lead_scorer_v2():
    scorer = LeadScorer("jewellery")
    comp = Company(
        job_id="j1",
        name="Royal Jewellers",
        normalized_name="royal jewellers",
        domain="royal.com",
        website="https://royal.com",
        source_url="https://royal.com",
        industry="Jewellery",
        city="Hyderabad",
        phones=[Phone(company_id="", phone="+914023456789", normalized_phone="+914023456789", raw_phone="+914023456789", source_url="def")],
        emails=[Email(company_id="", email="contact@royal.com", normalized_email="contact@royal.com", raw_email="contact@royal.com", source_url="def")],
        contacts=[Contact(company_id="", job_id="j1", name="Suresh Gupta", title="Owner", decision_maker_tier="Tier 1", source_url="def")],
    )

    cand = scorer.score_lead(comp, target_location="Hyderabad")
    assert cand.score >= 70
    assert len(cand.score_reasons) >= 4
