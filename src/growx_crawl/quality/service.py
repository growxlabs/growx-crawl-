"""
GrowX Data Quality Service Facade.
Provides the primary high-level API for evaluating records across all 5 quality gates,
persisting evaluation state and audit results, emitting quality telemetry, and routing
quarantine records.
"""

from typing import Any, Dict, List, Optional
from growx_crawl.quality.actions import map_reasons_to_actions
from growx_crawl.quality.gates import (
    CanonicalIngestionGate,
    IntelligenceTrustGate,
    OutreachEligibilityGate,
    PersonalizationGate,
    ProspectEligibilityGate,
)
from growx_crawl.quality.metrics import quality_events, quality_metrics
from growx_crawl.quality.models import (
    GateType,
    ProspectQualitySnapshot,
    QualityDecision,
    QualityResultEntity,
    QualityStateEntity,
    QualityStatus,
    QuarantineEntity,
)
from growx_crawl.quality.quarantine import quarantine_manager
from growx_crawl.quality.repository import QualityRepository, SqliteQualityRepository
from growx_crawl.shared.ids import generate_id
from growx_crawl.shared.time import utc_iso_now


class DataQualityService:
    """The authoritative quality evaluation service for GrowX Crawl & AutoGTM."""

    def __init__(self, repository: Optional[QualityRepository] = None):
        self.repository = repository or SqliteQualityRepository()

    def evaluate(
        self,
        subject_type: str,
        subject_id: str,
        gate_type: GateType,
        profile: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        policy_name: Optional[str] = None,
        **kwargs: Any,
    ) -> QualityDecision:
        """Evaluate a subject record against a specific quality gate."""
        payload = dict(data or {})
        if "subject_type" not in payload:
            payload["subject_type"] = subject_type
        if "subject_id" not in payload:
            payload["subject_id"] = subject_id
        if "id" not in payload:
            payload["id"] = subject_id

        # 1. Gate Execution
        if gate_type == GateType.CANONICAL_INGESTION:
            decision = CanonicalIngestionGate.evaluate(
                payload, policy_name=policy_name or "canonical_ingestion_v1"
            )
        elif gate_type == GateType.INTELLIGENCE_TRUST:
            decision = IntelligenceTrustGate.evaluate(
                payload, policy_name=policy_name or "intelligence_trust_v1"
            )
        elif gate_type == GateType.PROSPECT_ELIGIBILITY:
            existing_ids = kwargs.get("existing_prospect_ids")
            decision = ProspectEligibilityGate.evaluate(
                payload,
                policy_name=policy_name or "prospect_eligibility_v1",
                existing_prospect_ids=existing_ids,
            )
        elif gate_type == GateType.PERSONALIZATION_ELIGIBILITY:
            decision = PersonalizationGate.evaluate(
                payload, policy_name=policy_name or "personalization_v1"
            )
        elif gate_type == GateType.OUTREACH_ELIGIBILITY:
            suppressed = kwargs.get("suppressed_emails")
            decision = OutreachEligibilityGate.evaluate(
                payload,
                policy_name=policy_name or "outreach_v1",
                suppressed_emails=suppressed,
            )
        else:
            raise ValueError(f"Unknown gate type: {gate_type}")

        # 2. Record metrics and telemetry
        quality_metrics.record_decision(gate_type, decision)
        quality_events.emit(
            event_name="quality_evaluated",
            subject_type=subject_type,
            subject_id=subject_id,
            gate=gate_type.value,
            status=decision.status.value,
            score=decision.score,
        )

        # 3. Persist audit result and state
        res_id = generate_id("qres_")
        result_entity = QualityResultEntity(
            id=res_id,
            subject_type=subject_type,
            subject_id=subject_id,
            gate_type=gate_type,
            profile=profile or "default",
            status=decision.status,
            score=decision.score,
            policy_id=decision.policy_id,
            policy_version=decision.policy_version,
            evaluated_at=utc_iso_now(),
            valid_until=decision.valid_until,
            reasons=decision.reasons,
            required_actions=decision.required_actions,
            metadata_json=decision.details_json,
        )
        self.repository.save_result(result_entity, decision.rule_results)

        state_entity = QualityStateEntity(
            subject_type=subject_type,
            subject_id=subject_id,
            gate_type=gate_type,
            latest_result_id=res_id,
            status=decision.status,
            score=decision.score,
            valid_until=decision.valid_until,
            updated_at=utc_iso_now(),
        )
        self.repository.save_state(state_entity)

        # 4. Handle Quarantine if applicable
        if decision.status == QualityStatus.QUARANTINE:
            self.quarantine_item(
                subject_type=subject_type,
                payload=payload,
                reasons=decision.reasons,
                source_id=subject_id,
                metadata={"gate": gate_type.value, "score": decision.score},
            )

        return decision

    def evaluate_company(
        self,
        company_id: str,
        gate_type: GateType,
        company_data: Optional[Dict[str, Any]] = None,
        profile: Optional[str] = None,
        **kwargs: Any,
    ) -> QualityDecision:
        """Evaluate a company entity against a specific quality gate."""
        return self.evaluate(
            subject_type="company",
            subject_id=company_id,
            gate_type=gate_type,
            profile=profile,
            data=company_data,
            **kwargs,
        )

    def evaluate_person(
        self,
        person_id: str,
        gate_type: GateType,
        person_data: Optional[Dict[str, Any]] = None,
        profile: Optional[str] = None,
        **kwargs: Any,
    ) -> QualityDecision:
        """Evaluate a person entity against a specific quality gate."""
        return self.evaluate(
            subject_type="person",
            subject_id=person_id,
            gate_type=gate_type,
            profile=profile,
            data=person_data,
            **kwargs,
        )

    def evaluate_prospect(
        self,
        prospect_id: str,
        gate_type: GateType,
        prospect_data: Optional[Dict[str, Any]] = None,
        profile: Optional[str] = None,
        **kwargs: Any,
    ) -> QualityDecision:
        """Evaluate a prospect record against a specific quality gate."""
        return self.evaluate(
            subject_type="prospect",
            subject_id=prospect_id,
            gate_type=gate_type,
            profile=profile,
            data=prospect_data,
            **kwargs,
        )

    def evaluate_prospect_bundle(
        self,
        prospect_data: Dict[str, Any],
        existing_prospect_ids: Optional[List[str]] = None,
        suppressed_emails: Optional[List[str]] = None,
    ) -> ProspectQualitySnapshot:
        """
        Comprehensive multi-dimensional evaluation for a full prospect bundle.
        Evaluates company, person, employment, email, personalization, and outreach eligibility.
        """
        p_id = str(prospect_data.get("id") or prospect_data.get("prospect_id") or generate_id("prsp_"))

        # 1. Evaluate Prospect Eligibility
        prospect_dec = self.evaluate(
            subject_type="prospect",
            subject_id=p_id,
            gate_type=GateType.PROSPECT_ELIGIBILITY,
            data=prospect_data,
            existing_prospect_ids=existing_prospect_ids,
        )

        # 2. Evaluate Personalization Eligibility
        pers_dec = self.evaluate(
            subject_type="prospect",
            subject_id=p_id,
            gate_type=GateType.PERSONALIZATION_ELIGIBILITY,
            data=prospect_data,
        )

        # 3. Evaluate Outreach Eligibility
        outreach_dec = self.evaluate(
            subject_type="prospect",
            subject_id=p_id,
            gate_type=GateType.OUTREACH_ELIGIBILITY,
            data=prospect_data,
            suppressed_emails=suppressed_emails,
        )

        # Breakdown scores
        comp_score = prospect_dec.score
        person_score = 0.90 if prospect_data.get("name") or prospect_data.get("lead_name") else 0.40
        emp_score = 0.90 if prospect_data.get("employment_status") in (None, "verified", "active") else 0.30
        email_score = 0.95 if prospect_data.get("email_verification_status") in ("verified", "valid") or prospect_data.get("email_status") in ("verified", "valid") else 0.40
        pers_score = pers_dec.score
        outreach_score = outreach_dec.score

        # Combine reasons & actions
        combined_reasons: List[str] = []
        combined_reasons.extend(prospect_dec.reasons)
        combined_reasons.extend(pers_dec.reasons)
        combined_reasons.extend(outreach_dec.reasons)
        # Deduplicate preserving order
        unique_reasons = list(dict.fromkeys(combined_reasons))
        # Determine overall status
        if (
            outreach_dec.status == QualityStatus.BLOCKED
            or prospect_dec.status == QualityStatus.BLOCKED
            or pers_dec.status == QualityStatus.BLOCKED
        ):
            overall_status = QualityStatus.BLOCKED
        elif (
            outreach_dec.status == QualityStatus.REVERIFY
            or prospect_dec.status == QualityStatus.REVERIFY
            or pers_dec.status == QualityStatus.REVERIFY
        ):
            overall_status = QualityStatus.REVERIFY
        elif (
            outreach_dec.status == QualityStatus.LIMITED
            or prospect_dec.status == QualityStatus.LIMITED
            or pers_dec.status == QualityStatus.LIMITED
        ):
            overall_status = QualityStatus.LIMITED
        else:
            overall_status = QualityStatus.PASS

        actions = [] if overall_status == QualityStatus.PASS else map_reasons_to_actions(unique_reasons)

        snapshot = ProspectQualitySnapshot(
            prospect_id=p_id,
            company_score=comp_score,
            person_score=person_score,
            employment_score=emp_score,
            email_score=email_score,
            personalization_score=pers_score,
            outreach_score=outreach_score,
            overall_status=overall_status,
            reasons=unique_reasons,
            required_actions=actions,
            evaluated_at=utc_iso_now(),
        )

        self.repository.save_prospect_snapshot(snapshot)
        return snapshot

    def evaluate_batch(
        self,
        items: List[Dict[str, Any]],
        gate_type: GateType,
        subject_type: str = "prospect",
        profile: Optional[str] = None,
        **kwargs: Any,
    ) -> List[QualityDecision]:
        """Batch evaluate multiple items against a quality gate."""
        results: List[QualityDecision] = []
        for item in items:
            s_id = str(item.get("id") or item.get("subject_id") or generate_id("item_"))
            dec = self.evaluate(
                subject_type=subject_type,
                subject_id=s_id,
                gate_type=gate_type,
                profile=profile,
                data=item,
                **kwargs,
            )
            results.append(dec)
        return results

    def get_current(
        self, subject_type: str, subject_id: str, gate_type: GateType
    ) -> Optional[QualityStateEntity]:
        """Retrieve current cached quality state for a subject and gate."""
        return self.repository.get_state(subject_type, subject_id, gate_type)

    def quarantine_item(
        self,
        subject_type: str,
        payload: Dict[str, Any],
        reasons: List[str],
        source_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> QuarantineEntity:
        """Create and persist a quarantine record for malformed or conflicting data."""
        entity = quarantine_manager.create_quarantine_record(
            subject_type=subject_type,
            payload=payload,
            reasons=reasons,
            source_id=source_id,
            metadata=metadata,
        )
        self.repository.save_quarantine(entity)
        quality_events.emit(
            event_name="item_quarantined",
            subject_type=subject_type,
            subject_id=source_id or entity.id,
            gate="quarantine",
            status="quarantined",
            score=0.0,
        )
        return entity

    def list_quarantined(self, status: Optional[str] = None) -> List[QuarantineEntity]:
        """List quarantine records, optionally filtered by status."""
        return self.repository.list_quarantine(status)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Retrieve live metrics summary for all quality gate operations."""
        return quality_metrics.get_summary()


# Default singleton instance
quality_service = DataQualityService()
