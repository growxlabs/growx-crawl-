"""
GrowX Company Normalization.
Handles corporate legal suffix stripping, unicode normalization, and stable lookup keys.
"""

import re
import unicodedata

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


def clean_unicode(text: str) -> str:
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalized if not unicodedata.combining(c))


def clean_company_name(name: str) -> str:
    """
    Cleans company names for presentation by stripping common legal suffixes
    and excessive punctuation while preserving original casing.
    """
    if not name:
        return ""
    clean = name.strip()
    clean = re.sub(
        r"\b(Pvt\.?\s*Ltd\.?|Private\s+Limited|Ltd\.?|Inc\.?|LLP|Corporation|Corp\.?)\b",
        "",
        clean,
        flags=re.I,
    ).strip()
    clean = re.sub(r"\s+", " ", clean).strip(" -,.|")
    return clean or name.strip()


def normalize_company_name(name: str) -> str:
    """
    Normalizes company names for deduplication and matching:
    lowercased, legal suffixes stripped, whitespace collapsed.
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


def normalize_company_name_key(name: str) -> str:
    """
    Generates an alphanumeric-only canonical key from a company name.
    """
    cleaned = clean_company_name(name).lower()
    return re.sub(r"[^a-z0-9]", "", cleaned)
