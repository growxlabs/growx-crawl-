"""
GrowX Domain Verification.
Answers: 'Is this domain active and usable as current evidence?'
Performs DNS resolution, HTTP/HTTPS reachability, TLS inspection, redirect tracking,
and parking page detection.
"""

import asyncio
import socket
import time
from typing import Any, Dict, List, Optional, Tuple
import httpx
from growx_crawl.normalization.domain import normalize_domain
from growx_crawl.shared.ids import generate_id
from growx_crawl.shared.time import utc_iso_now
from growx_crawl.verification.confidence import compute_verification_confidence
from growx_crawl.verification.freshness import calculate_valid_until
from growx_crawl.verification.models import (
    DomainState,
    ReasonCode,
    VerificationCheckEntity,
    VerificationResultEntity,
    VerificationStatus,
)
from growx_crawl.verification.policies import get_policy

PARKING_INDICATORS = [
    "domain is for sale",
    "buy this domain",
    "domain has expired",
    "parked by godaddy",
    "sedo domain parking",
    "hugedomains.com",
    "parkingcrew.net",
    "namecheap parking",
    "dan.com",
]


class DomainVerifier:
    """Verifies domain reachability, web hosting, and parking states."""

    def __init__(self, timeout: float = 4.0):
        self.timeout = timeout
        self._cache: Dict[str, Tuple[float, VerificationResultEntity]] = {}

    async def verify(self, domain_str: str, policy_name: str = "domain_default_v1") -> VerificationResultEntity:
        clean = normalize_domain(domain_str)
        if not clean:
            return VerificationResultEntity(
                id=generate_id("ver_"),
                subject_type="domain",
                subject_id=domain_str,
                verification_type="domain",
                status=VerificationStatus.INVALID,
                confidence=0.0,
                policy_name=policy_name,
                reason_codes=["DOMAIN_INVALID_FORMAT"],
                details_json={"error": "Empty or malformed domain string"},
            )

        # Check in-memory cache (TTL 1 hour)
        cached = self._cache.get(clean)
        if cached and (time.time() - cached[0]) < 3600:
            return cached[1]

        policy = get_policy(policy_name)
        checks: List[VerificationCheckEntity] = []
        reason_codes: List[str] = []

        dns_ok = False
        https_ok = False
        http_ok = False
        tls_ok = False
        parking_detected = False
        content_present = False
        redirect_target = None
        http_status = None

        # 1. DNS Check
        loop = asyncio.get_running_loop()
        dns_start = time.time()
        try:
            await loop.getaddrinfo(clean, 80)
            dns_ok = True
            checks.append(VerificationCheckEntity(
                id=generate_id("chk_"),
                verification_run_id="",
                check_type="dns_check",
                status="passed",
                score=1.0,
                reason_code=ReasonCode.DNS_LOOKUP_SUCCESS,
                duration_ms=int((time.time() - dns_start) * 1000),
            ))
            reason_codes.append(ReasonCode.DNS_LOOKUP_SUCCESS)
        except Exception as e:
            checks.append(VerificationCheckEntity(
                id=generate_id("chk_"),
                verification_run_id="",
                check_type="dns_check",
                status="failed",
                score=0.0,
                reason_code=ReasonCode.DOMAIN_UNREACHABLE,
                duration_ms=int((time.time() - dns_start) * 1000),
                metadata_json={"error": str(e)},
            ))
            reason_codes.append(ReasonCode.DOMAIN_UNREACHABLE)

        # 2. HTTP/HTTPS Probe (if DNS ok)
        if dns_ok:
            http_start = time.time()
            for proto in ("https", "http"):
                url = f"{proto}://{clean}"
                try:
                    async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                        resp = await client.get(url)
                        http_status = resp.status_code
                        if proto == "https":
                            https_ok = True
                            tls_ok = True
                        else:
                            http_ok = True

                        if str(resp.url) != url:
                            redirect_target = str(resp.url)

                        body = resp.text.lower()
                        if len(body) > 100:
                            content_present = True

                        for indicator in PARKING_INDICATORS:
                            if indicator in body:
                                parking_detected = True
                                break
                        break
                except Exception:
                    pass

            probe_duration = int((time.time() - http_start) * 1000)
            if https_ok or http_ok:
                checks.append(VerificationCheckEntity(
                    id=generate_id("chk_"),
                    verification_run_id="",
                    check_type="http_check",
                    status="passed",
                    score=1.0 if https_ok else 0.85,
                    reason_code=ReasonCode.HTTP_REACHABLE,
                    duration_ms=probe_duration,
                    metadata_json={"status_code": http_status, "tls_ok": tls_ok},
                ))
                reason_codes.append(ReasonCode.HTTP_REACHABLE)
            else:
                checks.append(VerificationCheckEntity(
                    id=generate_id("chk_"),
                    verification_run_id="",
                    check_type="http_check",
                    status="warning",
                    score=0.3,
                    reason_code="HTTP_PROBE_FAILED",
                    duration_ms=probe_duration,
                ))

            if parking_detected:
                checks.append(VerificationCheckEntity(
                    id=generate_id("chk_"),
                    verification_run_id="",
                    check_type="parking_detection",
                    status="warning",
                    score=0.2,
                    reason_code=ReasonCode.PARKING_PAGE_DETECTED,
                    duration_ms=0,
                ))
                reason_codes.append(ReasonCode.PARKING_PAGE_DETECTED)

        # Evaluate final status & confidence
        if not dns_ok:
            domain_state = DomainState.UNREACHABLE
            v_status = VerificationStatus.UNREACHABLE
            conf = 0.1
        elif parking_detected:
            domain_state = DomainState.PARKED
            v_status = VerificationStatus.UNCERTAIN
            conf = 0.35
        elif redirect_target and clean not in redirect_target:
            domain_state = DomainState.REDIRECTING
            v_status = VerificationStatus.SUPPORTED
            conf = 0.80
        elif https_ok and content_present:
            domain_state = DomainState.ACTIVE
            v_status = VerificationStatus.VERIFIED
            conf = 0.95
        elif http_ok or dns_ok:
            domain_state = DomainState.ACTIVE
            v_status = VerificationStatus.SUPPORTED
            conf = 0.80
        else:
            domain_state = DomainState.INACTIVE
            v_status = VerificationStatus.UNVERIFIED
            conf = 0.40

        technical_score = 1.0 if (dns_ok and (https_ok or http_ok) and not parking_detected) else (0.5 if dns_ok else 0.0)
        final_conf = compute_verification_confidence(
            subject_type="domain",
            base_source_score=0.90,
            identity_strength=0.90,
            source_agreement=0.90,
            technical_checks_score=technical_score,
            freshness_score=1.0,
            conflict_penalty=0.5 if parking_detected else 0.0,
        )

        valid_until = calculate_valid_until(None, policy.ttl_hours).strftime("%Y-%m-%dT%H:%M:%SZ")

        result = VerificationResultEntity(
            id=generate_id("ver_"),
            subject_type="domain",
            subject_id=clean,
            verification_type="domain",
            status=v_status,
            confidence=final_conf,
            policy_name=policy.name,
            policy_version=policy.version,
            reason_codes=reason_codes,
            checks=checks,
            verified_at=utc_iso_now(),
            valid_until=valid_until,
            details_json={
                "domain": clean,
                "domain_state": domain_state.value,
                "dns_ok": dns_ok,
                "http_ok": http_ok,
                "https_ok": https_ok,
                "tls_ok": tls_ok,
                "parking_detected": parking_detected,
                "content_present": content_present,
                "redirect_target": redirect_target,
                "http_status": http_status,
            },
        )

        self._cache[clean] = (time.time(), result)
        return result


domain_verifier = DomainVerifier()


async def verify_domain(domain_str: str, policy_name: str = "domain_default_v1") -> VerificationResultEntity:
    """Convenience helper delegating to domain_verifier."""
    return await domain_verifier.verify(domain_str, policy_name)
