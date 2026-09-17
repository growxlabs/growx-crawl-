"""
GrowX Signal Expiry Policies.
Configures signal freshness decay and expiry rules per signal type.
"""

from typing import Dict, Optional
from growx_crawl.shared.time import utc_iso_now, utc_now, format_iso, calculate_future_utc_iso
from datetime import timedelta


# Signal expiry configuration: signal_type -> days until expiry
SIGNAL_EXPIRY_DAYS: Dict[str, int] = {
    "leadership_change": 135,
    "hiring_growth": 60,
    "location_expansion": 270,
    "technology_adoption": 365,
    "technology_removal": 180,
    "product_launch": 180,
    "market_expansion": 270,
    "operational_expansion": 270,
    "funding_raised": 180,
    "tech_stack_active": 180,
}

# Default expiry for unknown signal types
DEFAULT_EXPIRY_DAYS = 180


def get_signal_expiry_date(signal_type: str, detected_at: Optional[str] = None) -> str:
    """Calculate the expiry date for a signal based on its type."""
    days = SIGNAL_EXPIRY_DAYS.get(signal_type, DEFAULT_EXPIRY_DAYS)
    if detected_at:
        from growx_crawl.shared.time import parse_iso
        dt = parse_iso(detected_at)
        if dt:
            expiry = dt + timedelta(days=days)
            return format_iso(expiry) or calculate_future_utc_iso(days=days)
    return calculate_future_utc_iso(days=days)
