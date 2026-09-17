"""
GrowX Architecture Constitution Conformance Tests.
Validates service boundaries, module imports, backward compatibility adapters,
and core functionality of shared, normalization, entity_resolution, verification,
scoring, and ai subsystems.
"""

import pytest
from growx_crawl.shared.ids import generate_id, parse_id_timestamp_ms
from growx_crawl.shared.time import utc_now, utc_iso_now, parse_iso
from growx_crawl.shared.hashing import sha256_text, deterministic_json_hash
from growx_crawl.shared.pagination import PaginatedResponse

from growx_crawl.normalization.company import clean_company_name, normalize_company_name, normalize_company_name_key
from growx_crawl.normalization.person import clean_person_name, normalize_person_name, split_person_name
from growx_crawl.normalization.domain import normalize_domain, get_registrable_domain
from growx_crawl.normalization.phone import normalize_phone, extract_country_code
from growx_crawl.normalization.address import normalize_address
from growx_crawl.normalization.normalizer import Normalizer

from growx_crawl.identity.aliases import create_person_alias
from growx_crawl.identity.relationships import create_company_relationship

from growx_crawl.entity_resolution.scoring import jaro_winkler_similarity
from growx_crawl.entity_resolution.models import ResolutionDecision
from growx_crawl.entity_resolution.decisions import evaluate_decision
from growx_crawl.entity_resolution.candidate_generation import generate_company_blocking_keys, find_candidate_pairs
from growx_crawl.entity_resolution.company.matcher import CompanyMatcher
from growx_crawl.entity_resolution.person.matcher import PersonMatcher
from growx_crawl.entity_resolution.service import entity_resolution_service

from growx_crawl.intelligence.history.change_detector import detect_value_change
from growx_crawl.intelligence.signals.detectors import detect_signals_from_company

from growx_crawl.verification.email import EmailVerifier
from growx_crawl.verification.service import verification_service
from growx_crawl.verification.models import VerificationStatus
from growx_crawl.autogtm.verifier import EmailVerifier as LegacyEmailVerifier, email_verifier as legacy_email_verifier

from growx_crawl.scoring.data_confidence import calculate_data_confidence
from growx_crawl.scoring.icp_fit import calculate_icp_fit
from growx_crawl.scoring.buying_signal import calculate_buying_signal
from growx_crawl.scoring.service import scoring_service
from growx_crawl.core.enums import PriorityLevel

from growx_crawl.ai.models import AIRequest
from growx_crawl.ai.cost import calculate_ai_cost
from growx_crawl.ai.gateway import ai_gateway
from growx_crawl.ai.telemetry import ai_telemetry


def test_shared_primitives():
    # ID generation
    cid = generate_id("cmp_")
    assert cid.startswith("cmp_")
    ts = parse_id_timestamp_ms(cid)
    assert ts is not None and ts > 1700000000000

    # Time
    now = utc_now()
    assert now.tzinfo is not None
    iso = utc_iso_now()
    assert iso.endswith("Z")
    parsed = parse_iso(iso)
    assert parsed is not None

    # Hashing
    h = sha256_text("hello world")
    assert len(h) == 64
    jh = deterministic_json_hash({"b": 2, "a": 1})
    assert len(jh) == 64

    # Pagination
    resp = PaginatedResponse.create(items=[1, 2, 3], total=10, limit=3, offset=0)
    assert resp.has_more is True
    assert len(resp.items) == 3


def test_normalization_domain_split_and_facade():
    # Company
    raw_comp = "GrowX Labs Private Limited"
    clean = clean_company_name(raw_comp)
    assert clean == "GrowX Labs"
    norm_comp = normalize_company_name(raw_comp)
    assert norm_comp == "growx labs"
    key = normalize_company_name_key(raw_comp)
    assert key == "growxlabs"

    # Facade delegation
    assert Normalizer.clean_company_name(raw_comp) == clean
    assert Normalizer.normalize_company_name_key(raw_comp) == key

    # Person
    raw_per = "Dr. Rahul K. Sharma"
    assert clean_person_name(raw_per) == "Rahul K. Sharma"
    assert normalize_person_name(raw_per) == "rahul k. sharma"
    fn, ln = split_person_name(raw_per)
    assert fn == "Rahul" and ln == "K. Sharma"
    assert Normalizer.normalize_person_name(raw_per) == "rahul k. sharma"

    # Domain
    dom = "https://www.api.growxlabs.com/path"
    assert normalize_domain(dom) == "api.growxlabs.com"
    assert get_registrable_domain(dom) == "growxlabs.com"
    assert Normalizer.normalize_domain(dom) == "api.growxlabs.com"

    # Phone
    phone = "09876543210"
    assert normalize_phone(phone) == "+919876543210"
    assert extract_country_code(phone) == "+91"
    assert Normalizer.normalize_phone(phone) == "+919876543210"

    # Address
    addr = "  123 Tech Park, Whitefield,  Bangalore 560066  "
    assert "Bangalore 560066" in normalize_address(addr)


