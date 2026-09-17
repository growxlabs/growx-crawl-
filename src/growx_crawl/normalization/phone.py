"""
GrowX Phone Normalization.
Handles phone number cleaning, standard country code inference, and E.164 standardization.
"""

import re
from typing import Optional


def normalize_phone(phone: str) -> Optional[str]:
    """
    Normalizes phone numbers, retaining leading '+' and stripping non-digits.
    Defaults standard 10-digit mobile numbers to '+91' (India) if country code is omitted.
    """
    if not phone:
        return None
    # Keep leading +, strip all other non-digits
    digits = re.sub(r"[^\d+]", "", phone.strip())
    if digits.startswith("00"):
        digits = "+" + digits[2:]
    elif digits.startswith("0") and len(digits) == 11:
        digits = "+91" + digits[1:]  # Standard Indian mobile prefix if 098...
    elif len(digits) == 10 and not digits.startswith("+"):
        digits = "+91" + digits  # Standard India country code for 10-digit mobile
    return digits if len(digits) >= 7 else None


def extract_country_code(phone: str) -> Optional[str]:
    """Extracts dialing country code from a phone string."""
    norm = normalize_phone(phone)
    if norm and norm.startswith("+"):
        if norm.startswith("+91"):
            return "+91"
        if norm.startswith("+1"):
            return "+1"
        if norm.startswith("+44"):
            return "+44"
        match = re.match(r"^(\+\d{1,3})", norm)
        if match:
            return match.group(1)
    return "+91"
