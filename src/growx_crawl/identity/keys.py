import re
from typing import Optional
from growx_crawl.identity.normalization import normalize_domain


def build_domain_key(url_or_domain: str) -> str:
    """
    Builds a stable lookup key for a domain: domain:{normalized_domain}
    """
    normalized, _ = normalize_domain(url_or_domain)
    return f"domain:{normalized}" if normalized else ""


def build_external_id_key(provider: str, external_id: str) -> str:
    """
    Builds a stable lookup key for an external identifier: external:{provider}:{external_id}
    """
    prov = (provider or "").strip().lower()
    ext_id = (external_id or "").strip()
    return f"external:{prov}:{ext_id}" if prov and ext_id else ""


def build_registry_id_key(jurisdiction: str, registry_id: str) -> str:
    """
    Builds a stable lookup key for a corporate registry identifier: registry:{jurisdiction}:{registry_id}
    """
    jur = (jurisdiction or "").strip().lower()
    reg = (registry_id or "").strip()
    return f"registry:{jur}:{reg}" if jur and reg else ""


def build_person_email_key(email: str) -> str:
    """
    Builds a stable lookup key for a person by email: email:{email}
    """
    em = (email or "").strip().lower()
    return f"email:{em}" if em else ""


def build_linkedin_key(url_or_handle: str) -> str:
    """
    Extracts LinkedIn handle/slug and builds a stable key: external:linkedin:{slug}
    """
    if not url_or_handle:
        return ""
    val = url_or_handle.strip().lower()
    match = re.search(r"linkedin\.com/(?:in|company)/([a-zA-Z0-9_\-]+)", val)
    if match:
        handle = match.group(1)
    else:
        handle = val.split("/")[-1].split("?")[0]
    return f"external:linkedin:{handle}" if handle else ""
