import hashlib
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from growx_crawl.identity.ids import IDENTITY_PREFIXES, generate_identity_id
from growx_crawl.intelligence.facts.normalizers import normalize_fact_value
from growx_crawl.intelligence.facts.predicates import predicate_registry
from growx_crawl.intelligence.observations.models import ObservationEntity, ObservationRejectionEntity
from growx_crawl.intelligence.observations.repository import BaseObservationRepository, SqliteObservationRepository

logger = logging.getLogger("growx_crawl.intelligence.observations.service")


class ObservationService:
    """
    Ingests and validates raw observations against Predicate Registry,
    enforcing typing, idempotency, and quarantine of malformed records.
    """

    def __init__(self, repo: Optional[BaseObservationRepository] = None):
        self.repo = repo or SqliteObservationRepository()
        self._seen_hashes: set = set()

    def generate_idempotency_hash(
        self,
        subject_id: str,
        predicate: str,
        normalized_value: Dict[str, Any],
        source_id: Optional[str],
        observed_at: str,
    ) -> str:
        payload = f"{subject_id}|{predicate}|{json.dumps(normalized_value, sort_keys=True)}|{source_id or ''}|{observed_at[:13]}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def record_observation(
        self,
        subject_type: str,
        subject_id: str,
        predicate: str,
        raw_value: Any,
        source_id: Optional[str] = None,
        object_ref_id: Optional[str] = None,
        observed_at: Optional[str] = None,
        extractor_name: str = "default_extractor",
        extractor_version: str = "v1.0",
        model_run_id: Optional[str] = None,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[ObservationEntity], Optional[ObservationRejectionEntity]]:
        """
        Validates, normalizes, and persists an observation.
        If validation fails, the payload is quarantined in observation_rejections.
        """
        # Quality Gate 1: Subject ID validation
        if not subject_id or not any(subject_id.startswith(p) for p in IDENTITY_PREFIXES):
            rejection = self._quarantine(
                payload={
                    "subject_type": subject_type,
                    "subject_id": subject_id,
                    "predicate": predicate,
                    "raw_value": raw_value,
                },
                reason_code="missing_subject" if not subject_id else "invalid_entity_ref",
                source_id=source_id,
            )
            return None, rejection

        # Quality Gate 2: Predicate Registry validation
        pred_def = predicate_registry.get(predicate)
        if not pred_def:
            rejection = self._quarantine(
                payload={
                    "subject_type": subject_type,
                    "subject_id": subject_id,
                    "predicate": predicate,
                    "raw_value": raw_value,
                },
                reason_code="unknown_predicate",
                source_id=source_id,
            )
            return None, rejection

        # Quality Gate 3: Value Type Normalization
        is_valid, norm_val, error_reason = normalize_fact_value(pred_def.value_type, raw_value)
        if not is_valid:
            rejection = self._quarantine(
                payload={
                    "subject_type": subject_type,
                    "subject_id": subject_id,
                    "predicate": predicate,
                    "raw_value": raw_value,
                    "expected_type": pred_def.value_type,
                },
                reason_code=error_reason or "normalization_failed",
                source_id=source_id,
            )
            return None, rejection

        # Quality Gate 4: Idempotency check (Section 65)
        now_observed = observed_at or ObservationEntity.model_fields["observed_at"].default_factory()
        idem_hash = self.generate_idempotency_hash(subject_id, predicate, norm_val, source_id, now_observed)
        if idem_hash in self._seen_hashes:
            logger.debug("Skipping duplicate observation with hash %s (idempotency)", idem_hash)
            # Fetch existing or return mock
            existing_obs = ObservationEntity(
                id=generate_identity_id("obs_"),
                subject_type=subject_type,
                subject_id=subject_id,
                predicate=predicate,
                raw_value=str(raw_value) if raw_value is not None else None,
                normalized_value_json=norm_val,
                value_type=pred_def.value_type,
                source_id=source_id,
                object_ref_id=object_ref_id,
                observed_at=now_observed,
                extractor_name=extractor_name,
                extractor_version=extractor_version,
                model_run_id=model_run_id,
                confidence=confidence,
                metadata_json=metadata or {},
            )
            return existing_obs, None

        self._seen_hashes.add(idem_hash)

        obs_id = generate_identity_id("obs_")
        obs = ObservationEntity(
            id=obs_id,
            subject_type=subject_type,
            subject_id=subject_id,
            predicate=predicate,
            raw_value=str(raw_value) if raw_value is not None else None,
            normalized_value_json=norm_val,
            value_type=pred_def.value_type,
            source_id=source_id,
            object_ref_id=object_ref_id,
            observed_at=now_observed,
            extractor_name=extractor_name,
            extractor_version=extractor_version,
            model_run_id=model_run_id,
            confidence=confidence,
            metadata_json=metadata or {},
        )
        saved = self.repo.create(obs)
        return saved, None

    def _quarantine(
        self,
        payload: Dict[str, Any],
        reason_code: str,
        source_id: Optional[str] = None,
    ) -> ObservationRejectionEntity:
        rej_id = generate_identity_id("rej_")
        rej = ObservationRejectionEntity(
            id=rej_id,
            payload_json=payload,
            reason_code=reason_code,
            source_id=source_id,
        )
        logger.warning("Observation quarantined: %s (reason: %s)", rej_id, reason_code)
        return self.repo.quarantine(rej)


observation_service = ObservationService()
