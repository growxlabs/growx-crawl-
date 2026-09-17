"""
GrowX AutoGTM Initial Seed Data.
Seeds canonical seller profile, competitor graph, active ICP, project, and ranked prospects
to provide a realistic, source-backed operating environment out-of-the-box.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone, timedelta

from growx_crawl.autogtm.projects import project_service
from growx_crawl.intelligence.competitors.models import CompetitorEvidenceEntity, CompetitorRelationshipEntity
from growx_crawl.intelligence.competitors.service import competitor_service
from growx_crawl.intelligence.facts.models import FactEntity, FactValueEntity
from growx_crawl.intelligence.facts.service import fact_service
from growx_crawl.intelligence.icp.models import CriterionCategory, ICPCriterionEntity, ICPExclusionEntity, ICPPersonaEntity
from growx_crawl.intelligence.icp.service import icp_service
from growx_crawl.scoring.models import ProspectEntity, ProspectScoreEntity, RankingExplanationEntity, RankingReasonCode, RankingStatus
from growx_crawl.scoring.service import prospect_ranking_service
from growx_crawl.shared.ids import generate_id
from growx_crawl.shared.time import utc_iso_now

logger = logging.getLogger("growx_crawl.autogtm.seed")

SELLER_ID = "cmp_growxlabs"


def seed_canonical_environment() -> Dict[str, Any]:
    """Ensures rich initial operating data exists for GrowX UI."""
    now = datetime.now(timezone.utc)

    # ── 1. Seller Company (My Company) ──
    try:
        from growx_crawl.identity.service import identity_service
        existing_seller = identity_service.get_company(SELLER_ID)
        if not existing_seller:
            identity_service.resolve_company(
                name="GrowxLabs Intelligence",
                domain="growxlabs.tech",
                metadata={
                    "id": SELLER_ID,
                    "industry": "B2B Intelligence & Sales Automation",
                    "employee_count": 45,
                    "location": "San Francisco, CA & Bengaluru, India",
                    "description": "Continuous intelligence factory and automated GTM infrastructure platform discovering source-backed accounts, buyer contacts, and market signals.",
                    "tagline": "The source-backed intelligence operating system for modern GTM teams.",
                    "products": [
                        "GrowX Crawl Engine",
                        "AutoGTM Prospect Intelligence",
                        "Competitor Graph",
                        "Verified Contact Matrix",
                    ],
                    "target_problems": [
                        "High lead bounce rates from stale legacy B2B databases",
                        "Superficial AI prospecting lacking source evidence",
                        "Disconnected identity across domains, people, and employments",
                    ],
                    "capabilities": [
                        "Nightly continuous crawler and entity resolution",
                        "Multi-source fact verification and quality gates",
                        "Evidence-backed competitor graph mapping",
                        "Multi-dimensional prospect ranking (fit, signals, timing)",
                    ],
                    "is_verified": True,
                    "verification_status": "verified",
                    "quality_gate_passed": True,
                },
            )
    except Exception as e:
        logger.debug(f"Seller company seed check: {e}")

    # ── 2. Competitor Graph ──
    competitors_to_seed = [
        {"name": "Apollo.io", "domain": "apollo.io", "type": "direct", "strength": 0.88, "overlap": "Contact database & email automation"},
        {"name": "ZoomInfo", "domain": "zoominfo.com", "type": "direct", "strength": 0.85, "overlap": "Enterprise account intelligence & org charts"},
        {"name": "Clay", "domain": "clay.com", "type": "adjacent", "strength": 0.78, "overlap": "Waterfalled data enrichment & workflow automation"},
        {"name": "Cognism", "domain": "cognism.com", "type": "adjacent", "strength": 0.72, "overlap": "International phone & EMEA B2B data"},
    ]

    for comp in competitors_to_seed:
        try:
            comp_target_id = f"cmp_{comp['domain'].replace('.', '_')}"
            canonical_pair = f"{min(SELLER_ID, comp_target_id)}:{max(SELLER_ID, comp_target_id)}"
            rel = CompetitorRelationshipEntity(
                id=generate_id("cpr_"),
                company_id=SELLER_ID,
                competitor_company_id=comp_target_id,
                canonical_pair=canonical_pair,
                relationship_type=comp["type"],
                status="verified",
                confidence=0.92,
                strength=comp["strength"],
                market_overlap=comp["strength"],
                evidence_count=1,
                reasons=[f"Competitive overlap in {comp['overlap']}"],
                metadata_json={
                    "competitor_name": comp["name"],
                    "competitor_domain": comp["domain"],
                    "overlap": comp["overlap"],
                    "shared_features": ["B2B Data Factory", "Sales Intelligence"],
                    "advantages": ["First-party verified DOM proof", "Temporal change detection"],
                    "disadvantages": ["Legacy market footprint"],
                },
            )
            competitor_service.repository.save_relationship(rel)

            # Evidence for competitor
            ev = CompetitorEvidenceEntity(
                id=generate_id("cpe_"),
                relationship_id=rel.id,
                evidence_type="market_comparison",
                support_type="positive",
                confidence=0.90,
                metadata_json={
                    "source_url": f"https://g2.com/compare/{comp['domain']}-vs-growx",
                    "claim_text": f"Direct market alternative for {comp['overlap']}",
                },
            )
            competitor_service.repository.save_evidence(ev)
        except Exception as e:
            logger.debug(f"Competitor seed check: {e}")

    # ── 3. Canonical ICP ──
    icp_id = "icp_b2b_saas_expansion"
    try:
        existing_icp = icp_service.get_icp(icp_id)
        if not existing_icp:
            icp = icp_service.create_icp(
                seller_company_id=SELLER_ID,
                name="US Mid-Market B2B SaaS ICP",
                description="Ideal customer profile targeting high-growth North American software companies adopting modern developer & sales infrastructure.",
                criteria=[
                    ICPCriterionEntity(
                        id=generate_id("cr_"),
                        version_id="",
                        category=CriterionCategory.INDUSTRY.value,
                        field_name="industry",
                        operator="in",
                        value=["B2B SaaS", "Enterprise Software", "Cloud Infrastructure", "Fintech"],
                        weight=0.25,
                        mandatory=True,
                    ),
                    ICPCriterionEntity(
                        id=generate_id("cr_"),
                        version_id="",
                        category=CriterionCategory.COMPANY_SIZE.value,
                        field_name="employee_count",
                        operator="between",
                        value={"min": 50, "max": 1000},
                        weight=0.20,
                    ),
                    ICPCriterionEntity(
                        id=generate_id("cr_"),
                        version_id="",
                        category=CriterionCategory.GEOGRAPHY.value,
                        field_name="country",
                        operator="in",
                        value=["United States", "Canada", "United Kingdom"],
                        weight=0.15,
                    ),
                    ICPCriterionEntity(
                        id=generate_id("cr_"),
                        version_id="",
                        category=CriterionCategory.TECHNOLOGY.value,
                        field_name="tech_stack",
                        operator="contains_any",
                        value=["HubSpot", "Salesforce", "Stripe", "Next.js"],
                        weight=0.15,
                    ),
                    ICPCriterionEntity(
                        id=generate_id("cr_"),
                        version_id="",
                        category=CriterionCategory.SIGNALS.value,
                        field_name="signals",
                        operator="contains_any",
                        value=["expansion", "hiring_spike", "funding", "tech_adoption"],
                        weight=0.25,
                    ),
                ],
                personas=[
                    ICPPersonaEntity(
                        id=generate_id("prn_"),
                        version_id="",
                        title="VP of Sales",
                        seniority_tier="vp",
                        department="Sales",
                        weight=0.35,
                    ),
                    ICPPersonaEntity(
                        id=generate_id("prn_"),
                        version_id="",
                        title="Head of Growth",
                        seniority_tier="head",
                        department="Growth",
                        weight=0.35,
                    ),
                    ICPPersonaEntity(
                        id=generate_id("prn_"),
                        version_id="",
                        title="Director of Revenue Operations",
                        seniority_tier="director",
                        department="Operations",
                        weight=0.30,
                    ),
                ],
                exclusions=[
                    ICPExclusionEntity(
                        id=generate_id("ex_"),
                        version_id="",
                        rule_name="Competitors",
                        field_name="is_competitor",
                        operator="eq",
                        value=True,
                        hard_block=True,
                    ),
                    ICPExclusionEntity(
                        id=generate_id("ex_"),
                        version_id="",
                        rule_name="B2C Retail",
                        field_name="industry",
                        operator="eq",
                        value="B2C Retail",
                        hard_block=True,
                    ),
                ],
            )
            icp_id = icp.id
    except Exception as e:
        logger.debug(f"ICP seed check: {e}")

    # ── 4. Canonical Project ──
    project_id = "prj_us_saas_expansion"
    try:
        existing_prj = project_service.get_project(project_id)
        if not existing_prj:
            prj = project_service.create_project(
                name="US Mid-Market SaaS Expansion",
                seller_company_id=SELLER_ID,
                active_icp_id=icp_id,
                target_geography="United States & Canada",
                notes="Primary target market campaign for GrowX AutoGTM Q3. Sourcing high-fit accounts with active buying momentum.",
            )
            # Update canonical ID
            prj.id = project_id
            project_service.repo.save_project(prj)
    except Exception as e:
        logger.debug(f"Project seed check: {e}")

    # ── 5. Seed Prospects and Ranked Scores ──
    prospects_data = [
        {
            "company_id": "cmp_linear",
            "company_name": "Linear",
            "domain": "linear.app",
            "industry": "B2B SaaS",
            "employee_count": 85,
            "location": "San Francisco, CA",
            "person": {"name": "Karri Saarinen", "title": "VP of Growth & Co-Founder", "email": "karri@linear.app", "seniority": "vp"},
            "signals": [{"signal_type": "expansion", "confidence": 0.95, "detected_at": (now - timedelta(days=3)).isoformat()}],
            "icp_score": 0.94,
            "status": RankingStatus.PRIORITY.value,
        },
        {
            "company_id": "cmp_retool",
            "company_name": "Retool",
            "domain": "retool.com",
            "industry": "Enterprise Software",
            "employee_count": 350,
            "location": "San Francisco, CA",
            "person": {"name": "David Hsu", "title": "Chief Revenue Officer", "email": "david@retool.com", "seniority": "c_level"},
            "signals": [{"signal_type": "funding", "confidence": 0.92, "detected_at": (now - timedelta(days=12)).isoformat()}],
            "icp_score": 0.91,
            "status": RankingStatus.PRIORITY.value,
        },
        {
            "company_id": "cmp_datadog",
            "company_name": "Datadog",
            "domain": "datadoghq.com",
            "industry": "Cloud Infrastructure",
            "employee_count": 4500,
            "location": "New York, NY",
            "person": {"name": "Alexandre LeBrun", "title": "Director of Sales", "email": "alex@datadoghq.com", "seniority": "director", "employment_verified_at": (now - timedelta(days=220)).isoformat()},
            "signals": [{"signal_type": "tech_adoption", "confidence": 0.80, "detected_at": (now - timedelta(days=40)).isoformat()}],
            "icp_score": 0.88,
            "status": RankingStatus.REVERIFY.value,
        },
        {
            "company_id": "cmp_supabase",
            "company_name": "Supabase",
            "domain": "supabase.com",
            "industry": "Cloud Infrastructure",
            "employee_count": 120,
            "location": "Singapore / Remote",
            "person": {"name": "Paul Copplestone", "title": "Head of Revenue Operations", "email": "paul@supabase.com", "seniority": "head", "employment_confidence": 0.50},
            "signals": [],
            "icp_score": 0.74,
            "status": RankingStatus.RESEARCH_MORE.value,
        },
        {
            "company_id": "cmp_apollo_io",
            "company_name": "Apollo.io",
            "domain": "apollo.io",
            "industry": "B2B Sales Tech",
            "employee_count": 400,
            "location": "San Francisco, CA",
            "person": {"name": "Tim Zheng", "title": "CEO", "email": "tim@apollo.io", "seniority": "c_level"},
            "is_competitor": True,
            "icp_score": 0.90,
            "status": RankingStatus.NOT_ELIGIBLE.value,
        },
    ]

    for item in prospects_data:
        try:
            prospect = prospect_ranking_service.create_prospect(
                project_id=project_id,
                company_id=item["company_id"],
                person_id=f"prs_{item['company_id']}",
                icp_version_id=icp_id,
                metadata={
                    "company_data": {
                        "id": item["company_id"],
                        "company_name": item["company_name"],
                        "domain": item["domain"],
                        "industry": item["industry"],
                        "employee_count": item["employee_count"],
                        "location": item["location"],
                        "is_verified": True,
                        "quality_gate_passed": True,
                        "is_competitor": item.get("is_competitor", False),
                    },
                    "person_data": item["person"],
                    "signals": item.get("signals", []),
                },
            )

            prospect_ranking_service.rank_prospect(
                prospect_id=prospect.id,
                company_data=prospect.metadata_json.get("company_data"),
                person_data=item["person"],
                signals=item.get("signals"),
                icp_score=item["icp_score"],
                is_competitor=item.get("is_competitor", False),
            )
        except Exception as e:
            logger.debug(f"Prospect seed check: {e}")

    return {
        "status": "seeded",
        "seller_company_id": SELLER_ID,
        "project_id": project_id,
        "icp_id": icp_id,
        "prospects_count": len(prospects_data),
    }
