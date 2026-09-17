import os
import pytest
from growx_crawl.identity import (
    IDENTITY_PREFIXES,
    build_domain_key,
    build_external_id_key,
    build_linkedin_key,
    build_person_email_key,
    build_registry_id_key,
    generate_identity_id,
    identity_service,
    normalize_company_name,
    normalize_domain,
    normalize_person_name,
    resolve_canonical_id_chain,
)
from growx_crawl.autogtm.models import CompanyAnalysis, ICPProfile
from growx_crawl.autogtm.prospector import prospect_harvester


def test_identity_id_generation():
    """Verify unique, lexically sortable ID generation across all Section 6 prefixes."""
    for prefix in IDENTITY_PREFIXES:
        gen_id = generate_identity_id(prefix)
        assert gen_id.startswith(prefix)
        assert len(gen_id) > len(prefix) + 12
        assert "_" in gen_id


def test_company_normalization():
    """Verify legal corporate suffixes are stripped while core business names remain intact."""
    test_cases = [
        ("GrowX Labs Pvt. Ltd.", "growx labs"),
        ("Acme Corporation, Inc.", "acme"),
        ("Stripe, LLC", "stripe"),
        ("Siemens AG & Co. KG", "siemens"),
        ("DeepMind Technologies Limited", "deepmind technologies"),
        ("Delivery Hero SE & Co. KGaA", "delivery hero"),
        ("BioNTech SE GMBH", "biontech"),
    ]
    for raw, expected in test_cases:
        norm = normalize_company_name(raw)
        assert norm == expected, f"Failed for {raw}: got {norm}, expected {expected}"


def test_person_normalization():
    """Verify honorifics are removed while maintaining initials and middle names."""
    test_cases = [
        ("Dr. Rahul K. Sharma", "rahul k. sharma"),
        ("Prof. John H. Watson", "john h. watson"),
        ("Mr. Marcus Vance", "marcus vance"),
        ("Elena Rostova", "elena rostova"),
        ("Ms. Sarah Chen", "sarah chen"),
    ]
    for raw, expected in test_cases:
        norm = normalize_person_name(raw)
        assert norm == expected, f"Failed for {raw}: got {norm}, expected {expected}"


def test_domain_normalization():
    """Verify URL and domain normalization with registrable domain separation."""
    test_cases = [
        ("https://www.GrowXLabs.com/about?ref=producthunt", ("growxlabs.com", "growxlabs.com")),
        ("http://uk.store.example.com/", ("uk.store.example.com", "example.com")),
        ("SUBDOMAIN.CO.UK", ("subdomain.co.uk", "subdomain.co.uk")),
        ("https://api.v2.stripe.com/docs", ("api.v2.stripe.com", "stripe.com")),
    ]
    for raw, (expected_host, expected_reg) in test_cases:
        host, reg = normalize_domain(raw)
        assert host == expected_host
        assert reg == expected_reg


def test_lookup_key_builders():
    """Verify deterministic lookup key generators."""
    assert build_domain_key("https://www.growxlabs.com/test") == "domain:growxlabs.com"
    assert build_external_id_key("CRUNCHBASE", "org/growx") == "external:crunchbase:org/growx"
    assert build_registry_id_key("DE", "HRB-123456") == "registry:de:HRB-123456"
    assert build_person_email_key("Rahul@GrowXLabs.com") == "email:rahul@growxlabs.com"
    assert build_linkedin_key("https://www.linkedin.com/in/marcus-vance-492") == "external:linkedin:marcus-vance-492"


def test_deterministic_company_and_domain_resolution():
    """Verify resolving or creating a company attaches domains and deduplicates."""
    import uuid
    dom_str = f"test-hex-{uuid.uuid4().hex[:6]}.io"
    comp1 = identity_service.get_or_create_company("Hexagon Data, Inc.", domain=f"https://{dom_str}")
    assert comp1.id.startswith("cmp_")
    assert comp1.normalized_name == "hexagon data"

    # Second call with alias and same domain should return same company
    comp2 = identity_service.get_or_create_company("Hexagon Data Tech LLC", domain=dom_str)
    assert comp2.id == comp1.id

    # Verify domain entity was created
    dom = identity_service.get_or_create_domain(dom_str)
    assert dom.id.startswith("dom_")
    assert dom.normalized_domain == dom_str


def test_person_resolution_with_keys_and_employment():
    """Verify person resolution attaches email and LinkedIn external identities and employment."""
    import uuid
    tag = uuid.uuid4().hex[:6]
    comp = identity_service.get_or_create_company(f"Synthex Systems {tag}", domain=f"synthex-{tag}.ai")
    
    person1, emp1 = identity_service.get_or_create_person(
        full_name="Elena Rostova",
        company_id=comp.id,
        title="CEO & Co-Founder",
        email=f"elena@{tag}.ai",
        linkedin_url=f"https://www.linkedin.com/in/elena-rostova-{tag}",
    )
    assert person1.id.startswith("per_")
    assert emp1 is not None
    assert emp1.company_id == comp.id
    assert emp1.is_current is True

    # Resolving with same email resolves to same canonical person
    person2, _ = identity_service.get_or_create_person(
        full_name="Dr. Elena Rostova",
        email=f"elena@{tag}.ai",
    )
    assert person2.id == person1.id


