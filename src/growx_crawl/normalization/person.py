"""
GrowX Person Normalization.
Handles honorific stripping, name splitting, and case folding.
"""

import re
import unicodedata
from typing import Tuple

HONORIFICS = [
    r"^(mr|mrs|ms|dr|prof)\.?\s+",
]


def clean_unicode(text: str) -> str:
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalized if not unicodedata.combining(c))


def clean_person_name(name: str) -> str:
    """Cleans a person name by stripping leading honorifics while preserving case."""
    if not name:
        return ""
    text = name.strip()
    for h in HONORIFICS:
        text = re.sub(h, "", text, flags=re.IGNORECASE).strip()
    return re.sub(r"\s+", " ", text).strip()


def normalize_person_name(name: str) -> str:
    """Normalizes a person name for matching: lowercased, stripped honorifics."""
    if not name:
        return ""
    text = clean_unicode(name).lower().strip()
    for h in HONORIFICS:
        text = re.sub(h, "", text, flags=re.IGNORECASE).strip()
    return re.sub(r"\s+", " ", text).strip()


def split_person_name(name: str) -> Tuple[str, str]:
    """
    Splits full name into (first_name, last_name).
    If only one name is provided, returns (name, "").
    """
    cleaned = clean_person_name(name)
    parts = cleaned.split()
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])
