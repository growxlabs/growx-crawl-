import re
from typing import Any, Dict, Optional, Tuple
from growx_crawl.identity.ids import IDENTITY_PREFIXES
from growx_crawl.identity.normalization import normalize_domain


def normalize_integer(raw: Any) -> Optional[int]:
    if raw is None:
        return None
    if isinstance(raw, int):
        return raw
    s = str(raw).replace(",", "").strip()
    match = re.search(r"\b(\d+)\b", s)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


def normalize_employee_range(raw: Any) -> Optional[Dict[str, Any]]:
    """
    Parses employee count or range into structured dict:
    e.g. '50-200 employees' -> {'min': 50, 'max': 200, 'unit': 'count'}
         '250+'             -> {'min': 250, 'max': None, 'unit': 'count'}
         250                -> {'min': 250, 'max': 250, 'unit': 'count', 'value': 250}
    """
    if raw is None:
        return None
    if isinstance(raw, dict) and ("min" in raw or "max" in raw or "value" in raw):
        return {
            "min": raw.get("min") or raw.get("value"),
            "max": raw.get("max") or raw.get("value"),
            "unit": "count",
            "value": raw.get("value") or raw.get("min"),
        }

    s = str(raw).replace(",", "").strip().lower()

    # Range like '50-200' or '50 to 200'
    range_match = re.search(r"(\d+)\s*(?:-|to)\s*(\d+)", s)
    if range_match:
        min_v = int(range_match.group(1))
        max_v = int(range_match.group(2))
        return {"min": min_v, "max": max_v, "unit": "count"}

    # Plus format '250+'
    plus_match = re.search(r"(\d+)\s*\+", s)
    if plus_match:
        v = int(plus_match.group(1))
        return {"min": v, "max": None, "unit": "count"}

    # Single integer
    int_val = normalize_integer(s)
    if int_val is not None:
        return {"min": int_val, "max": int_val, "value": int_val, "unit": "count"}

    return None


def normalize_revenue_range(raw: Any) -> Optional[Dict[str, Any]]:
    """
    Parses structured currency amounts and ranges:
    e.g. '₹10-50 Cr' -> {'min': 100000000, 'max': 500000000, 'currency': 'INR', 'unit': 'currency'}
         '$5M - $10M' -> {'min': 5000000, 'max': 10000000, 'currency': 'USD', 'unit': 'currency'}
    """
    if raw is None:
        return None
    if isinstance(raw, dict) and ("min" in raw or "max" in raw or "value" in raw):
        return {
            "min": raw.get("min"),
            "max": raw.get("max"),
            "currency": raw.get("currency", "USD"),
            "unit": "currency",
            "value": raw.get("value"),
        }

    s = str(raw).strip()
    currency = "USD"
    if "₹" in s or "inr" in s.lower():
        currency = "INR"
    elif "€" in s or "eur" in s.lower():
        currency = "EUR"
    elif "£" in s or "gbp" in s.lower():
        currency = "GBP"

    # Multiplier detection
    def parse_amount(val_str: str) -> Optional[float]:
        val_str = val_str.replace(",", "").strip().lower()
        multiplier = 1.0
        if "cr" in val_str or "crore" in val_str:
            multiplier = 10_000_000.0
        elif "lakh" in val_str or "lac" in val_str:
            multiplier = 100_000.0
        elif "b" in val_str or "billion" in val_str:
            multiplier = 1_000_000_000.0
        elif "m" in val_str or "million" in val_str:
            multiplier = 1_000_000.0
        elif "k" in val_str or "thousand" in val_str:
            multiplier = 1_000.0

        match = re.search(r"(\d+(?:\.\d+)?)", val_str)
        if match:
            return float(match.group(1)) * multiplier
        return None

    range_match = re.search(r"([^\-]+?)\s*(?:-|to)\s*([^\-]+)", s)
    if range_match:
        part1 = range_match.group(1).strip()
        part2 = range_match.group(2).strip()

        multiplier = 1.0
        p2_lower = part2.lower()
        if "cr" in p2_lower or "crore" in p2_lower:
            multiplier = 10_000_000.0
        elif "lakh" in p2_lower or "lac" in p2_lower:
            multiplier = 100_000.0
        elif "b" in p2_lower or "billion" in p2_lower:
            multiplier = 1_000_000_000.0
        elif "m" in p2_lower or "million" in p2_lower:
            multiplier = 1_000_000.0
        elif "k" in p2_lower or "thousand" in p2_lower:
            multiplier = 1_000.0

        min_v = parse_amount(part1)
        max_v = parse_amount(part2)
        if min_v is not None and not any(w in part1.lower() for w in ["cr", "crore", "lakh", "lac", "b", "m", "k"]):
            min_v = min_v * multiplier

        if min_v is not None or max_v is not None:
            return {
                "min": min_v,
                "max": max_v,
                "currency": currency,
                "unit": "currency",
                "raw": s,
            }

    single_v = parse_amount(s)
    if single_v is not None:
        return {
            "value": single_v,
            "min": single_v,
            "max": single_v,
            "currency": currency,
            "unit": "currency",
            "raw": s,
        }

    return {"raw": s, "currency": currency, "unit": "currency"}


