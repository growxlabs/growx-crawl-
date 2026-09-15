import urllib.parse
from bs4 import BeautifulSoup
from growx_crawl.models.page import FetchedPage


class PageClassifier:
    @classmethod
    def classify(cls, page: FetchedPage) -> str:
        if not page.url:
            return "other"

        parsed = urllib.parse.urlparse(page.url)
        path = parsed.path.lower().rstrip("/")
        title = (page.title or "").lower()

        if not path or path in ["", "/index.html", "/index.php"]:
            return "homepage"

        if any(kw in path for kw in ["/about", "/company", "/story", "/who-we-are"]):
            return "about"

        if any(kw in path for kw in ["/contact", "/reach-us", "/location", "/get-in-touch"]):
            return "contact"

        if any(kw in path for kw in ["/team", "/leadership", "/management", "/founders", "/our-team", "/board"]):
            return "leadership"

        if any(kw in path for kw in ["/product", "/shop", "/catalog", "/collection", "/category", "/item"]):
            return "product"

        if any(kw in path for kw in ["/service", "/solution", "/what-we-do"]):
            return "service"

        if any(kw in path for kw in ["/store", "/branches", "/outlets", "/find-us"]):
            return "location"

        if any(kw in path for kw in ["/privacy", "/terms", "/legal", "/disclaimer"]):
            return "legal"

        if any(kw in path for kw in ["/blog", "/news", "/press", "/articles"]):
            return "blog"

        # Title fallback
        if "about" in title:
            return "about"
        if "contact" in title:
            return "contact"
        if any(w in title for w in ["team", "leadership", "management"]):
            return "leadership"

        return "other"
