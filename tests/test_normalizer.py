from growx_crawl.normalization.normalizer import Normalizer


def test_normalize_domain():
    assert Normalizer.normalize_domain("https://www.royaljewellers.com/about") == "royaljewellers.com"
    assert Normalizer.normalize_domain("http://krizzjewels.com:8080/contact?ref=123") == "krizzjewels.com"
    assert Normalizer.normalize_domain("amarsonsjewellers.in") == "amarsonsjewellers.in"


def test_normalize_email():
    assert Normalizer.normalize_email("  INFO@RoyalJewellers.com ") == "info@royaljewellers.com"
    assert Normalizer.normalize_email("invalid-email") is None


def test_normalize_phone():
    assert Normalizer.normalize_phone("+91-40-23456789") == "+914023456789"
    assert Normalizer.normalize_phone("09876543210") == "+919876543210"
    assert Normalizer.normalize_phone("9876543210") == "+919876543210"


def test_clean_company_name():
    assert Normalizer.clean_company_name("Royal Jewellers Pvt. Ltd.") == "Royal Jewellers"
    assert Normalizer.clean_company_name("Krizz Jewels Private Limited") == "Krizz Jewels"
    assert Normalizer.clean_company_name("Amarsons Jewellers Inc.") == "Amarsons Jewellers"