def normalize_entity_ref(raw: Any, expected_prefix: Optional[str] = None) -> Optional[str]:
    """
    Validates canonical entity reference format (e.g. cmp_..., loc_...).
    """
    if not raw or not isinstance(raw, str):
        return None
    ref = raw.strip()
    if expected_prefix:
        if not ref.startswith(expected_prefix):
            return None
    elif not any(ref.startswith(p) for p in IDENTITY_PREFIXES):
        return None
    return ref


def normalize_email(raw: Any) -> Optional[str]:
    if not raw or not isinstance(raw, str):
        return None
    clean = raw.strip().lower()
    if re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", clean):
        return clean
    return None


def normalize_phone(raw: Any) -> Optional[str]:
    if not raw or not isinstance(raw, str):
        return None
    # Strip spaces and standard formatting punctuation
    clean = re.sub(r"[^\d+]", "", raw.strip())
    if len(clean) >= 7:
        return raw.strip()
    return None


def normalize_url(raw: Any) -> Optional[str]:
    if not raw or not isinstance(raw, str):
        return None
    s = raw.strip()
    if not s.startswith("http://") and not s.startswith("https://"):
        s = "https://" + s
    host, _ = normalize_domain(s)
    return s if host else None


def normalize_fact_value(value_type: str, raw_value: Any) -> Tuple[bool, Any, Optional[str]]:
    """
    Validates and normalizes raw values into typed, structured representations.
    Returns: (is_valid, normalized_value_dict_or_scalar, error_reason)
    """
    if raw_value is None:
        return False, None, "null_value"

    vt = value_type.strip().lower()

    if vt == "string":
        val = str(raw_value).strip()
        if not val:
            return False, None, "empty_string"
        return True, {"value": val}, None

    elif vt == "integer":
        int_val = normalize_integer(raw_value)
        if int_val is None:
            return False, None, "invalid_integer"
        return True, {"value": int_val}, None

    elif vt == "json":
        if isinstance(raw_value, dict):
            return True, raw_value, None
        # Try employee range or general dict
        emp_range = normalize_employee_range(raw_value)
        if emp_range is not None:
            return True, emp_range, None
        rev_range = normalize_revenue_range(raw_value)
        if rev_range is not None:
            return True, rev_range, None
        return True, {"raw": str(raw_value)}, None

    elif vt == "entity_ref":
        ref = normalize_entity_ref(raw_value)
        if not ref:
            return False, None, "invalid_entity_ref"
        return True, {"entity_id": ref}, None

    elif vt == "email":
        em = normalize_email(raw_value)
        if not em:
            return False, None, "invalid_email"
        return True, {"email": em, "value": em}, None

    elif vt == "phone":
        ph = normalize_phone(raw_value)
        if not ph:
            return False, None, "invalid_phone"
        return True, {"phone": ph, "value": ph}, None

    elif vt == "url":
        u = normalize_url(raw_value)
        if not u:
            return False, None, "invalid_url"
        return True, {"url": u, "value": u}, None

    elif vt in ["decimal", "float"]:
        try:
            flt_val = float(str(raw_value).replace(",", "").strip())
            return True, {"value": flt_val}, None
        except ValueError:
            return False, None, "invalid_decimal"

    elif vt == "boolean":
        if isinstance(raw_value, bool):
            return True, {"value": raw_value}, None
        s = str(raw_value).strip().lower()
        if s in ["true", "1", "yes"]:
            return True, {"value": True}, None
        if s in ["false", "0", "no"]:
            return True, {"value": False}, None
        return False, None, "invalid_boolean"

    # Default fallback
    return True, {"value": raw_value if not isinstance(raw_value, (list, dict)) else raw_value}, None
