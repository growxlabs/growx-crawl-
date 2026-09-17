"""
GrowX Platform Canonical ID Generator.
Provides globally unique, lexically sortable, prefixed identifier generation.
"""

import secrets
import time
from typing import Optional

CANONICAL_PREFIXES = {
    # Identity
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
    # Intelligence
    "obs_": "observation",
    "evd_": "evidence",
    "fct_": "fact",
    "val_": "fact value",
    "cnf_": "fact conflict",
    "sig_": "signal",
    "cpr_": "competitor relationship",
    "cpe_": "competitor evidence",
    "icp_": "ideal customer profile",
    "icpv_": "icp version",
    "snp_": "seller snapshot",
    "cr_": "icp criterion",
    "ex_": "icp exclusion",
    "prn_": "icp persona",
    "sc_": "icp company score",
    "psc_": "icp person score",
    # Ranking
    "prsp_": "prospect",
    "rkp_": "ranking profile",
    "prs_": "prospect score",
    "rkh_": "prospect score history",
    "rex_": "ranking explanation",
    # Verification
    "ver_": "verification result",

    # Platform / Execution
    "prj_": "project",
    "job_": "job",
    "wrk_": "worker",
    "cpg_": "campaign",
    "eml_": "mail message",
    "mtg_": "meeting",
    "opp_": "opportunity",
    "tx_": "billing transaction",
    "ai_": "ai model run",
}


def generate_id(prefix: str) -> str:
    """
    Generates an application-side, globally unique, lexically sortable ID.
    Format: {prefix}{timestamp_ms_hex}_{random_hex_12}
    """
    if not prefix.endswith("_"):
        prefix = f"{prefix}_"

    timestamp_ms = int(time.time() * 1000)
    time_hex = f"{timestamp_ms:012x}"
    random_hex = secrets.token_hex(6)
    return f"{prefix}{time_hex}_{random_hex}"


def generate_identity_id(prefix: str) -> str:
    """Backward-compatible alias for identity generation."""
    return generate_id(prefix)


def parse_id_timestamp_ms(canonical_id: str) -> Optional[int]:
    """Extracts the millisecond epoch timestamp from a canonical ID."""
    try:
        parts = canonical_id.split("_")
        if len(parts) >= 3:
            time_hex = parts[1]
            return int(time_hex, 16)
    except Exception:
        pass
    return None
