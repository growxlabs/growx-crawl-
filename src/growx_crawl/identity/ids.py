import secrets
import time
from typing import Optional

IDENTITY_PREFIXES = {
    "cmp_": "company",
    "per_": "person",
    "dom_": "domain",
    "loc_": "location",
    "brd_": "brand",
    "src_": "source",
    "rel_": "relationship",
    "ext_": "external identity",
    "cand_": "identity candidate",
    "evt_": "identity event",
    "mrg_": "entity merge",
}


def generate_identity_id(prefix: str) -> str:
    """
    Generates an application-side, globally unique, lexically sortable ID for identity entities.
    Format: {prefix}{timestamp_ms_hex}_{random_hex_12}
    """
    if not prefix.endswith("_"):
        prefix = f"{prefix}_"

    timestamp_ms = int(time.time() * 1000)
    time_hex = f"{timestamp_ms:012x}"
    random_hex = secrets.token_hex(6)
    return f"{prefix}{time_hex}_{random_hex}"