def test_merge_redirect_chain_and_cycle_protection():
    """Verify recursive merge resolution and loop protection."""
    import uuid
    # Test pure function resolver
    merge_map = {
        "cmp_1": "cmp_2",
        "cmp_2": "cmp_3",
        "cmp_cycle_a": "cmp_cycle_b",
        "cmp_cycle_b": "cmp_cycle_a",
    }

    def lookup_target(entity_id: str):
        return merge_map.get(entity_id)

    assert resolve_canonical_id_chain("cmp_1", lookup_target) == "cmp_3"
    assert resolve_canonical_id_chain("cmp_2", lookup_target) == "cmp_3"
    assert resolve_canonical_id_chain("cmp_3", lookup_target) == "cmp_3"

    # Cycles terminate safely without hanging
    res_cycle = resolve_canonical_id_chain("cmp_cycle_a", lookup_target)
    assert res_cycle in ["cmp_cycle_a", "cmp_cycle_b"]

    # Test via IdentityService with fresh unique entities
    tag = uuid.uuid4().hex[:6]
    comp_old = identity_service.get_or_create_company(f"Old Co {tag} Inc", domain=f"oldco-{tag}.example")
    comp_new = identity_service.get_or_create_company(f"New Co {tag} Inc", domain=f"newco-{tag}.example")

    merge = identity_service.merge_entities(
        entity_type="company",
        source_entity_id=comp_old.id,
        target_entity_id=comp_new.id,
        reason="Acquisition and domain rebranding",
    )
    assert merge.id.startswith("mrg_")
    assert identity_service.resolve_canonical_id(comp_old.id) == comp_new.id
    assert identity_service.resolve_canonical_id(comp_new.id) == comp_new.id


def test_ambiguous_name_match_queues_candidate():
    """Verify Section 13 rule: do NOT auto-merge matching names across distinct domains."""
    comp_a = identity_service.get_or_create_company("Summit Peak Partners", domain="summitpeak.us")
    
    # Another company with identical normalized name on a different domain
    comp_b = identity_service.get_or_create_company("Summit Peak Partners LLC", domain="summitpeak.co.uk")
    
    # Must NOT auto-merge
    assert comp_a.id != comp_b.id
    
    # Must have queued an identity candidate
    candidates = identity_service.identity_repo.list_candidates(status="pending")
    candidate_keys = [c.candidate_key for c in candidates]
    assert any("summit peak partners" in k for k in candidate_keys)


def test_locations_brands_relationships():
    """Verify adding locations, brands, and company relationships."""
    comp_parent = identity_service.get_or_create_company("Parent Global Holdings", domain="parentholdings.com")
    comp_sub = identity_service.get_or_create_company("Sub Tech Ltd", domain="subtech.io")

    # Location
    loc = identity_service.add_location(
        company_id=comp_parent.id,
        name="Global Headquarters",
        city="London",
        country_code="GB",
        is_primary=True,
    )
    assert loc.id.startswith("loc_")
    locs = identity_service.identity_repo.list_company_locations(comp_parent.id)
    assert len(locs) >= 1
    assert locs[0][1].city == "London"

    # Brand
    brand = identity_service.add_brand(comp_parent.id, "Apex Cloud Platform", domain="apexcloud.com")
    assert brand.id.startswith("brd_")
    brands = identity_service.identity_repo.list_company_brands(comp_parent.id)
    assert len(brands) >= 1

    # Relationship
    rel = identity_service.add_company_relationship(
        from_company_id=comp_parent.id,
        to_company_id=comp_sub.id,
        relationship_type="parent_of",
    )
    assert rel.id.startswith("rel_")
    rels = identity_service.identity_repo.list_relationships(comp_parent.id)
    assert len(rels) >= 1


@pytest.mark.asyncio
async def test_autogtm_prospector_canonical_identity_attachment():
    """Verify AutoGTM prospect harvest leads have canonical IDs attached."""
    analysis = CompanyAnalysis(
        domain="hexagondata.io",
        company_name="Hexagon Data",
        primary_offer="B2B Data Platform",
    )
    icp = ICPProfile(
        target_industries=["tech", "software"],
        company_size=["50-200"],
        target_roles=["VP of Revenue Growth", "CRO"],
        geographies=["United States"],
    )
    leads = await prospect_harvester.harvest_leads(analysis, icp, limit=2)
    assert len(leads) == 2
    for lead in leads:
        assert lead.canonical_company_id is not None
        assert lead.canonical_company_id.startswith("cmp_")
        assert lead.canonical_person_id is not None
        assert lead.canonical_person_id.startswith("per_")
        assert lead.canonical_domain_id is not None
        assert lead.canonical_domain_id.startswith("dom_")
