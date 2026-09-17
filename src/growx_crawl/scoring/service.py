"""
GrowX Scoring Service.
Maintains strict separation between:
1. Data Confidence
2. ICP Fit
3. Buying Signal
4. Priority
"""

from typing import Any, Callable, Dict, List, Optional, Tuple
import logging
from pydantic import BaseModel, Field
from growx_crawl.core.enums import PriorityLevel
from growx_crawl.scoring.buying_signal import calculate_buying_signal
from growx_crawl.scoring.data_confidence import calculate_data_confidence
from growx_crawl.scoring.icp_fit import calculate_icp_fit
from growx_crawl.scoring.models import (
    ProspectEntity,
    ProspectScoreEntity,
    ProspectScoreHistoryEntity,
    ProspectStatus,
    RankingExplanationEntity,
    RankingProfileEntity,
    RankingStatus,
)
from growx_crawl.scoring.profiles import BUILTIN_PROFILES, RankingProfileConfig, profile_registry
from growx_crawl.scoring.prospect_ranker import ProspectRanker
from growx_crawl.scoring.repository import BaseRankingRepository, SqliteRankingRepository
from growx_crawl.shared.ids import generate_id
from growx_crawl.shared.time import utc_iso_now

logger = logging.getLogger("growx_crawl.scoring.service")


class CompanyScoreBreakdown(BaseModel):
    data_confidence: float = Field(ge=0.0, le=100.0)
    icp_fit: float = Field(ge=0.0, le=100.0)
    buying_signal: float = Field(ge=0.0, le=100.0)
    priority: PriorityLevel
    reasons: List[str] = Field(default_factory=list)


class ScoringService:
    """Canonical service boundary for evaluating multidimensional lead scores."""

    def score_company(
        self,
        company_data: Dict[str, Any],
        target_industry: Optional[str] = None,
        target_location: Optional[str] = None,
        signals: Optional[List[Dict[str, Any]]] = None,
    ) -> CompanyScoreBreakdown:
        conf_score, conf_reasons = calculate_data_confidence(company_data)
        icp_score, icp_reasons = calculate_icp_fit(company_data, target_industry, target_location)
        sig_score, sig_reasons = calculate_buying_signal(signals or [])

        # Priority evaluates multi-factor balance
        composite = (conf_score * 0.25) + (icp_score * 0.45) + (sig_score * 0.30)
        if composite >= 75.0 or (icp_score >= 80.0 and conf_score >= 60.0):
            priority = PriorityLevel.HIGH
        elif composite >= 50.0:
            priority = PriorityLevel.MEDIUM
        else:
            priority = PriorityLevel.LOW

        all_reasons = conf_reasons + icp_reasons + sig_reasons
        return CompanyScoreBreakdown(
            data_confidence=conf_score,
            icp_fit=icp_score,
            buying_signal=sig_score,
            priority=priority,
            reasons=all_reasons,
        )


scoring_service = ScoringService()


