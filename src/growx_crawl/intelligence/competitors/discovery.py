"""
GrowX Competitor Discovery & Profile Builder.
Constructs competitive profiles from verified facts and generates candidate competitors.
"""

from typing import Any, Dict, List, Optional
from growx_crawl.intelligence.competitors.models import CompetitiveProfile
from growx_crawl.intelligence.competitors.policies import canonical_pair
from growx_crawl.intelligence.facts.repository import BaseFactRepository, SqliteFactRepository
from growx_crawl.storage.db import get_db


class CompetitiveProfileBuilder:
    """Builds a structured CompetitiveProfile from company facts and identity attributes."""

    def __init__(self, fact_repository: Optional[BaseFactRepository] = None):
        self.fact_repo = fact_repository or SqliteFactRepository()

    def build_profile(
        self,
        company_id: str,
        company_data: Optional[Dict[str, Any]] = None,
        facts: Optional[List[Any]] = None,
    ) -> CompetitiveProfile:
        """Derives profile dimensions from canonical facts and basic entity data."""
        data = company_data or {}
        company_name = data.get("canonical_name") or data.get("company_name") or company_id

        industries = []
        if data.get("industry"):
            industries.append(data["industry"])

        products = []
        services = []
        technologies = data.get("technologies_used", []) or []
        geographies = []
        if data.get("city"):
            geographies.append(data["city"])
        if data.get("country_code"):
            geographies.append(data["country_code"])

        target_customers = []
        positioning_terms = []
        buying_problems = []
        company_size = data.get("employee_range")

        # Ingest verified facts if available
        if facts is None:
            try:
                facts = self.fact_repo.list_current("company", company_id)
            except Exception:
                facts = []

        for f in facts:
            pred = getattr(f, "predicate", "") or (f.get("predicate") if isinstance(f, dict) else "")
            val_json = getattr(f, "current_value_json", {}) or (f.get("current_value_json") if isinstance(f, dict) else {})
            val = val_json.get("value") if isinstance(val_json, dict) else val_json

            if pred == "company.industry" and val:
                if str(val) not in industries:
                    industries.append(str(val))
            elif pred == "company.product" and val:
                if str(val) not in products:
                    products.append(str(val))
            elif pred == "company.service" and val:
                if str(val) not in services:
                    services.append(str(val))
            elif pred == "company.technology" and val:
                if str(val) not in technologies:
                    technologies.append(str(val))
            elif pred == "company.location" and val:
                if str(val) not in geographies:
                    geographies.append(str(val))
            elif pred == "company.employee_range" and val:
                company_size = str(val)
            elif pred == "company.description" and val:
                positioning_terms.append(str(val))

        # Infer basic buying problems or target customers if industry present
        for ind in industries:
            buying_problems.append(f"{ind.lower()} operations")

        return CompetitiveProfile(
            company_id=company_id,
            company_name=company_name,
            industries=industries,
            products=products,
            services=services,
            target_customers=target_customers,
            company_size=company_size,
            geographies=geographies,
            technologies=technologies,
            positioning_terms=positioning_terms,
            buying_problems=buying_problems,
        )


class CompetitorCandidateGenerator:
    """Surfaces candidate competitors from stored GrowX intelligence dataset."""

    def __init__(
        self,
        db_path: Optional[str] = None,
        profile_builder: Optional[CompetitiveProfileBuilder] = None,
    ):
        self.db_path = db_path
        self.profile_builder = profile_builder or CompetitiveProfileBuilder()

    def generate_candidates(
        self,
        target_profile: CompetitiveProfile,
        rejection_check_fn: Optional[Any] = None,
        limit: int = 50,
        known_companies: Optional[List[Dict[str, Any]]] = None,
    ) -> List[CompetitiveProfile]:
        """
        Retrieves candidate companies from internal database matching industry or offerings.
        Enforces internal-data-first rule and respects rejection memory.
        """
        candidates: List[CompetitiveProfile] = []

        if known_companies is not None:
            raw_companies = known_companies
        else:
            raw_companies = self._query_database_candidates(target_profile, limit * 2)

        for comp in raw_companies:
            comp_id = comp.get("id") or comp.get("company_id")
            if not comp_id or comp_id == target_profile.company_id:
                continue

            # Check rejection memory (Section 57)
            pair_key = canonical_pair(target_profile.company_id, comp_id)
            if rejection_check_fn and rejection_check_fn(pair_key):
                continue

            candidate_profile = self.profile_builder.build_profile(
                company_id=comp_id,
                company_data=comp,
            )
            candidates.append(candidate_profile)
            if len(candidates) >= limit:
                break

        return candidates

    def _query_database_candidates(
        self,
        profile: CompetitiveProfile,
        fetch_limit: int,
    ) -> List[Dict[str, Any]]:
        """Queries local SQLite companies matching target profile keywords."""
        if not profile.industries:
            query = "SELECT * FROM companies WHERE id != ? LIMIT ?"
            params = (profile.company_id, fetch_limit)
        else:
            # Query by same industry
            placeholders = ",".join("?" for _ in profile.industries)
            query = f"SELECT * FROM companies WHERE id != ? AND industry IN ({placeholders}) LIMIT ?"
            params = (profile.company_id, *profile.industries, fetch_limit)

        try:
            with get_db(self.db_path) as conn:
                rows = conn.execute(query, params).fetchall()
                return [dict(r) for r in rows]
        except Exception:
            return []
