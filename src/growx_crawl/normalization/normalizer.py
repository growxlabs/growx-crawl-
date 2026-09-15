import re
import urllib.parse
from typing import Optional


class Normalizer:
    @classmethod
    def normalize_domain(cls, url_or_domain: str) -> str:
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

    @classmethod
    def normalize_url(cls, url: str) -> str:
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

    @classmethod
    def normalize_email(cls, email: str) -> Optional[str]:
        if not email:
            return None
        clean = email.strip().lower()
        if "@" in clean and len(clean) >= 5:
            return clean
        return None

    @classmethod
    def normalize_phone(cls, phone: str) -> Optional[str]:
        if not phone:
            return None
        # Keep leading +, strip all other non-digits
        digits = re.sub(r"[^\d+]", "", phone.strip())
        if digits.startswith("00"):
            digits = "+" + digits[2:]
        elif digits.startswith("0") and len(digits) == 11:
            digits = "+91" + digits[1:]  # Default Indian mobile prefix if 098...
        elif len(digits) == 10 and not digits.startswith("+"):
            digits = "+91" + digits  # Default India country code for 10-digit mobile
        return digits if len(digits) >= 7 else None

    @classmethod
    def extract_country_code(cls, phone: str) -> Optional[str]:
        norm = cls.normalize_phone(phone)
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

    @classmethod
    def clean_company_name(cls, name: str) -> str:
        if not name:
            return ""
        clean = name.strip()
        # Remove common business entity suffixes for cleaner presentation
        clean = re.sub(
            r"\b(Pvt\.?\s*Ltd\.?|Private\s+Limited|Ltd\.?|Inc\.?|LLP|Corporation|Corp\.?)\b",
            "",
            clean,
            flags=re.I,
        ).strip()
        # Strip excessive punctuation
        clean = re.sub(r"\s+", " ", clean).strip(" -,.|")
        return clean or name.strip()

    @classmethod
    def normalize_company_name_key(cls, name: str) -> str:
        cleaned = cls.clean_company_name(name).lower()
        return re.sub(r"[^a-z0-9]", "", cleaned)
