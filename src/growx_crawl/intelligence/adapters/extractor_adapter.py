import logging
from typing import Any, Dict, List, Optional

from growx_crawl.identity import identity_service
from growx_crawl.intelligence.evidence.service import evidence_service
from growx_crawl.intelligence.facts.service import fact_service
from growx_crawl.intelligence.observations.service import observation_service

logger = logging.getLogger("growx_crawl.intelligence.adapters.extractor_adapter")


class ExtractorAdapter:
    """
    Adapter bridging existing raw web crawler extraction outputs into the Phase 04
    canonical Observation -> Evidence -> Fact intelligence flow without requiring
    full crawler or extractor rewrites (Section 77).
    """

    def __init__(self):
        self.obs_service = observation_service
        self.evi_service = evidence_service
        self.fact_service = fact_service
        self.ident_service = identity_service

    def ingest_extraction_result(
        self,
        domain: str,
        company_name: str,
        analysis_dict: Dict[str, Any],
        source_url: Optional[str] = None,
        source_id: Optional[str] = None,
        object_ref_id: Optional[str] = None,
        extractor_name: str = "web_company_extractor",
        extractor_version: str = "v1.0",
        source_authority_class: str = "first_party",
        scope_type: str = "global",
        scope_id: str = "global",
    ) -> List[Any]:
        """
        Takes raw extraction results, resolves canonical identity, ingests observations,
        attaches evidence, and proposes canonical facts.
        """
        # Step 1: Canonical Entity Identity (Phase 03)
        comp = self.ident_service.get_or_create_company(
            name=company_name or domain,
            domain=domain,
            source_id=source_id,
        )

        facts_produced = []

        # Mapping of extraction keys to canonical predicates
        predicate_mapping = [
            ("summary", "company.description"),
            ("primary_offer", "company.description"),
            ("industry", "company.industry"),
            ("employee_count", "company.employee_count"),
            ("employee_range", "company.employee_range"),
            ("revenue_range", "company.revenue_range"),
            ("phone", "company.phone"),
            ("email", "company.email"),
        ]

        # Multi-value list keys
        list_predicates = [
            ("tech_stack", "company.technology"),
            ("features", "company.product"),
            ("services", "company.service"),
        ]

        # Process scalar predicates
        for key, pred in predicate_mapping:
            val = analysis_dict.get(key)
            if val:
                obs, rej = self.obs_service.record_observation(
                    subject_type="company",
                    subject_id=comp.id,
                    predicate=pred,
                    raw_value=val,
                    source_id=source_id,
                    object_ref_id=object_ref_id,
                    extractor_name=extractor_name,
                    extractor_version=extractor_version,
                )
                if obs:
                    # Attach evidence
                    self.evi_service.attach_evidence(
                        observation_id=obs.id,
                        evidence_type="html_fragment",
                        source_id=source_id,
                        object_ref_id=object_ref_id,
                        source_url=source_url or f"https://{domain}",
                        quoted_text=str(val)[:200],
                    )
                    # Propose fact
                    fact = self.fact_service.propose_fact(
                        observation=obs,
                        source_authority_class=source_authority_class,
                        scope_type=scope_type,
                        scope_id=scope_id,
                    )
                    facts_produced.append(fact)

        # Process multi-value predicates
        for list_key, pred in list_predicates:
            items = analysis_dict.get(list_key, [])
            if isinstance(items, list):
                for item in items:
                    if not item:
                        continue
                    obs, _ = self.obs_service.record_observation(
                        subject_type="company",
                        subject_id=comp.id,
                        predicate=pred,
                        raw_value=item,
                        source_id=source_id,
                        object_ref_id=object_ref_id,
                        extractor_name=extractor_name,
                        extractor_version=extractor_version,
                    )
                    if obs:
                        self.evi_service.attach_evidence(
                            observation_id=obs.id,
                            evidence_type="structured_metadata",
                            source_id=source_id,
                            object_ref_id=object_ref_id,
                            source_url=source_url or f"https://{domain}",
                            quoted_text=str(item),
                        )
                        fact = self.fact_service.propose_fact(
                            observation=obs,
                            source_authority_class=source_authority_class,
                            scope_type=scope_type,
                            scope_id=scope_id,
                        )
                        facts_produced.append(fact)

        logger.info("Ingested %d canonical facts for company %s (%s)", len(facts_produced), comp.id, comp.canonical_name)
        return facts_produced


extractor_adapter = ExtractorAdapter()
