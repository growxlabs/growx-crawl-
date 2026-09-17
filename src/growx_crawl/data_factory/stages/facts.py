"""
GrowX Data Factory Stage 5: Fact Ingestion & Evidence Linking.
Transforms resolved observations into canonical facts with attached source evidence.
Ensures identical values do not duplicate facts and update freshness instead.
"""

from typing import Any, Dict, List, Optional
from growx_crawl.data_factory.metrics import DataFactoryMetrics
from growx_crawl.intelligence.facts.service import FactService, fact_service
from growx_crawl.intelligence.observations.service import ObservationService, observation_service


class FactsStage:
    """Ingests source-backed facts and updates canonical intelligence graph."""

    def __init__(
        self,
        service: Optional[FactService] = None,
        obs_service: Optional[ObservationService] = None,
    ):
        self.fact_service = service or fact_service
        self.obs_service = obs_service or observation_service

    def execute(
        self,
        resolved_items: List[Dict[str, Any]],
        metrics: DataFactoryMetrics,
    ) -> List[Dict[str, Any]]:
        """Processes resolved observations into verified facts."""
        facts_output: List[Dict[str, Any]] = []

        for item in resolved_items:
            cid = item.get("canonical_company_id")
            obs = item.get("observation", {})
            domain = item.get("domain", "")
            src_url = obs.get("source_url", f"https://{domain}")

            created_facts = []

            # 1. Business description fact
            desc = obs.get("description")
            if desc and cid:
                try:
                    obs_rec, rej = self.obs_service.record_observation(
                        subject_type="company",
                        subject_id=cid,
                        predicate="company.description",
                        raw_value=desc,
                        source_id=src_url,
                        confidence=0.85,
                    )
                    if obs_rec:
                        fact = self.fact_service.propose_fact(obs_rec, source_authority_class="first_party")
                        created_facts.append(fact)
                        metrics.facts_produced += 1
                    elif rej:
                        metrics.quarantined += 1
                except Exception:
                    pass

            # 2. Contact email fact
            for email in obs.get("emails", [])[:2]:
                if cid and email:
                    try:
                        obs_rec, rej = self.obs_service.record_observation(
                            subject_type="company",
                            subject_id=cid,
                            predicate="company.email",
                            raw_value=email,
                            source_id=src_url,
                            confidence=0.90,
                        )
                        if obs_rec:
                            fact = self.fact_service.propose_fact(obs_rec, source_authority_class="first_party")
                            created_facts.append(fact)
                            metrics.facts_produced += 1
                        elif rej:
                            metrics.quarantined += 1
                    except Exception:
                        pass

            # 3. Contact phone fact
            for phone in obs.get("phones", [])[:1]:
                if cid and phone:
                    try:
                        obs_rec, rej = self.obs_service.record_observation(
                            subject_type="company",
                            subject_id=cid,
                            predicate="company.phone",
                            raw_value=phone,
                            source_id=src_url,
                            confidence=0.80,
                        )
                        if obs_rec:
                            fact = self.fact_service.propose_fact(obs_rec, source_authority_class="first_party")
                            created_facts.append(fact)
                            metrics.facts_produced += 1
                        elif rej:
                            metrics.quarantined += 1
                    except Exception:
                        pass

            facts_output.append({
                "canonical_company_id": cid,
                "company_name": item.get("company_name", domain),
                "domain": domain,
                "facts": created_facts,
                "observation": obs,
            })

        return facts_output
