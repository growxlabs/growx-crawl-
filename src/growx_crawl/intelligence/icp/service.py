"""
GrowX ICP Intelligence Service.
Unified service boundary coordinating ICP generation, version management, prospect evaluation,
explainability, and temporal staleness detection.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from growx_crawl.intelligence.icp.builder import ICPBuilder
from growx_crawl.intelligence.icp.explain import ICPExplainer
from growx_crawl.intelligence.icp.models import (
    CriterionCategory,
    ICPEntity,
    ICPStatus,
    ICPType,
    ICPVersionEntity,
    SellerSnapshotEntity,
    ICPCriterionEntity,
    ICPExclusionEntity,
    ICPPersonaEntity,
    ICPCompanyScoreEntity,
    ICPPersonScoreEntity,
)

from growx_crawl.intelligence.icp.refresh import ICPRefreshEngine
from growx_crawl.intelligence.icp.repository import BaseICPRepository, SqliteICPRepository
from growx_crawl.intelligence.icp.scoring import ICPScorer
from growx_crawl.intelligence.icp.versions import ICPVersionManager
from growx_crawl.shared.ids import generate_id
from growx_crawl.shared.time import utc_iso_now

logger = logging.getLogger("growx_crawl.intelligence.icp.service")


class ICPIntelligenceService:
    """Canonical service for managing versioned ICPs and evaluating prospect accounts and personas."""

    def __init__(
        self,
        repository: Optional[BaseICPRepository] = None,
        builder: Optional[ICPBuilder] = None,
        scorer: Optional[ICPScorer] = None,
        version_manager: Optional[ICPVersionManager] = None,
        refresh_engine: Optional[ICPRefreshEngine] = None,
        explainer: Optional[ICPExplainer] = None,
    ):
        self.repo = repository or SqliteICPRepository()
        self.builder = builder or ICPBuilder()
        self.scorer = scorer or ICPScorer()
        self.version_manager = version_manager or ICPVersionManager()
        self.refresh_engine = refresh_engine or ICPRefreshEngine()
        self.explainer = explainer or ICPExplainer()

    def create_icp(
        self,
        seller_company_id: str,
        name: str,
        description: Optional[str] = None,
        source_type: str = ICPType.SELLER_DERIVED.value,
        target_industries: Optional[List[str]] = None,
        target_geographies: Optional[List[str]] = None,
        target_employee_range: Optional[Tuple[int, int]] = None,
        seller_data: Optional[Dict[str, Any]] = None,
        facts: Optional[List[Any]] = None,
        custom_criteria: Optional[List[Dict[str, Any]]] = None,
        custom_exclusions: Optional[List[Dict[str, Any]]] = None,
        custom_personas: Optional[List[Dict[str, Any]]] = None,
        activate: bool = True,
    ) -> Tuple[ICPEntity, ICPVersionEntity]:
        """Creates a new ICP container with initial Version 1 targeting model."""
        icp_id = generate_id("icp_")

        # 1. Build Version 1
        version, snapshot, criteria, exclusions, personas = self.builder.build_from_seller_context(
            icp_id=icp_id,
            seller_company_id=seller_company_id,
            seller_data=seller_data,
            facts=facts,
            version_num=1,
            target_industries=target_industries,
            target_geographies=target_geographies,
            target_employee_range=target_employee_range,
            custom_criteria=custom_criteria,
            custom_exclusions=custom_exclusions,
            custom_personas=custom_personas,
        )

        if activate:
            version.status = ICPStatus.ACTIVE.value

        # 2. Persist parent ICP
        icp = ICPEntity(
            id=icp_id,
            seller_company_id=seller_company_id,
            name=name,
            description=description,
            status=ICPStatus.ACTIVE.value if activate else ICPStatus.DRAFT.value,
            source_type=source_type,
            current_version_id=version.id if activate else None,
            created_at=utc_iso_now(),
            updated_at=utc_iso_now(),
        )

        self.repo.save_icp(icp)
        self.repo.save_snapshot(snapshot)
        self.repo.save_version(version)
        self.repo.save_criteria(criteria)
        self.repo.save_exclusions(exclusions)
        self.repo.save_personas(personas)

        logger.info(
            f"Created ICP {icp_id} for seller {seller_company_id} with version {version.id} (status: {version.status})"
        )
        return icp, version

    def create_version(
        self,
        icp_id: str,
        seller_data: Optional[Dict[str, Any]] = None,
        facts: Optional[List[Any]] = None,
        target_industries: Optional[List[str]] = None,
        target_geographies: Optional[List[str]] = None,
        target_employee_range: Optional[Tuple[int, int]] = None,
        custom_criteria: Optional[List[Dict[str, Any]]] = None,
        custom_exclusions: Optional[List[Dict[str, Any]]] = None,
        custom_personas: Optional[List[Dict[str, Any]]] = None,
    ) -> ICPVersionEntity:
        """Generates a new draft version for an existing ICP."""
        icp = self.repo.get_icp(icp_id)
        if not icp:
            raise ValueError(f"ICP with id '{icp_id}' not found.")

        existing_versions = self.repo.list_versions(icp_id)
        next_ver = max([v.version for v in existing_versions], default=0) + 1

        prev_version = self.get_active_version(icp_id)
        if prev_version:
            if seller_data is None and prev_version.seller_snapshot_id:
                prev_snap = self.repo.get_snapshot(prev_version.seller_snapshot_id)
                if prev_snap:
                    seller_data = prev_snap.fact_snapshot_json.get("seller_data", {})
            if target_geographies is None:
                prev_crit = self.repo.list_criteria(prev_version.id, category=CriterionCategory.GEOGRAPHIC.value)
                for pc in prev_crit:
                    if pc.field == "country" and isinstance(pc.value_json, list):
                        target_geographies = pc.value_json
                        break
            if target_employee_range is None:
                prev_crit = self.repo.list_criteria(prev_version.id, category=CriterionCategory.FIRMOGRAPHIC.value)
                for pc in prev_crit:
                    if pc.field == "employee_count" and isinstance(pc.value_json, list) and len(pc.value_json) == 2:
                        target_employee_range = (int(pc.value_json[0]), int(pc.value_json[1]))
                        break

        version, snapshot, criteria, exclusions, personas = self.builder.build_from_seller_context(
            icp_id=icp_id,
            seller_company_id=icp.seller_company_id,
            seller_data=seller_data,
            facts=facts,
            version_num=next_ver,
            target_industries=target_industries,
            target_geographies=target_geographies,
            target_employee_range=target_employee_range,
            custom_criteria=custom_criteria,
            custom_exclusions=custom_exclusions,
            custom_personas=custom_personas,
        )
        version.status = ICPStatus.DRAFT.value


        self.repo.save_snapshot(snapshot)
        self.repo.save_version(version)
        self.repo.save_criteria(criteria)
        self.repo.save_exclusions(exclusions)
        self.repo.save_personas(personas)

        logger.info(f"Created draft version {version.id} (v{next_ver}) for ICP {icp_id}")
        return version

    def get_icp(self, icp_id: str) -> Optional[ICPEntity]:
        return self.repo.get_icp(icp_id)

    def list_icps(
        self,
        seller_company_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[ICPEntity]:
        return self.repo.list_icps(seller_company_id=seller_company_id, status=status, limit=limit)

    def get_version(self, version_id: str) -> Optional[ICPVersionEntity]:
        return self.repo.get_version(version_id)

    def list_versions(self, icp_id: str) -> List[ICPVersionEntity]:
        return self.repo.list_versions(icp_id)

    def get_active_version(self, icp_id: str) -> Optional[ICPVersionEntity]:
        icp = self.repo.get_icp(icp_id)
        if not icp:
            return None
        if icp.current_version_id:
            return self.repo.get_version(icp.current_version_id)
        # Fallback to latest active
        versions = self.repo.list_versions(icp_id)
        for v in reversed(versions):
            if v.status == ICPStatus.ACTIVE.value:
                return v
        return None

    def activate_version(self, icp_id: str, version_id: str) -> ICPVersionEntity:
        """Activates target version, transitioning previously active versions to superseded."""
        icp = self.repo.get_icp(icp_id)
        if not icp:
            raise ValueError(f"ICP with id '{icp_id}' not found.")

        target = self.repo.get_version(version_id)
        if not target or target.icp_id != icp_id:
            raise ValueError(f"Version '{version_id}' not found for ICP '{icp_id}'.")

        all_versions = self.repo.list_versions(icp_id)
        activated, superseded = self.version_manager.activate_version(target, all_versions)

        # Update in database
        self.repo.update_version_status(activated.id, ICPStatus.ACTIVE.value)
        for sup in superseded:
            self.repo.update_version_status(sup.id, ICPStatus.SUPERSEDED.value)

        self.repo.update_icp_status(icp_id, ICPStatus.ACTIVE.value, current_version_id=activated.id)
        logger.info(f"Activated version {activated.id} for ICP {icp_id}")
        return activated

    def get_version_details(self, version_id: str) -> Dict[str, Any]:
        """Retrieves full specification of an ICP version."""
        version = self.repo.get_version(version_id)
        if not version:
            raise ValueError(f"Version '{version_id}' not found.")

        criteria = self.repo.list_criteria(version_id)
        exclusions = self.repo.list_exclusions(version_id)
        personas = self.repo.list_personas(version_id)
        snapshot = self.repo.get_snapshot(version.seller_snapshot_id) if version.seller_snapshot_id else None

        return {
            "version": version,
            "criteria": criteria,
            "exclusions": exclusions,
            "personas": personas,
            "snapshot": snapshot,
        }

    def score_company(
        self,
        icp_id: str,
        company_data: Dict[str, Any],
        version_id: Optional[str] = None,
        seller_competitor_ids: Optional[List[str]] = None,
        existing_customer_ids: Optional[List[str]] = None,
        facts: Optional[List[Any]] = None,
        signals: Optional[List[Any]] = None,
    ) -> ICPCompanyScoreEntity:
        """Scores a prospect company against an ICP version."""
        icp = self.repo.get_icp(icp_id)
        if not icp:
            raise ValueError(f"ICP '{icp_id}' not found.")

        if version_id:
            target_version = self.repo.get_version(version_id)
        else:
            target_version = self.get_active_version(icp_id)

        if not target_version:
            raise ValueError(f"No active version found for ICP '{icp_id}'.")

        # Automatically discover competitors from competitor graph if not explicitly provided
        if seller_competitor_ids is None and icp.seller_company_id:
            try:
                from growx_crawl.intelligence.competitors.service import competitor_service
                rels = competitor_service.get_competitors(icp.seller_company_id)
                seller_competitor_ids = [r.competitor_company_id for r in rels]
            except Exception:
                seller_competitor_ids = []

        criteria = self.repo.list_criteria(target_version.id)
        exclusions = self.repo.list_exclusions(target_version.id)

        score = self.scorer.score_company(
            icp_version_id=target_version.id,
            criteria=criteria,
            exclusions=exclusions,
            company_data=company_data,
            facts=facts,
            signals=signals,
            seller_competitor_ids=seller_competitor_ids,
            existing_customer_ids=existing_customer_ids,
        )

        self.repo.save_company_score(score)
        return score

    def score_person(
        self,
        icp_id: str,
        person_data: Dict[str, Any],
        company_id: str,
        version_id: Optional[str] = None,
    ) -> ICPPersonScoreEntity:
        """Scores an individual buyer within a company against ICP personas."""
        if version_id:
            target_version = self.repo.get_version(version_id)
        else:
            target_version = self.get_active_version(icp_id)

        if not target_version:
            raise ValueError(f"No active version found for ICP '{icp_id}'.")

        personas = self.repo.list_personas(target_version.id)

        score = self.scorer.score_person(
            icp_version_id=target_version.id,
            personas=personas,
            person_data=person_data,
            company_id=company_id,
        )

        self.repo.save_person_score(score)
        return score

    def query_matches(
        self,
        icp_id: str,
        version_id: Optional[str] = None,
        min_fit: float = 0.5,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[ICPCompanyScoreEntity]:
        """Queries prospects evaluated against an ICP meeting a minimum fit threshold."""
        if version_id:
            target_version = self.repo.get_version(version_id)
        else:
            target_version = self.get_active_version(icp_id)

        if not target_version:
            return []

        return self.repo.list_company_scores(
            icp_version_id=target_version.id,
            min_fit=min_fit,
            status=status,
            limit=limit,
        )

    def compare_versions(self, version_a_id: str, version_b_id: str) -> Dict[str, Any]:
        """Compares two ICP versions and outputs differences in criteria, exclusions, and personas."""
        details_a = self.get_version_details(version_a_id)
        details_b = self.get_version_details(version_b_id)

        return self.version_manager.compare_versions(
            version_a=details_a["version"],
            version_b=details_b["version"],
            criteria_a=details_a["criteria"],
            criteria_b=details_b["criteria"],
            exclusions_a=details_a["exclusions"],
            exclusions_b=details_b["exclusions"],
            personas_a=details_a["personas"],
            personas_b=details_b["personas"],
        )

    def check_refresh(
        self,
        icp_id: str,
        current_seller_data: Optional[Dict[str, Any]] = None,
        current_seller_facts: Optional[List[Any]] = None,
        max_age_days: Optional[int] = None,
    ) -> Tuple[bool, List[str]]:
        """Checks if an ICP needs a refreshed version due to age or seller fact changes."""
        icp = self.repo.get_icp(icp_id)
        if not icp:
            return True, ["ICP not found."]

        active_version = self.get_active_version(icp_id)
        snapshot = None
        if active_version and active_version.seller_snapshot_id:
            snapshot = self.repo.get_snapshot(active_version.seller_snapshot_id)

        return self.refresh_engine.evaluate_icp_staleness(
            icp=icp,
            active_version=active_version,
            snapshot=snapshot,
            current_seller_data=current_seller_data,
            current_seller_facts=current_seller_facts,
            max_age_days=max_age_days,
        )


# Global singleton instance
icp_service = ICPIntelligenceService()
