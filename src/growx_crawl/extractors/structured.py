from typing import Any, Dict, List, Optional
from growx_crawl.crawler.fetcher import fetcher_pipeline


class StructuredExtractor:
    """
    Capability 2: CSS / XPath Structured Data Extraction powered by Parsel & lxml.
    Supports Scrapy-style ::text, ::attr(name), XPath queries, and list extractions.
    """

    def extract_from_html(self, html: str, selectors: Dict[str, str]) -> Dict[str, Any]:
        """Extract structured fields from raw HTML string using CSS or XPath selectors."""
        extracted: Dict[str, Any] = {}
        try:
            from parsel import Selector
            sel = Selector(text=html)
            for field_name, selector_expr in selectors.items():
                s = selector_expr.strip()
                try:
                    if s.startswith("//") or s.startswith("./"):
                        matches = sel.xpath(s).getall()
                    else:
                        matches = sel.css(s).getall()
                    cleaned = [m.strip() for m in matches if m and m.strip()]
                    if not cleaned:
                        extracted[field_name] = None
                    elif len(cleaned) == 1:
                        extracted[field_name] = cleaned[0]
                    else:
                        extracted[field_name] = cleaned
                except Exception:
                    extracted[field_name] = None
        except ImportError:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            for field_name, s in selectors.items():
                try:
                    found = soup.select(s)
                    if not found:
                        extracted[field_name] = None
                    elif len(found) == 1:
                        extracted[field_name] = found[0].get_text(strip=True)
                    else:
                        extracted[field_name] = [el.get_text(strip=True) for el in found]
                except Exception:
                    extracted[field_name] = None
        return extracted

    async def extract(
        self,
        url: str,
        selectors: Dict[str, str],
        fetcher: str = "auto",
        timeout: int = 30,
    ) -> Dict[str, Any]:
        res = await fetcher_pipeline.fetch(url=url, mode=fetcher, timeout=timeout)
        extracted = self.extract_from_html(res.html, selectors)
        return {
            "status": "success",
            "url": url,
            "fetcher_used": res.fetcher_used,
            "extracted_fields": len([k for k, v in extracted.items() if v is not None]),
            "data": extracted,
            "latency_ms": res.latency_ms,
        }


structured_extractor = StructuredExtractor()
