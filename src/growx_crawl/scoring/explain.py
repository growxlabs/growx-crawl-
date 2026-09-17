"""
GrowX Ranking Explainer.
Generates human-readable audit summaries and atomic explanation records with signed component contributions.
"""

from typing import Any, Dict, List, Optional
from growx_crawl.scoring.models import (
    RankingExplanationEntity,
    RankingStatus,
)
from growx_crawl.shared.ids import generate_id


class RankingExplainer:
    """Produces explainable audit packets for prospect ranking decisions."""

    @staticmethod
    def explain(
        score_id: str,
        prospect_name: str,
        final_score: float,
        raw_score: float,
        confidence_factor: float,
        status: str,
        reason_codes: List[str],
        account_contrib: float,
        person_contrib: float,
        signal_contrib: float,
        timing_contrib: float,
        contact_contrib: float,
        penalty_deduction: float,
        evidence_refs: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        refs = evidence_refs or []

        # 1. Build Narrative
        status_label = status.replace("_", " ").title()
        if status == RankingStatus.NOT_ELIGIBLE.value:
            narrative = f"{prospect_name} is disqualified from targeting: {', '.join(reason_codes)}."
        elif status == RankingStatus.REVERIFY.value:
            narrative = f"{prospect_name} has high targeting fit but critical data requires reverification before outreach."
        elif status == RankingStatus.RESEARCH_MORE.value:
            narrative = f"{prospect_name} has high potential but requires deeper enrichment to confirm ICP fit."
        else:
            narrative = (
                f"{prospect_name} ranked as {status_label} (Priority: {final_score:.2f}, "
                f"Raw: {raw_score:.2f}, Confidence: {int(confidence_factor * 100)}%)."
            )

        # 2. Build Atomic Contributions List
        contributions: List[Dict[str, Any]] = [
            {"component": "account", "contribution": account_contrib, "direction": "positive", "label": "Account & ICP Fit"},
            {"component": "person", "contribution": person_contrib, "direction": "positive", "label": "Buyer Persona Alignment"},
            {"component": "signal", "contribution": signal_contrib, "direction": "positive", "label": "Detected Event Signals"},
            {"component": "timing", "contribution": timing_contrib, "direction": "positive", "label": "Actionable Timing & Recency"},
            {"component": "contactability", "contribution": contact_contrib, "direction": "positive", "label": "Deliverability & Contactability"},
        ]
        if penalty_deduction > 0:
            contributions.append({
                "component": "penalties",
                "contribution": -penalty_deduction,
                "direction": "negative",
                "label": "Staleness & Mailbox Penalties",
            })

        # 3. Create Persistent Explanation Entities
        explanation_entities: List[RankingExplanationEntity] = []

        # Explicit reason code entities
        for rc in reason_codes:
            is_neg = any(neg in rc for neg in ("BLOCK", "PENALTY", "EXCLUSION", "SUPPRESS", "INVALID", "STALE", "CONFLICT", "MISSING"))
            direction = "negative" if is_neg else "positive"
            comp = "penalty" if is_neg else "fit"
            contrib_val = -1.0 if (is_neg and status == RankingStatus.NOT_ELIGIBLE.value) else (0.10 if not is_neg else -0.05)
            explanation_entities.append(
                RankingExplanationEntity(
                    id=generate_id("rex_"),
                    score_id=score_id,
                    reason_code=rc,
                    component=comp,
                    contribution=contrib_val,
                    direction=direction,
                    evidence_refs=refs,
                )
            )

        # Component contribution entities
        for c in contributions:
            explanation_entities.append(
                RankingExplanationEntity(
                    id=generate_id("rex_"),
                    score_id=score_id,
                    reason_code=f"CONTRIB_{c['component'].upper()}",
                    component=c["component"],
                    contribution=c["contribution"],
                    direction=c["direction"],
                    evidence_refs=refs,
                )
            )

        return {
            "narrative": narrative,
            "final_score": final_score,
            "raw_score": raw_score,
            "confidence_factor": confidence_factor,
            "status": status,
            "reason_codes": reason_codes,
            "contributions": contributions,
            "entities": explanation_entities,
        }