def test_identity_expansion():
    alias = create_person_alias("per_123", "Dr. Bob", alias_type="nickname")
    assert alias.id.startswith("alt_")
    assert alias.normalized_alias == "bob"

    rel = create_company_relationship("cmp_1", "cmp_2", "subsidiary")
    assert rel.id.startswith("rel_")
    assert rel.relationship_type == "subsidiary"


def test_entity_resolution_matcher_and_decisions():
    # Similarity
    sim = jaro_winkler_similarity("GrowX Labs", "GrowX Labs Inc")
    assert sim > 0.80

    # Decisions
    assert evaluate_decision(0.95) == ResolutionDecision.AUTO_MERGED
    assert evaluate_decision(0.75) == ResolutionDecision.REVIEW_REQUIRED
    assert evaluate_decision(0.30) == ResolutionDecision.NO_MATCH

    # Company matcher
    matcher = CompanyMatcher()
    c1 = {"name": "Acme Corp", "domain": "acme.com", "emails": ["info@acme.com"]}
    c2 = {"name": "Acme", "domain": "acme.com", "emails": ["sales@acme.com"]}
    conf, expl = matcher.match(c1, c2)
    assert conf == 1.0
    assert "same_domain" in [s.name for s in expl.signals]

    # Blocking keys
    bks = generate_company_blocking_keys("cmp_1", "Acme Corporation", "acme.com")
    assert any(bk.key_type == "domain_root" for bk in bks)
    pairs = find_candidate_pairs(bks + generate_company_blocking_keys("cmp_2", "Acme Industries", "acme.com"))
    assert ("cmp_1", "cmp_2") in pairs or ("cmp_2", "cmp_1") in pairs

    # Person matcher
    p_matcher = PersonMatcher()
    p1 = {"name": "Alice Smith", "email": "alice@acme.com"}
    p2 = {"name": "Alice S.", "email": "alice@acme.com"}
    p_conf, p_expl = p_matcher.match(p1, p2)
    assert p_conf == 1.0


def test_intelligence_history_and_signals():
    # History change detection
    change = detect_value_change(100, 250, "company.employee_count")
    assert change is not None
    assert change["change_type"] == "headcount_growth"

    no_change = detect_value_change("Tech", "Tech", "company.industry")
    assert no_change is None

    # Signals
    signals = detect_signals_from_company("cmp_1", {
        "funding_stage": "Series A",
        "technologies_used": ["Python", "FastAPI", "Postgres", "Redis"],
    })
    assert len(signals) == 2
    types = [s.signal_type for s in signals]
    assert "funding_raised" in types
    assert "tech_stack_active" in types


@pytest.mark.asyncio
async def test_verification_boundary_and_adapters():
    # Email syntax check
    v = EmailVerifier()
    assert v.is_syntax_valid("contact@growxlabs.com") is True
    assert v.is_syntax_valid("invalid_email") is False

    # Adapter backward compatibility
    assert LegacyEmailVerifier is EmailVerifier
    assert legacy_email_verifier.is_syntax_valid("test@example.com") is True

    # Verification service
    dom_res = await verification_service.verify_domain("google.com")
    assert dom_res.status == VerificationStatus.VERIFIED

    comp_res = await verification_service.verify_company("cmp_1", {"name": "Test Co", "domain": "test.com"})
    assert comp_res.status == VerificationStatus.VERIFIED

    emp_res = await verification_service.verify_employment("per_1", "cmp_1", "alex@growxlabs.com", "growxlabs.com")
    assert emp_res.status == VerificationStatus.VERIFIED
    assert emp_res.confidence >= 0.90


def test_scoring_dimensional_separation():
    comp_data = {
        "domain": "growxlabs.com",
        "emails": ["founders@growxlabs.com"],
        "phones": ["+1234567890"],
        "address": "San Francisco, CA",
        "city": "San Francisco",
        "industry": "Software & Artificial Intelligence",
        "description": "B2B SaaS Growth Engine",
    }
    signals = [{"signal_type": "funding_raised"}]

    scores = scoring_service.score_company(
        company_data=comp_data,
        target_industry="Software",
        target_location="San Francisco",
        signals=signals,
    )

    # 4 distinct dimensions
    assert scores.data_confidence >= 80.0
    assert scores.icp_fit >= 80.0
    assert scores.buying_signal >= 40.0
    assert scores.priority in (PriorityLevel.HIGH, PriorityLevel.MEDIUM)
    assert len(scores.reasons) > 0


@pytest.mark.asyncio
async def test_ai_gateway_boundary():
    req = AIRequest(
        task="icp_synthesis",
        prompt="Analyze ideal customer profile for growxlabs",
        prompt_version="v1",
    )
    resp = await ai_gateway.complete(req)

    assert resp.run_id.startswith("ai_")
    assert resp.model == "gemini-2.0-flash"
    assert resp.provider == "gemini"
    assert resp.total_tokens > 0
    assert resp.cost_usd >= 0.0

    cost = calculate_ai_cost("gemini-2.0-flash", 1000, 500)
    assert cost > 0.0

    summary = ai_telemetry.get_summary()
    assert summary["total_runs"] >= 1
