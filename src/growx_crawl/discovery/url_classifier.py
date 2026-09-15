import urllib.parse
from growx_crawl.normalization.normalizer import Normalizer


class URLClassifier:
    SOCIAL_DOMAINS = {
        "instagram.com", "facebook.com", "linkedin.com", "youtube.com",
        "twitter.com", "x.com", "whatsapp.com", "pinterest.com"
    }

    DIRECTORY_DOMAINS = {
        "yellowpages.com", "justdial.com", "indiamart.com", "tradeindia.com",
        "sulekha.com", "yelp.com", "tripadvisor.com", "glassdoor.com",
        "crunchbase.com", "kompass.com"
    }

    MARKETPLACE_DOMAINS = {
        "amazon.com", "amazon.in", "flipkart.com", "ebay.com",
        "etsy.com", "myntra.com", "ajio.com"
    }

    ARTICLE_DOMAINS = {
        "wikipedia.org", "medium.com", "news.google.com", "timesofindia.com",
        "thehindu.com", "economic-times.com", "quora.com", "reddit.com"
    }

    @classmethod
    def classify(cls, url: str) -> str:
        if not url:
            return "unknown"
        domain = Normalizer.normalize_domain(url)
        if not domain:
            return "unknown"

        if any(sd in domain for sd in cls.SOCIAL_DOMAINS):
            return "social_profile"

        if any(dd in domain for dd in cls.DIRECTORY_DOMAINS):
            return "directory"

        if any(md in domain for md in cls.MARKETPLACE_DOMAINS):
            return "marketplace"

        if any(ad in domain for ad in cls.ARTICLE_DOMAINS):
            return "article"

        # Path heuristics
        parsed = urllib.parse.urlparse(url)
        path = parsed.path.lower()
        if any(kw in path for kw in ["/news/", "/blog/", "/article/", "/wiki/"]):
            return "article"

        return "company_website"