class ProspectRankingService:
    """Canonical service boundary for evaluating, ranking, and managing prospect priority queues."""

    def __init__(
        self,
        repository: Optional[BaseRankingRepository] = None,
        ranker: Optional[ProspectRanker] = None,
    ):
        self.repo = repository or SqliteRankingRepository()
        self.ranker = ranker or ProspectRanker()
        self._seed_builtin_profiles()

    def _seed_builtin_profiles(self) -> None:
        """Ensures builtin ranking profiles exist in storage."""
        try:
            for prof_id, prof_cfg in BUILTIN_PROFILES.items():
                existing = self.repo.get_profile(prof_id)
                if not existing:
                    self.repo.save_profile(
                        RankingProfileEntity(
                            id=prof_id,
                            name=prof_cfg.name,
                            version=prof_cfg.version,
                            config_json=prof_cfg.model_dump(),
                            enabled=prof_cfg.enabled,
                        )
                    )
        except Exception as e:
            logger.debug(f"Could not seed builtin profiles: {e}")

    def create_prospect(
        self,
        project_id: str,
        company_id: str,
        person_id: Optional[str] = None,
        icp_version_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ProspectEntity:
        """Creates or returns an existing prospect association."""
        existing = self.repo.get_prospect_by_entity(project_id, company_id, person_id)
        if existing:
            return existing

        prospect = ProspectEntity(
            id=generate_id("prsp_"),
            project_id=project_id,
            company_id=company_id,
            person_id=person_id,
            icp_version_id=icp_version_id,
            status=ProspectStatus.CANDIDATE.value,
            metadata_json=metadata or {},
        )
        return self.repo.save_prospect(prospect)

    def get_prospect(self, prospect_id: str) -> Optional[ProspectEntity]:
        """Retrieves a prospect by canonical identifier."""
        return self.repo.get_prospect(prospect_id)

    def list_prospects(
        self, project_id: Optional[str] = None, status: Optional[str] = None, limit: int = 50
    ) -> List[ProspectEntity]:
        """Lists prospects matching optional project or status filters."""
        return self.repo.list_prospects(project_id=project_id, status=status, limit=limit)

    def update_prospect_status(self, prospect_id: str, status: str) -> Optional[ProspectEntity]:
        """Updates lifecycle status for a prospect."""
        prospect = self.repo.get_prospect(prospect_id)
        if not prospect:
            return None
        prospect.status = status
        prospect.updated_at = utc_iso_now()
        return self.repo.save_prospect(prospect)

    def rank_prospect(
        self,
        prospect_id: str,
        company_data: Optional[Dict[str, Any]] = None,
        person_data: Optional[Dict[str, Any]] = None,
        signals: Optional[List[Any]] = None,
        icp_score: Optional[float] = None,
        icp_version_id: Optional[str] = None,
        ranking_profile_id: str = "default_v1",
        profile_config: Optional[RankingProfileConfig] = None,
        is_competitor: bool = False,
        is_hard_excluded: bool = False,
        quality_gate_blocked: bool = False,
    ) -> Tuple[ProspectScoreEntity, List[RankingExplanationEntity]]:
        """
        Evaluates and persists multidimensional ranking score and explanations for a prospect.
        """
        prospect = self.repo.get_prospect(prospect_id)
        if company_data is None:
            if prospect:
                company_data = prospect.metadata_json.get("company_data", {"company_id": prospect.company_id, "id": prospect.company_id})
                person_data = person_data or prospect.metadata_json.get("person_data")
                icp_version_id = icp_version_id or prospect.icp_version_id
            else:
                company_data = {"company_id": "cmp_unknown", "id": "cmp_unknown"}

        score_ent, explanations = self.ranker.rank_prospect(
            prospect_id=prospect_id,
            company_data=company_data,
            person_data=person_data,
            signals=signals,
            icp_score=icp_score,
            icp_version_id=icp_version_id,
            profile_config=profile_config,
            ranking_profile_id=ranking_profile_id,
            is_competitor=is_competitor,
            is_hard_excluded=is_hard_excluded,
            quality_gate_blocked=quality_gate_blocked,
        )

        # Persist score and explanations
        self.repo.save_score(score_ent)
        self.repo.save_explanations(explanations)

        # Snapshot history
        self.repo.save_score_history(
            ProspectScoreHistoryEntity(
                id=generate_id("rkh_"),
                prospect_id=prospect_id,
                score_id=score_ent.id,
                ranking_profile_id=score_ent.ranking_profile_id,
                rank_position=score_ent.rank_position,
                final_score=score_ent.final_score,
                status=score_ent.status,
                calculated_at=score_ent.calculated_at,
                metadata_json=score_ent.metadata_json,
            )
        )

        # Update prospect lifecycle status if prospect exists
        if prospect:
            if score_ent.status == RankingStatus.NOT_ELIGIBLE.value:
                prospect.status = ProspectStatus.REJECTED.value
            elif score_ent.status in (RankingStatus.PRIORITY.value, RankingStatus.STRONG.value):
                prospect.status = ProspectStatus.CAMPAIGN_READY.value
            elif score_ent.status == RankingStatus.RESEARCH_MORE.value:
                prospect.status = ProspectStatus.RESEARCHING.value
            elif score_ent.status == RankingStatus.REVERIFY.value:
                prospect.status = ProspectStatus.QUALIFIED.value
            else:
                prospect.status = ProspectStatus.RANKED.value
            prospect.updated_at = utc_iso_now()
            self.repo.save_prospect(prospect)

        return score_ent, explanations

    def rank_batch(
        self,
        candidates: List[Dict[str, Any]],
        ranking_profile_id: str = "default_v1",
        profile_config: Optional[RankingProfileConfig] = None,
    ) -> List[Tuple[ProspectScoreEntity, List[RankingExplanationEntity]]]:
        """
        Evaluates a batch of prospect candidates, assigns rank positions, and persists results.
        """
        scored_pairs = self.ranker.rank_batch(
            prospect_candidates=candidates,
            profile_config=profile_config,
            ranking_profile_id=ranking_profile_id,
        )

        for score_ent, explanations in scored_pairs:
            self.repo.save_score(score_ent)
            self.repo.save_explanations(explanations)
            self.repo.save_score_history(
                ProspectScoreHistoryEntity(
                    id=generate_id("rkh_"),
                    prospect_id=score_ent.prospect_id,
                    score_id=score_ent.id,
                    ranking_profile_id=score_ent.ranking_profile_id,
                    rank_position=score_ent.rank_position,
                    final_score=score_ent.final_score,
                    status=score_ent.status,
                    calculated_at=score_ent.calculated_at,
                    metadata_json=score_ent.metadata_json,
                )
            )
            # Update prospect status if entity exists in repo
            prospect = self.repo.get_prospect(score_ent.prospect_id)
            if prospect:
                if score_ent.status == RankingStatus.NOT_ELIGIBLE.value:
                    prospect.status = ProspectStatus.REJECTED.value
                elif score_ent.status in (RankingStatus.PRIORITY.value, RankingStatus.STRONG.value):
                    prospect.status = ProspectStatus.CAMPAIGN_READY.value
                elif score_ent.status == RankingStatus.RESEARCH_MORE.value:
                    prospect.status = ProspectStatus.RESEARCHING.value
                else:
                    prospect.status = ProspectStatus.RANKED.value
                prospect.updated_at = utc_iso_now()
                self.repo.save_prospect(prospect)

        return scored_pairs

    def rank_account_first(
        self,
        candidates: List[Dict[str, Any]],
        icp_version_id: Optional[str] = None,
        profile_id: str = "account_first_v1",
        max_people_per_account: int = 3,
    ) -> List[ProspectScoreEntity]:
        """
        Account-First Ranking Strategy (Section 25, 41):
        1. Groups candidates by company_id.
        2. Evaluates contacts per account, selecting top N buyer contacts per company.
        3. Ranks final queue across all accounts using account-first profile weights.
        """
        # Group candidates by company_id
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for cand in candidates:
            c_data = cand.get("company_data", {})
            cid = c_data.get("id") or c_data.get("company_id") or "unknown_company"
            grouped.setdefault(cid, []).append(cand)

        selected_candidates: List[Dict[str, Any]] = []

        for cid, company_candidates in grouped.items():
            # If company has multiple person candidates, evaluate each and keep top N
            if len(company_candidates) > max_people_per_account:
                # Score them within the account
                temp_scores: List[Tuple[float, Dict[str, Any]]] = []
                for cand in company_candidates:
                    score_ent, _ = self.ranker.rank_prospect(
                        prospect_id=cand.get("prospect_id", generate_id("prsp_")),
                        company_data=cand.get("company_data", {}),
                        person_data=cand.get("person_data"),
                        signals=cand.get("signals"),
                        icp_score=cand.get("icp_score"),
                        icp_version_id=icp_version_id or cand.get("icp_version_id"),
                        ranking_profile_id=profile_id,
                    )
                    temp_scores.append((score_ent.final_score, cand))
                # Sort descending and take top N
                temp_scores.sort(key=lambda x: x[0], reverse=True)
                selected_candidates.extend([cand for _, cand in temp_scores[:max_people_per_account]])
            else:
                selected_candidates.extend(company_candidates)

        # Batch rank the selected set across all accounts
        scored_pairs = self.rank_batch(
            candidates=selected_candidates,
            ranking_profile_id=profile_id,
        )

        return [score_ent for score_ent, _ in scored_pairs]

    def get_ranked_queue(
        self,
        ranking_profile_id: Optional[str] = None,
        status: Optional[str] = None,
        min_score: float = 0.0,
        limit: int = 50,
    ) -> List[ProspectScoreEntity]:
        """Returns the prioritized prospect score queue ordered by rank and score."""
        return self.repo.list_scores(
            ranking_profile_id=ranking_profile_id,
            status=status,
            min_score=min_score,
            limit=limit,
        )

    def get_score(self, score_id: str) -> Optional[ProspectScoreEntity]:
        """Retrieves a prospect score by ID."""
        return self.repo.get_score(score_id)

    def get_prospect_score(
        self, prospect_id: str, ranking_profile_id: Optional[str] = None
    ) -> Optional[ProspectScoreEntity]:
        """Retrieves the latest score for a prospect."""
        return self.repo.get_latest_prospect_score(prospect_id, ranking_profile_id)

    def get_score_history(self, prospect_id: str) -> List[ProspectScoreHistoryEntity]:
        """Returns chronological score history for a prospect."""
        return self.repo.list_score_history(prospect_id)

    def get_score_explanations(self, score_id: str) -> List[RankingExplanationEntity]:
        """Retrieves individual explanation contributions for a score."""
        return self.repo.list_explanations(score_id)

    def create_profile(
        self, name: str, config: Dict[str, Any], profile_id: Optional[str] = None
    ) -> RankingProfileEntity:
        """Registers a custom ranking profile."""
        pid = profile_id or generate_id("rkp_")
        profile_cfg = RankingProfileConfig(**config)
        profile_registry.register_profile(pid, profile_cfg)

        entity = RankingProfileEntity(
            id=pid,
            name=name,
            version=profile_cfg.version,
            config_json=profile_cfg.model_dump(),
            enabled=profile_cfg.enabled,
        )
        return self.repo.save_profile(entity)

    def get_profile(self, profile_id: str) -> Optional[RankingProfileEntity]:
        """Retrieves profile configuration entity."""
        entity = self.repo.get_profile(profile_id)
        if entity:
            return entity
        cfg = BUILTIN_PROFILES.get(profile_id)
        if cfg:
            return RankingProfileEntity(
                id=profile_id,
                name=cfg.name,
                version=cfg.version,
                config_json=cfg.model_dump(),
                enabled=cfg.enabled,
            )
        return None

    def list_profiles(self, limit: int = 50) -> List[RankingProfileEntity]:
        """Lists active ranking profiles."""
        profiles = self.repo.list_profiles(limit=limit)
        if not profiles:
            self._seed_builtin_profiles()
            profiles = self.repo.list_profiles(limit=limit)
        if not profiles:
            return [
                RankingProfileEntity(
                    id=pid,
                    name=cfg.name,
                    version=cfg.version,
                    config_json=cfg.model_dump(),
                    enabled=cfg.enabled,
                )
                for pid, cfg in BUILTIN_PROFILES.items()
            ][:limit]
        return profiles

    def compare_profiles(
        self,
        prospect_id: str,
        company_data: Dict[str, Any],
        person_data: Optional[Dict[str, Any]] = None,
        signals: Optional[List[Any]] = None,
        icp_score: Optional[float] = None,
        profile_a: str = "default_v1",
        profile_b: str = "high_intent_v1",
    ) -> Dict[str, Any]:
        """
        Profile Sensitivity Analysis (Section 44, 45, 66):
        Ranks prospect under two different profiles to measure score shift and ranking sensitivity.
        """
        score_a, _ = self.ranker.rank_prospect(
            prospect_id=prospect_id,
            company_data=company_data,
            person_data=person_data,
            signals=signals,
            icp_score=icp_score,
            ranking_profile_id=profile_a,
        )
        score_b, _ = self.ranker.rank_prospect(
            prospect_id=prospect_id,
            company_data=company_data,
            person_data=person_data,
            signals=signals,
            icp_score=icp_score,
            ranking_profile_id=profile_b,
        )

        return {
            "prospect_id": prospect_id,
            "profile_a": {
                "profile_id": profile_a,
                "final_score": score_a.final_score,
                "raw_score": score_a.raw_score,
                "status": score_a.status,
                "score_id": score_a.id,
            },
            "profile_b": {
                "profile_id": profile_b,
                "final_score": score_b.final_score,
                "raw_score": score_b.raw_score,
                "status": score_b.status,
                "score_id": score_b.id,
            },
            "score_delta": round(score_b.final_score - score_a.final_score, 4),
            "status_delta": f"{score_a.status} -> {score_b.status}",
        }


prospect_ranking_service = ProspectRankingService()

