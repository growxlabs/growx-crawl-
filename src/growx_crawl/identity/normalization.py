import re
import unicodedata
from typing import Tuple
from urllib.parse import urlparse

LEGAL_SUFFIXES = [
    r"private\s+limited",
    r"pvt\s+ltd",
    r"limited",
    r"ltd",
    r"incorporated",
    r"inc",
    r"corporation",
    r"corp",
    r"llc",
    r"llp",
    r"gmbh",
    r"plc",
    r"s\s*a",
    r"s\s*r\s*l",
    r"(?:&\s*)?co\s*kg",
    r"(?:&\s*)?co\s*kgaa",
    r"kgaa",
    r"ag",
    r"se",
]

HONORIFICS = [
    r"^(mr|mrs|ms|dr|prof)\.?\s+",
]


def clean_unicode(text: str) -> str:
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalized if not unicodedata.combining(c))


def normalize_company_name(name: str) -> str:
    """
    Normalizes company names by lowercasing, stripping punctuation,
    and removing corporate legal suffixes per Section 10 specification.
    
    Example:
        'GrowX Labs Pvt. Ltd.' -> 'growx labs'
        'Acme Corporation, Inc.' -> 'acme'
    """
    if not name:
        return ""

    text = clean_unicode(name).lower().strip()
    text = re.sub(r"[\.,\-_/]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    changed = True
    while changed:
        changed = False
        for pattern in LEGAL_SUFFIXES:
            new_text = re.sub(rf"\b{pattern}\s*$", "", text, flags=re.IGNORECASE).strip()
            new_text = re.sub(r"(?:\s+&\s*|\s+and\s*)$", "", new_text).strip()
            if new_text and new_text != text:
                text = new_text
                changed = True

    return text or name.lower().strip()


def normalize_person_name(name: str) -> str:
    """
    Normalizes person names by trimming, lowercasing, and stripping honorifics
    while preserving initials and middle names per Section 11 specification.
    
    Example:
        'Dr. Rahul K. Sharma' -> 'rahul k. sharma'
    """
    if not name:
        return ""

    text = clean_unicode(name).lower().strip()
    for h in HONORIFICS:
        text = re.sub(h, "", text, flags=re.IGNORECASE).strip()

    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_domain(url_or_domain: str) -> Tuple[str, str]:
    """
    Normalizes URLs or domain strings into canonical hostname and registrable domain
    per Section 12 specification.
    
    Returns (normalized_domain, registrable_domain)
    
    Examples:
        'https://www.example.com/about?ref=1' -> ('example.com', 'example.com')
        'https://uk.store.example.com'        -> ('uk.store.example.com', 'example.com')
    """
    if not url_or_domain:
        return "", ""

    raw = url_or_domain.strip().lower()
    if not raw.startswith("http://") and not raw.startswith("https://"):
        raw = "https://" + raw

    parsed = urlparse(raw)
    hostname = (parsed.netloc or "").split(":")[0].strip()

    if hostname.startswith("www."):
        hostname = hostname[4:]

    parts = hostname.split(".")
    if len(parts) >= 2:
        # Basic registrable domain extraction (e.g. example.com or example.co.uk)
        if len(parts) >= 3 and parts[-2] in ["co", "com", "org", "gov", "ac", "net"] and len(parts[-1]) == 2:
            registrable = ".".join(parts[-3:])
        else:
            registrable = ".".join(parts[-2:])
    else:
        registrable = hostname

    return hostname, registrable
