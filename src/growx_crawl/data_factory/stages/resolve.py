"""
GrowX Data Factory Stage 4: Identity & Entity Resolution.
Resolves extracted observations to durable canonical company and domain identities.
Applies EntityResolutionService to avoid creating duplicates or merging ambiguous candidates.
"""

from typing import Any, Dict, List, Optional
from growx_crawl.data_factory.metrics import DataFactoryMetrics
from growx_crawl.entity_resolution import entity_resolution_service
from growx_crawl.identity import identity_service


class ResolveStage:
    """Executes deterministic identity matching and fuzzy entity resolution."""

    def __init__(self, id_service=None, er_service=None):
        self.identity_service = id_service or identity_service
        self.er_service = er_service or entity_resolution_service

    def execute(
        self,
        observations: List[Dict[str, Any]],
        metrics: DataFactoryMetrics,
    ) -> List[Dict[str, Any]]:
        """Resolves observations to canonical identities."""
        resolved_entities: List[Dict[str, Any]] = []

        for obs in observations:
            company_name = obs.get("company_name", "Unknown")
            domain = obs.get("domain", "")

            try:
                # 1. Deterministic canonical resolution
                company = self.identity_service.get_or_create_company(
                    name=company_name,
                    domain=domain,
                )

                # Check if newly created vs existing
                if company.metadata_json.get("is_new"):
                    metrics.companies_created += 1
                else:
                    metrics.companies_updated += 1
                    metrics.er_matches += 1

                resolved_entities.append({
                    "canonical_company_id": company.id,
                    "canonical_domain_id": company.primary_domain_id,
                    "company_name": company.canonical_name,
                    "domain": domain,
                    "observation": obs,
                })
            except Exception as e:
                metrics.errors += 1

        return resolved_entities
