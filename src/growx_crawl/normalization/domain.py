"""
GrowX Domain & URL Normalization.
Handles hostname extraction, protocol normalization, and registrable domain determination.
"""

import urllib.parse
from typing import Tuple

KNOWN_MULTI_PART_TLDS = {
    "co.uk", "org.uk", "gov.uk", "ac.uk",
    "co.in", "net.in", "org.in", "gen.in", "firm.in", "ind.in",
    "com.au", "net.au", "org.au", "edu.au",
    "co.jp", "ne.jp", "ac.jp",
    "co.za", "org.za",
    "com.br", "net.br", "org.br",
    "com.sg", "edu.sg",
}


def normalize_domain(url_or_domain: str) -> str:
    """
    Normalizes a domain or URL to its clean lowercase hostname without port or leading 'www.'.
    """
    if not url_or_domain:
        return ""
    val = url_or_domain.strip().lower()
    if not val.startswith(("http://", "https://")):
        val = f"http://{val}"
    try:
        parsed = urllib.parse.urlparse(val)
        netloc = parsed.netloc or parsed.path
        netloc = netloc.split(":")[0]  # strip port
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc.strip().lower()
    except Exception:
        return val.strip().lower()


def normalize_url(url: str) -> str:
    """
    Normalizes an HTTP/HTTPS URL into a canonical string format:
    lowercase scheme and netloc, stripped www., trailing slash removed.
    """
    if not url:
        return ""
    val = url.strip()
    if not val.startswith(("http://", "https://")):
        val = f"https://{val}"
    try:
        parsed = urllib.parse.urlparse(val)
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        path = parsed.path.rstrip("/")
        return urllib.parse.urlunparse((parsed.scheme.lower(), netloc, path, "", "", ""))
    except Exception:
        return val


def get_registrable_domain(domain_or_host: str) -> str:
    """
    Extracts the registrable domain (e.g. 'growxlabs.com' from 'api.growxlabs.com').
    """
    clean = normalize_domain(domain_or_host)
    if not clean:
        return ""

    parts = clean.split(".")
    if len(parts) <= 2:
        return clean

    # Check multi-part TLD (e.g. example.co.uk)
    last_two = ".".join(parts[-2:])
    if last_two in KNOWN_MULTI_PART_TLDS and len(parts) >= 3:
        return ".".join(parts[-3:])

    return ".".join(parts[-2:])


def normalize_domain_tuple(url_or_domain: str) -> Tuple[str, str]:
    """Returns (normalized_domain, registrable_domain)."""
    norm = normalize_domain(url_or_domain)
    reg = get_registrable_domain(norm)
    return norm, reg
