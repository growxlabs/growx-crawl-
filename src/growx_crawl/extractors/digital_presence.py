import re
from typing import Any, Dict, List
from bs4 import BeautifulSoup
from growx_crawl.models.page import FetchedPage


class DigitalPresenceExtractor:
    @classmethod
    def extract_signals(cls, page: FetchedPage) -> Dict[str, Any]:
        if not page.html_content:
            return {}

        html_lower = page.html_content.lower()
        url_lower = page.url.lower()
        soup = BeautifulSoup(page.html_content, "lxml")

        # 1. E-Commerce Detection
        has_ecommerce = any(
            kw in html_lower
            for kw in ["add to cart", "buy now", "checkout", "shopping-cart", "add_to_cart"]
        ) or any(path in url_lower for path in ["/shop", "/cart", "/checkout", "/product/"])

        # 2. Online Catalogue Detection
        has_catalogue = any(
            kw in html_lower for kw in ["catalogue", "view collection", "brochure", "lookbook"]
        ) or any(path in url_lower for path in ["/catalogue", "/collection", "/lookbook"])

        # 3. WhatsApp Detection
        has_whatsapp = "wa.me" in html_lower or "api.whatsapp.com" in html_lower or "whatsapp" in html_lower

        # 4. Contact Form Detection
        forms = soup.find_all("form")
        has_contact_form = any(
            "contact" in form.get("id", "").lower()
            or "contact" in form.get("class", "").lower()
            or "contact" in form.get("action", "").lower()
            or "email" in form.get_text().lower()
            for form in forms
        ) or bool(forms)

        # 5. Technology Fingerprinting
        techs: List[str] = []
        if "shopify" in html_lower:
            techs.append("Shopify")
        if "woocommerce" in html_lower or "wp-content" in html_lower:
            techs.append("WooCommerce/WordPress")
        if "wix.com" in html_lower:
            techs.append("Wix")
        if "squarespace" in html_lower:
            techs.append("Squarespace")

        return {
            "has_ecommerce": has_ecommerce,
            "has_catalogue": has_catalogue,
            "has_whatsapp": has_whatsapp,
            "has_contact_form": has_contact_form,
            "detected_technologies": list(set(techs)),
        }
