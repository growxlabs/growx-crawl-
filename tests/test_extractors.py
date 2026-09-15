from pathlib import Path
from growx_crawl.extractors import (
    AddressExtractor,
    CompanyExtractor,
    ContactExtractor,
    EmailExtractor,
    PhoneExtractor,
    SocialExtractor,
)
from growx_crawl.models import FetchedPage

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_homepage_extraction():
    html_file = FIXTURE_DIR / "sample_homepage.html"
    html_content = html_file.read_text(encoding="utf-8")

    page = FetchedPage(
        job_id="test_job",
        target_id="test_target",
        url="https://royaljewellers.com",
        title="Royal Jewellers | Gold & Diamond Jewellery Hyderabad",
        html_content=html_content,
        text_content="Royal Jewellers in Hyderabad info@royaljewellers.com +91-40-23456789",
    )

    # 1. Company Extractor
    comp_ext = CompanyExtractor()
    comp_data = comp_ext.extract(page)
    assert comp_data["name"] in ["Royal Jewellers Hyderabad", "Royal Jewellers"]
    assert comp_data["industry"] == "Jewellery"

    # 2. Email Extractor
    email_ext = EmailExtractor()
    emails = email_ext.extract(page)
    norm_emails = {e.normalized_email for e in emails}
    assert "info@royaljewellers.com" in norm_emails
    assert "sales@royaljewellers.com" in norm_emails

    # 3. Phone Extractor
    phone_ext = PhoneExtractor()
    phones = phone_ext.extract(page)
    norm_phones = {p.normalized_phone for p in phones}
    assert "+914023456789" in norm_phones or "+919876543210" in norm_phones

    # 4. Social Extractor
    soc_ext = SocialExtractor()
    socials = soc_ext.extract(page)
    platforms = {s.platform for s in socials}
    assert "instagram" in platforms
    assert "linkedin" in platforms

    # 5. Address Extractor
    addr_ext = AddressExtractor()
    addr_data = addr_ext.extract(page)
    assert addr_data["city"] == "Hyderabad"
    assert addr_data["state"] == "Telangana"
    assert addr_data["country"] == "India"


def test_contact_page_extraction():
    html_file = FIXTURE_DIR / "sample_contact.html"
    html_content = html_file.read_text(encoding="utf-8")

    page = FetchedPage(
        job_id="test_job",
        target_id="test_target",
        url="https://royaljewellers.com/contact",
        html_content=html_content,
    )

    cnt_ext = ContactExtractor()
    contacts = cnt_ext.extract(page)
    roles = {c.title for c in contacts}
    assert "Managing Director" in roles or "Store Manager" in roles
