"""
GrowX Prospect Ranker.
Core deterministic ranking engine coordinating multi-dimensional evaluation, hard blocks,
workflow states (REVERIFY, RESEARCH_MORE), confidence calibration, and idempotency fingerprints.
"""

import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple

from growx_crawl.scoring.account_score import AccountScoreCalculator
from growx_crawl.scoring.confidence import ConfidenceAdjuster
from growx_crawl.scoring.contactability import ContactabilityCalculator
from growx_crawl.scoring.explain import RankingExplainer
from growx_crawl.scoring.freshness_score import FreshnessScoreCalculator
from growx_crawl.scoring.models import (
    ProspectScoreEntity,
    RankingExplanationEntity,
    RankingReasonCode,
    RankingStatus,
)
from growx_crawl.scoring.person_score import PersonScoreCalculator
from growx_crawl.scoring.policies import normalize_score
from growx_crawl.scoring.profiles import BUILTIN_PROFILES, RankingProfileConfig
from growx_crawl.scoring.signal_score import SignalScoreCalculator
from growx_crawl.scoring.timing_score import TimingScoreCalculator
from growx_crawl.shared.ids import generate_id
from growx_crawl.shared.time import utc_iso_now


class ProspectRanker:
    """Evaluates and ranks prospects against versioned ranking profiles."""

    def __init__(
        self,
        account_calculator: Optional[AccountScoreCalculator] = None,
        person_calculator: Optional[PersonScoreCalculator] = None,
        signal_calculator: Optional[SignalScoreCalculator] = None,
        timing_calculator: Optional[TimingScoreCalculator] = None,
        contactability_calculator: Optional[ContactabilityCalculator] = None,
        freshness_calculator: Optional[FreshnessScoreCalculator] = None,
    ):
        self.account_calc = account_calculator or AccountScoreCalculator()
        self.person_calc = person_calculator or PersonScoreCalculator()
        self.signal_calc = signal_calculator or SignalScoreCalculator()
        self.timing_calc = timing_calculator or TimingScoreCalculator()
        self.contact_calc = contactability_calculator or ContactabilityCalculator()
        self.freshness_calc = freshness_calculator or FreshnessScoreCalculator()
        self.explainer = RankingExplainer()

    def rank_prospect(
        self,
        prospect_id: str,
        company_data: Dict[str, Any],
        person_data: Optional[Dict[str, Any]] = None,
        signals: Optional[List[Any]] = None,
        icp_score: Optional[float] = None,
        icp_version_id: Optional[str] = None,
        profile_config: Optional[RankingProfileConfig] = None,
        ranking_profile_id: str = "default_v1",
        is_competitor: bool = False,
        is_hard_excluded: bool = False,
        quality_gate_blocked: bool = False,
    ) -> Tuple[ProspectScoreEntity, List[RankingExplanationEntity]]:
        """
        Calculates multidimensional score and status for a single prospect.
        Returns (ProspectScoreEntity, List[RankingExplanationEntity]).
        """
        profile = profile_config or BUILTIN_PROFILES.get(ranking_profile_id, BUILTIN_PROFILES["default_v1"])
        company_id = company_data.get("id") or company_data.get("company_id") or "cmp_unknown"
        person_id = (person_data.get("id") or person_data.get("person_id")) if person_data else None
        prospect_name = (person_data.get("name") if person_data else None) or company_data.get("company_name") or company_id
        score_id = generate_id("prs_")

        # ── 1. HARD BLOCKS (Section 21, 71) ──
        # Check hard blocks that immediately yield NOT_ELIGIBLE with 0.0 final score
        hard_block_reason: Optional[str] = None

        if is_competitor or company_data.get("is_competitor"):
            hard_block_reason = RankingReasonCode.COMPETITOR_EXCLUDED.value
        elif is_hard_excluded or company_data.get("status") == "excluded":
            hard_block_reason = RankingReasonCode.HARD_ICP_EXCLUSION.value
        elif quality_gate_blocked or company_data.get("quality_status") == "blocked":
            hard_block_reason = RankingReasonCode.BLOCKED_QUALITY_GATE.value

        # Contactability calculation (checks suppression & invalid email)
        contact_res = self.contact_calc.calculate(person_data=person_data, company_data=company_data)
        if contact_res.is_suppressed:
            hard_block_reason = RankingReasonCode.SUPPRESSED_CONTACT.value
        elif not contact_res.is_valid_email and contact_res.email_type == "invalid":
            hard_block_reason = RankingReasonCode.INVALID_EMAIL.value

        if hard_block_reason:
            fp = self._compute_fingerprint(company_id, person_id, icp_version_id, ranking_profile_id, company_data)
            exp_data = self.explainer.explain(
                score_id=score_id,
                prospect_name=prospect_name,
                final_score=0.0,
                raw_score=0.0,
                confidence_factor=1.0,
                status=RankingStatus.NOT_ELIGIBLE.value,
                reason_codes=[hard_block_reason],
                account_contrib=0.0,
                person_contrib=0.0,
                signal_contrib=0.0,
                timing_contrib=0.0,
                contact_contrib=0.0,
                penalty_deduction=0.0,
            )
            score_entity = ProspectScoreEntity(
                id=score_id,
                prospect_id=prospect_id,
                company_id=company_id,
                person_id=person_id,
                icp_version_id=icp_version_id,
                ranking_profile_id=ranking_profile_id,
                account_score=0.0,
                person_score=0.0,
                signal_score=0.0,
                timing_score=0.0,
                quality_score=0.0,
                verification_score=0.0,
                contactability_score=0.0,
                penalty_score=1.0,
                raw_score=0.0,
                confidence_factor=0.0,
                final_score=0.0,
                status=RankingStatus.NOT_ELIGIBLE.value,
                calculated_at=utc_iso_now(),
                fingerprint=fp,
                metadata_json={"narrative": exp_data["narrative"], "reason_codes": [hard_block_reason]},
            )
            return score_entity, exp_data["entities"]

        # ── 2. COMPONENT SCORING ──
        # Account score
        acc_res = self.account_calc.calculate(
            company_data=company_data,
            icp_fit=icp_score,
            verification_score=company_data.get("verification_score"),
            quality_score=company_data.get("quality_score"),
            historical_summary=company_data.get("historical_summary"),
        )

        # Person score
        per_res = self.person_calc.calculate(
            person_data=person_data,
            persona_score=person_data.get("fit_score") if person_data else None,
        )

        # Signal score
        sig_res = self.signal_calc.calculate(signals=signals)

        # Timing score
        tim_res = self.timing_calc.calculate(signals=signals, decay_halflife_days=profile.signal_decay_halflife_days)

        # Freshness score
        fresh_res = self.freshness_calc.calculate(company_data=company_data, person_data=person_data)

        # Penalties: freshness + contactability penalties
        total_penalties = fresh_res.penalties
        if contact_res.email_type == "role_mailbox":
            total_penalties += profile.role_mailbox_penalty
        elif contact_res.email_type == "missing":
            total_penalties += profile.missing_email_penalty

        # ── 3. RAW WEIGHTED SCORE COMBINATION ──
        acc_contrib = profile.account_weight * acc_res.score
        per_contrib = profile.person_weight * per_res.score
        sig_contrib = profile.signal_weight * sig_res.score
        tim_contrib = profile.timing_weight * tim_res.score
        con_contrib = profile.contactability_weight * contact_res.score

        raw_score = acc_contrib + per_contrib + sig_contrib + tim_contrib + con_contrib - total_penalties
        raw_score = normalize_score(max(0.0, raw_score))

        # ── 4. CONFIDENCE FACTOR & ADJUSTED SCORE (Section 24, 25) ──
        conf_factor = ConfidenceAdjuster.calculate_confidence_factor(
            verification_confidence=acc_res.verification_score,
            data_quality_score=acc_res.quality_score,
            freshness_score=fresh_res.overall_freshness,
        )
        final_score = ConfidenceAdjuster.adjust_score(raw_score, conf_factor)

        # ── 5. STATUS DETERMINATION & WORKFLOW STATES (Section 53, 54) ──
        all_reasons = list(set(
            acc_res.reason_codes
            + per_res.reason_codes
            + sig_res.reason_codes
            + tim_res.reason_codes
            + contact_res.reason_codes
            + fresh_res.reason_codes
        ))

        # Check REVERIFY: High potential / high fit but stale critical data
        if (acc_res.icp_fit >= 0.70 or final_score >= 0.65) and (fresh_res.is_stale_employment or fresh_res.is_stale_company):
            status = RankingStatus.REVERIFY.value
        # Check RESEARCH_MORE: Promising but insufficient intelligence
        elif acc_res.quality_score < profile.min_data_research_more or (raw_score >= 0.60 and conf_factor < 0.50):
            status = RankingStatus.RESEARCH_MORE.value
            all_reasons.append(RankingReasonCode.INSUFFICIENT_DATA.value)
        # Standard threshold banding
        elif final_score >= profile.priority_threshold:
            status = RankingStatus.PRIORITY.value
        elif final_score >= profile.strong_threshold:
            status = RankingStatus.STRONG.value
        elif final_score >= profile.possible_threshold:
            status = RankingStatus.POSSIBLE.value
        else:
            status = RankingStatus.POSSIBLE.value

        # ── 6. EXPLANATION & IDEMPOTENCY ──
        fp = self._compute_fingerprint(company_id, person_id, icp_version_id, ranking_profile_id, company_data)
        exp_data = self.explainer.explain(
            score_id=score_id,
            prospect_name=prospect_name,
            final_score=final_score,
            raw_score=raw_score,
            confidence_factor=conf_factor,
            status=status,
            reason_codes=all_reasons,
            account_contrib=acc_contrib,
            person_contrib=per_contrib,
            signal_contrib=sig_contrib,
            timing_contrib=tim_contrib,
            contact_contrib=con_contrib,
            penalty_deduction=total_penalties,
        )

        score_entity = ProspectScoreEntity(
            id=score_id,
            prospect_id=prospect_id,
            company_id=company_id,
            person_id=person_id,
            icp_version_id=icp_version_id,
            ranking_profile_id=ranking_profile_id,
            account_score=acc_res.score,
            person_score=per_res.score,
            signal_score=sig_res.score,
            timing_score=tim_res.score,
            quality_score=acc_res.quality_score,
            verification_score=acc_res.verification_score,
            contactability_score=contact_res.score,
            penalty_score=normalize_score(total_penalties),
            raw_score=raw_score,
            confidence_factor=conf_factor,
            final_score=final_score,
            status=status,
            calculated_at=utc_iso_now(),
            fingerprint=fp,
            metadata_json={"narrative": exp_data["narrative"], "reason_codes": all_reasons},
        )

        return score_entity, exp_data["entities"]

    def rank_batch(
        self,
        prospect_candidates: List[Dict[str, Any]],
        profile_config: Optional[RankingProfileConfig] = None,
        ranking_profile_id: str = "default_v1",
    ) -> List[Tuple[ProspectScoreEntity, List[RankingExplanationEntity]]]:
        """Evaluates a batch of candidates and assigns sorted rank positions."""
        scored_pairs: List[Tuple[ProspectScoreEntity, List[RankingExplanationEntity]]] = []
        for cand in prospect_candidates:
            res_score, res_exps = self.rank_prospect(
                prospect_id=cand.get("prospect_id", generate_id("prsp_")),
                company_data=cand.get("company_data", {}),
                person_data=cand.get("person_data"),
                signals=cand.get("signals"),
                icp_score=cand.get("icp_score"),
                icp_version_id=cand.get("icp_version_id"),
                profile_config=profile_config,
                ranking_profile_id=ranking_profile_id,
                is_competitor=cand.get("is_competitor", False),
                is_hard_excluded=cand.get("is_hard_excluded", False),
                quality_gate_blocked=cand.get("quality_gate_blocked", False),
            )
            scored_pairs.append((res_score, res_exps))

        # Sort descending by final score, secondary by raw score
        scored_pairs.sort(key=lambda pair: (pair[0].final_score, pair[0].raw_score), reverse=True)

        # Assign rank positions
        for pos, (score_ent, _) in enumerate(scored_pairs, start=1):
            score_ent.rank_position = pos

        return scored_pairs

    def _compute_fingerprint(
        self,
        company_id: str,
        person_id: Optional[str],
        icp_version_id: Optional[str],
        profile_id: str,
        company_data: Dict[str, Any],
    ) -> str:
        """Generates SHA-256 fingerprint for idempotency caching (Section 62, 63)."""
        h = hashlib.sha256()
        h.update(f"{company_id}:{person_id or ''}:{icp_version_id or ''}:{profile_id}".encode())
        for k in sorted(company_data.keys()):
            h.update(f"{k}:{company_data[k]}".encode())
        return h.hexdigest()
