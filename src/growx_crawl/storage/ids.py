import secrets
import time
from typing import Optional

# Canonical prefixes per Section 8 specification
VALID_PREFIXES = {
    "cmp_": "company",
    "per_": "person",
    "dom_": "domain",
    "loc_": "location",
    "src_": "source",
    "job_": "job",
    "run_": "crawl/model/agent run",
    "prj_": "project",
    "emp_": "employment",
    "alias_": "company alias",
}


def generate_canonical_id(prefix: str) -> str:
    """
    Generates an application-side, globally unique, lexically sortable canonical ID.
    Format: {prefix}{timestamp_ms_hex}_{random_hex_12}
    
    Example:
        cmp_0191fa2b48c0_3d8f1e2a9b4c
        per_0191fa2b48c1_8f2a1b9e4c3d
        dom_0191fa2b48c2_1e4c3d8f2a1b
    """
    if not prefix.endswith("_"):
        prefix = f"{prefix}_"

    timestamp_ms = int(time.time() * 1000)
    time_hex = f"{timestamp_ms:012x}"
    random_hex = secrets.token_hex(6)
    return f"{prefix}{time_hex}_{random_hex}"


def extract_timestamp_from_id(canonical_id: str) -> Optional[int]:
    """
    Extracts the millisecond epoch timestamp encoded within a canonical ID.
    """
    try:
        parts = canonical_id.split("_")
        if len(parts) >= 3:
            time_hex = parts[1]
            return int(time_hex, 16)
        elif len(parts) == 2 and len(parts[1]) >= 12:
            time_hex = parts[1][:12]
            return int(time_hex, 16)
    except Exception:
        pass
    return None
