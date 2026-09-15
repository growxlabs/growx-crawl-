from growx_crawl.discovery import QueryExpander, URLClassifier


def test_query_expander():
    variants = QueryExpander.expand_query(
        query="jewellery stores Hyderabad",
        industry="jewellery",
        location="Hyderabad",
        max_variants=5,
    )
    assert len(variants) >= 3
    assert "jewellery stores Hyderabad" in variants
    assert any("gold jewellery" in v.lower() for v in variants)


def test_url_classifier():
    assert URLClassifier.classify("https://instagram.com/royaljewellers") == "social_profile"
    assert URLClassifier.classify("https://wikipedia.org/wiki/Jewellery") == "article"
    assert URLClassifier.classify("https://justdial.com/Hyderabad/jewellers") == "directory"
    assert URLClassifier.classify("https://royaljewellers.com") == "company_website"
