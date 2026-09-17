"""
GrowX Address Normalization.
Handles street and location string cleaning and component parsing.
"""

import re
from typing import Dict, Optional


def normalize_address(address: str) -> str:
    """Normalizes address string by collapsing whitespace, stripping trailing separators."""
    if not address:
        return ""
    clean = re.sub(r"[\r\n\t]+", " ", address.strip())
    clean = re.sub(r"\s+", " ", clean)
    clean = re.sub(r"\s*,\s*", ", ", clean)
    return clean.strip(" ,.-")


def parse_address_components(address: str) -> Dict[str, Optional[str]]:
    """
    Heuristically extracts postal code, city, and street from address text.
    """
    clean = normalize_address(address)
    postal_code = None

    # Common 6-digit postal code (India) or 5-digit zip (US)
    pincode_match = re.search(r"\b(\d{6})\b", clean)
    if pincode_match:
        postal_code = pincode_match.group(1)
    else:
        zip_match = re.search(r"\b(\d{5}(?:-\d{4})?)\b", clean)
        if zip_match:
            postal_code = zip_match.group(1)

    parts = [p.strip() for p in clean.split(",") if p.strip()]
    city = parts[-2] if len(parts) >= 2 else (parts[0] if parts else None)

    return {
        "raw": address,
        "normalized": clean,
        "postal_code": postal_code,
        "city": city,
    }
