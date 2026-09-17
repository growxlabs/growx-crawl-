"""
GrowX ICP Builder.
Constructs structured, versioned ICP definitions from seller facts, competitor context, and policy.
Captures reproducible SellerSnapshots.
"""

from typing import Any, Dict, List, Optional, Tuple
from growx_crawl.intelligence.icp.models import (
    CriterionCategory,
    CriterionOperator,
    ExclusionType,
    ICPCriterionEntity,
    ICPExclusionEntity,
    ICPPersonaEntity,
    ICPStatus,
    ICPVersionEntity,
    PersonaCategory,
    RequirementType,
    SellerSnapshotEntity,
)
from growx_crawl.shared.ids import generate_id
from growx_crawl.shared.time import utc_iso_now


class ICPBuilder:
    """Constructs structured, versioned ICP definitions."""

    def build_from_seller_context(
        self,
        icp_id: str,
        seller_company_id: str,
        seller_data: Optional[Dict[str, Any]] = None,
        facts: Optional[List[Any]] = None,
        version_num: int = 1,
        target_industries: Optional[List[str]] = None,
        target_geographies: Optional[List[str]] = None,
        target_employee_range: Optional[Tuple[int, int]] = None,
        custom_criteria: Optional[List[Dict[str, Any]]] = None,
        custom_exclusions: Optional[List[Dict[str, Any]]] = None,
        custom_personas: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[
        ICPVersionEntity,
        SellerSnapshotEntity,
        List[ICPCriterionEntity],
        List[ICPExclusionEntity],
        List[ICPPersonaEntity],
    ]:
        """
        Synthesizes structured targeting model from seller data, facts, and parameters.
        Preserves an immutable SellerSnapshot.
        """
        data = seller_data or {}

        # 1. Capture Seller Snapshot (Section 20)
        snapshot_id = generate_id("snp_")
        snapshot = SellerSnapshotEntity(
            id=snapshot_id,
            seller_company_id=seller_company_id,
            fact_snapshot_json={
                "seller_data": data,
                "fact_count": len(facts) if facts else 0,
            },
            verified_at=utc_iso_now(),
        )

        version_id = generate_id("icpv_")
        version = ICPVersionEntity(
            id=version_id,
            icp_id=icp_id,
            version=version_num,
            status=ICPStatus.DRAFT.value,
            seller_snapshot_id=snapshot_id,
        )

        criteria: List[ICPCriterionEntity] = []
        exclusions: List[ICPExclusionEntity] = []
        personas: List[ICPPersonaEntity] = []

        # 2. Derive Firmographic Criteria (Industry, Size)
        inds = target_industries or (
            [data["industry"]] if data.get("industry") else ["B2B Technology", "Manufacturing"]
        )
        criteria.append(
            ICPCriterionEntity(
                id=generate_id("cr_"),
                icp_version_id=version_id,
                category=CriterionCategory.FIRMOGRAPHIC.value,
                field="industry",
                operator=CriterionOperator.IN.value,
                value_json=inds,
                weight=1.5,
                requirement_type=RequirementType.REQUIRED.value,
            )
        )

        size_range = target_employee_range or (20, 5000)
        criteria.append(
            ICPCriterionEntity(
                id=generate_id("cr_"),
                icp_version_id=version_id,
                category=CriterionCategory.FIRMOGRAPHIC.value,
                field="employee_count",
                operator=CriterionOperator.RANGE.value,
                value_json=list(size_range),
                weight=1.0,
                requirement_type=RequirementType.REQUIRED.value,
            )
        )

        # 3. Derive Geographic Criteria
        geos = target_geographies or (
            [data["country_code"]] if data.get("country_code") else ["IN", "US", "United States", "India"]
        )

        criteria.append(
            ICPCriterionEntity(
                id=generate_id("cr_"),
                icp_version_id=version_id,
                category=CriterionCategory.GEOGRAPHIC.value,
                field="country",
                operator=CriterionOperator.IN.value,
                value_json=geos,
                weight=1.0,
                requirement_type=RequirementType.REQUIRED.value,
            )
        )

        # 4. Derive Operational / Signal Criteria (Preferred/Boost)
        criteria.append(
            ICPCriterionEntity(
                id=generate_id("cr_"),
                icp_version_id=version_id,
                category=CriterionCategory.SIGNAL.value,
                field="employee_growth",
                operator=CriterionOperator.EXISTS.value,
                value_json=True,
                weight=0.8,
                requirement_type=RequirementType.BOOST.value,
            )
        )

        # 5. Default Exclusions (Competitors & Existing Customers - Sections 36-37)
        exclusions.append(
            ICPExclusionEntity(
                id=generate_id("ex_"),
                icp_version_id=version_id,
                rule_type=ExclusionType.COMPETITOR.value,
                field="company_id",
                operator=CriterionOperator.EQUALS.value,
                value_json="competitor",
                reason="Exclude verified seller competitors from prospecting",
            )
        )
        exclusions.append(
            ICPExclusionEntity(
                id=generate_id("ex_"),
                icp_version_id=version_id,
                rule_type=ExclusionType.EXISTING_CUSTOMER.value,
                field="company_id",
                operator=CriterionOperator.EQUALS.value,
                value_json="existing_customer",
                reason="Exclude existing active customers from new logo campaigns",
            )
        )

        # 6. Structured Buyer Personas (Section 45-47)
        default_personas = [
            {
                "name": "Chief Technology Officer / Head of IT",
                "department": "technology",
                "seniority": "c_level",
                "patterns": ["cto", "chief technology officer", "vp of it", "head of it", "director of it", "head of information technology"],
                "category": PersonaCategory.TECHNICAL_BUYER.value,
                "priority": 1,
            },
            {
                "name": "Chief Operating Officer / Plant Head",
                "department": "operations",
                "seniority": "executive",
                "patterns": ["coo", "chief operating officer", "head of operations", "plant head", "vp operations", "operations director"],
                "category": PersonaCategory.OPERATIONAL_BUYER.value,
                "priority": 1,
            },
            {
                "name": "Chief Executive Officer / Founder",
                "department": "executive",
                "seniority": "c_level",
                "patterns": ["ceo", "founder", "managing director", "president", "co-founder"],
                "category": PersonaCategory.ECONOMIC_BUYER.value,
                "priority": 2,
            },
        ]
        for p in (custom_personas or default_personas):
            personas.append(
                ICPPersonaEntity(
                    id=generate_id("prn_"),
                    icp_version_id=version_id,
                    name=p.get("name", "Decision Maker"),
                    department=p.get("department", "executive"),
                    seniority=p.get("seniority", "executive"),
                    title_patterns=p.get("title_patterns", p.get("patterns", [])),
                    persona_category=p.get("persona_category", p.get("category", PersonaCategory.TECHNICAL_BUYER.value)),
                    priority=p.get("priority", 1),
                )
            )

        # 7. Add any custom criteria
        if custom_criteria:
            for cc in custom_criteria:
                val = cc.get("value_json", cc.get("value"))
                criteria.append(
                    ICPCriterionEntity(
                        id=generate_id("cr_"),
                        icp_version_id=version_id,
                        category=cc.get("category", CriterionCategory.FIRMOGRAPHIC.value),
                        field=cc["field"],
                        operator=cc.get("operator", CriterionOperator.EQUALS.value),
                        value_json=val,
                        weight=float(cc.get("weight", 1.0)),
                        requirement_type=cc.get("requirement_type", RequirementType.PREFERRED.value),
                    )
                )

        # 8. Add any custom exclusions
        if custom_exclusions:
            for ce in custom_exclusions:
                val = ce.get("value_json", ce.get("value"))
                exclusions.append(
                    ICPExclusionEntity(
                        id=generate_id("ex_"),
                        icp_version_id=version_id,
                        rule_type=ce.get("rule_type", ExclusionType.BAD_FIT.value),
                        field=ce["field"],
                        operator=ce.get("operator", CriterionOperator.EQUALS.value),
                        value_json=val,
                        reason=ce.get("reason", "Custom disqualifier"),
                    )
                )

        return version, snapshot, criteria, exclusions, personas

