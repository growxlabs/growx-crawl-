from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, List, Optional

from growx_crawl.identity.ids import generate_identity_id
from growx_crawl.intelligence.evidence.repository import BaseEvidenceRepository, SqliteEvidenceRepository
from growx_crawl.intelligence.facts.confidence import compute_fact_confidence
from growx_crawl.intelligence.facts.conflicts import create_fact_conflict
from growx_crawl.intelligence.facts.models import (
    FactConflictEntity,
    FactEntity,
    FactEventEntity,
    FactEvidenceEntity,
    FactValueEntity,
)
from growx_crawl.intelligence.facts.predicates import predicate_registry
from growx_crawl.intelligence.facts.repository import BaseFactRepository, SqliteFactRepository
from growx_crawl.intelligence.facts.selectors import evaluate_fact_transition, values_are_equal
from growx_crawl.intelligence.observations.models import ObservationEntity
from growx_crawl.intelligence.observations.repository import BaseObservationRepository, SqliteObservationRepository

logger = logging.getLogger("growx_crawl.intelligence.facts.service")


class FactService:
    """
    Primary intelligence boundary service turning observations and evidence
    into verified, provenance-backed canonical facts while preserving historical values.
    """

    def __init__(
        self,
        fact_repo: Optional[BaseFactRepository] = None,
        obs_repo: Optional[BaseObservationRepository] = None,
        evidence_repo: Optional[BaseEvidenceRepository] = None,
    ):
        self.fact_repo = fact_repo or SqliteFactRepository()
        self.obs_repo = obs_repo or SqliteObservationRepository()
        self.evidence_repo = evidence_repo or SqliteEvidenceRepository()

    def propose_fact(
        self,
        observation: ObservationEntity,
        source_authority_class: str = "first_party",
        scope_type: str = "global",
        scope_id: str = "global",
        actor_type: str = "system",
        actor_id: Optional[str] = None,
    ) -> FactEntity:
        """
        Processes an observation through the fact proposal pipeline:
        evaluates same-value, multi-value coexistence, superseding, or conflict.
        Preserves historical values without destructive overwrites.
        """
        pred_def = predicate_registry.get(observation.predicate)
        if not pred_def:
            raise ValueError(f"Unknown predicate '{observation.predicate}' cannot be proposed as a fact.")

        now_iso = datetime.now(timezone.utc).isoformat()
        existing_fact = self.fact_repo.find_current(
            subject_type=observation.subject_type,
            subject_id=observation.subject_id,
            predicate=observation.predicate,
            scope_type=scope_type,
            scope_id=scope_id,
        )

        action = evaluate_fact_transition(
            existing_fact=existing_fact,
            new_obs=observation,
            predicate_def=pred_def,
            source_authority_class=source_authority_class,
        )

        logger.info(
            "Evaluating fact transition for %s:%s predicate '%s' -> Action: %s",
            observation.subject_type,
            observation.subject_id,
            observation.predicate,
            action,
        )

        if action == "create":
            # Initial fact creation
            fact_id = generate_identity_id("fct_")
            confidence = compute_fact_confidence(
                authority_class=source_authority_class,
                extractor_confidence=observation.confidence,
                num_independent_sources=1,
            )
            fact = FactEntity(
                id=fact_id,
                subject_type=observation.subject_type,
                subject_id=observation.subject_id,
                predicate=observation.predicate,
                value_type=pred_def.value_type,
                current_value_json=observation.normalized_value_json,
                status="accepted",
                confidence=confidence,
                verification_state="source_supported",
                first_seen_at=observation.observed_at,
                last_seen_at=observation.observed_at,
                valid_from=observation.observed_at,
                scope_type=scope_type,
                scope_id=scope_id,
            )
            saved_fact = self.fact_repo.create(fact)

            # Record initial fact history value
            val_id = generate_identity_id("fvl_")
            val = FactValueEntity(
                id=val_id,
                fact_id=saved_fact.id,
                value_json=observation.normalized_value_json,
                value_type=pred_def.value_type,
                confidence=confidence,
                status="accepted",
                valid_from=observation.observed_at,
                first_seen_at=observation.observed_at,
                last_seen_at=observation.observed_at,
            )
            self.fact_repo.add_value(val)

            # Link supporting observation
            self.fact_repo.link_evidence(
                FactEvidenceEntity(
                    fact_id=saved_fact.id,
                    observation_id=observation.id,
                    support_type="supports",
                    weight=1.0,
                )
            )

            # Audit event
            self._emit_event(saved_fact.id, "fact_created", {"value": observation.normalized_value_json}, actor_type, actor_id)
            return saved_fact

        elif action == "same_value":
            assert existing_fact is not None
            # Update timestamps & strengthen confidence (Section 50)
            existing_fact.last_seen_at = observation.observed_at
            existing_fact.updated_at = now_iso

            # Count distinct supporting observations
            current_evidence = self.fact_repo.list_evidence(existing_fact.id)
            sources_count = len(current_evidence) + 1
            computed_conf = compute_fact_confidence(
                authority_class=source_authority_class,
                extractor_confidence=observation.confidence,
                num_independent_sources=sources_count,
            )
            # Monotonically strengthen confidence upon independent corroboration
            boost = 0.04
            existing_fact.confidence = min(max(existing_fact.confidence + boost, computed_conf), 0.99)
            if sources_count >= 2:
                existing_fact.verification_state = "multi_source_supported"

            updated_fact = self.fact_repo.update(existing_fact)

            # Link observation in evidence
            self.fact_repo.link_evidence(
                FactEvidenceEntity(
                    fact_id=existing_fact.id,
                    observation_id=observation.id,
                    support_type="supports",
                    weight=1.0,
                )
            )

            # Update latest history record last_seen
            history = self.fact_repo.list_history(existing_fact.id)
            if history:
                latest_val = history[0]
                latest_val.last_seen_at = observation.observed_at
                self.fact_repo.update_value(latest_val)

            self._emit_event(existing_fact.id, "fact_updated", {"action": "same_value_strengthened"}, actor_type, actor_id)
            return updated_fact

        elif action == "coexist":
            assert existing_fact is not None
            # Multi-value predicate: add new value to history and link evidence
            val_id = generate_identity_id("fvl_")
            val = FactValueEntity(
                id=val_id,
                fact_id=existing_fact.id,
                value_json=observation.normalized_value_json,
                value_type=pred_def.value_type,
                confidence=observation.confidence,
                status="accepted",
                valid_from=observation.observed_at,
                first_seen_at=observation.observed_at,
                last_seen_at=observation.observed_at,
            )
            self.fact_repo.add_value(val)
            self.fact_repo.link_evidence(
                FactEvidenceEntity(
                    fact_id=existing_fact.id,
                    observation_id=observation.id,
                    support_type="supports",
                    weight=1.0,
                )
            )
            existing_fact.last_seen_at = observation.observed_at
            existing_fact.updated_at = now_iso

            # Maintain list of all active values in current_value_json
            history = self.fact_repo.list_history(existing_fact.id)
            active_vals = []
            for h in history:
                if h.status == "accepted":
                    v = h.value_json.get("value") or h.value_json
                    if v and v not in active_vals:
                        active_vals.append(v)

            existing_fact.current_value_json = {
                "value": observation.normalized_value_json.get("value"),
                "values": active_vals,
            }
            updated_fact = self.fact_repo.update(existing_fact)
            self._emit_event(existing_fact.id, "fact_updated", {"action": "multi_value_coexist", "new_value": observation.normalized_value_json}, actor_type, actor_id)
            return updated_fact

        elif action == "supersede":
            assert existing_fact is not None
            # Historical Preservation: expire old value
            history = self.fact_repo.list_history(existing_fact.id)
            if history:
                old_val = history[0]
                old_val.valid_to = observation.observed_at
                old_val.status = "superseded"
                self.fact_repo.update_value(old_val)

            # Add new value
            val_id = generate_identity_id("fvl_")
            new_val = FactValueEntity(
                id=val_id,
                fact_id=existing_fact.id,
                value_json=observation.normalized_value_json,
                value_type=pred_def.value_type,
                confidence=observation.confidence,
                status="accepted",
                valid_from=observation.observed_at,
                first_seen_at=observation.observed_at,
                last_seen_at=observation.observed_at,
            )
            self.fact_repo.add_value(new_val)

            # Update current fact
            existing_fact.current_value_json = observation.normalized_value_json
            existing_fact.valid_from = observation.observed_at
            existing_fact.last_seen_at = observation.observed_at
            existing_fact.updated_at = now_iso
            existing_fact.confidence = compute_fact_confidence(
                authority_class=source_authority_class,
                extractor_confidence=observation.confidence,
                num_independent_sources=1,
            )
            updated_fact = self.fact_repo.update(existing_fact)

            self.fact_repo.link_evidence(
                FactEvidenceEntity(
                    fact_id=existing_fact.id,
                    observation_id=observation.id,
                    support_type="supersedes",
                    weight=1.0,
                )
            )
            self._emit_event(existing_fact.id, "fact_superseded", {"new_value": observation.normalized_value_json}, actor_type, actor_id)
            return updated_fact

        elif action == "conflict":
            assert existing_fact is not None
            # Conflicting value detected (Sections 29-31)
            existing_fact.status = "conflicting"
            existing_fact.verification_state = "disputed"
            existing_fact.updated_at = now_iso
            updated_fact = self.fact_repo.update(existing_fact)

            # Preserve the conflicting value in history
            val_id = generate_identity_id("fvl_")
            conflict_val = FactValueEntity(
                id=val_id,
                fact_id=existing_fact.id,
                value_json=observation.normalized_value_json,
                value_type=pred_def.value_type,
                confidence=observation.confidence,
                status="conflicting",
                valid_from=observation.observed_at,
                first_seen_at=observation.observed_at,
                last_seen_at=observation.observed_at,
            )
            self.fact_repo.add_value(conflict_val)

            # Open conflict tracking record
            conflict = create_fact_conflict(
                subject_type=observation.subject_type,
                subject_id=observation.subject_id,
                predicate=observation.predicate,
                status="open",
                metadata={
                    "current_fact_value": existing_fact.current_value_json,
                    "conflicting_value": observation.normalized_value_json,
                    "observation_id": observation.id,
                },
            )
            self.fact_repo.create_conflict(conflict)

            self.fact_repo.link_evidence(
                FactEvidenceEntity(
                    fact_id=existing_fact.id,
                    observation_id=observation.id,
                    support_type="contradicts",
                    weight=1.0,
                )
            )
            self._emit_event(existing_fact.id, "fact_conflict_opened", {"conflicting_value": observation.normalized_value_json}, actor_type, actor_id)
            return updated_fact

        raise RuntimeError(f"Unhandled transition action: {action}")

    def get_current(
        self,
        subject_type: str,
        subject_id: str,
        predicate: str,
        scope_type: str = "global",
        scope_id: str = "global",
    ) -> Optional[FactEntity]:
        return self.fact_repo.find_current(subject_type, subject_id, predicate, scope_type, scope_id)

    def list_current(
        self,
        subject_type: str,
        subject_id: str,
        scope_type: str = "global",
        scope_id: str = "global",
    ) -> List[FactEntity]:
        return self.fact_repo.list_current(subject_type, subject_id, scope_type, scope_id)

    def get_history(self, fact_id: str) -> List[FactValueEntity]:
        return self.fact_repo.list_history(fact_id)

    def list_conflicts(
        self,
        subject_type: Optional[str] = None,
        subject_id: Optional[str] = None,
        status: str = "open",
    ) -> List[FactConflictEntity]:
        return self.fact_repo.list_conflicts(subject_type, subject_id, status)

    def resolve_conflict(
        self,
        conflict_id: str,
        resolution_method: str,
        selected_fact_value_id: Optional[str] = None,
    ) -> Optional[FactConflictEntity]:
        return self.fact_repo.resolve_conflict(conflict_id, resolution_method, selected_fact_value_id)

    def calculate_quality_metrics(self) -> Dict[str, float]:
        """
        Calculates intelligence health metrics per Section 71.
        """
        total_facts = self.fact_repo.count()
        total_obs = self.obs_repo.count()
        total_rejections = self.obs_repo.count_rejections()

        if total_facts == 0:
            return {
                "facts_with_evidence_rate": 1.0,
                "conflicting_fact_rate": 0.0,
                "quarantine_rejection_rate": 0.0,
                "total_facts": 0,
                "total_observations": total_obs,
            }

        conflicts = len(self.fact_repo.list_conflicts(status="open"))
        return {
            "facts_with_evidence_rate": 1.0,  # Enforced by propose_fact
            "conflicting_fact_rate": round(conflicts / total_facts, 4),
            "quarantine_rejection_rate": round(total_rejections / (total_obs + total_rejections) if (total_obs + total_rejections) > 0 else 0.0, 4),
            "total_facts": total_facts,
            "total_observations": total_obs,
            "total_rejections": total_rejections,
        }

    def _emit_event(
        self,
        fact_id: str,
        event_type: str,
        payload: Dict[str, Any],
        actor_type: str = "system",
        actor_id: Optional[str] = None,
    ) -> None:
        event = FactEventEntity(
            id=generate_identity_id("fev_"),
            fact_id=fact_id,
            event_type=event_type,
            payload_json=payload,
            actor_type=actor_type,
            actor_id=actor_id,
        )
        self.fact_repo.record_event(event)


fact_service = FactService()
