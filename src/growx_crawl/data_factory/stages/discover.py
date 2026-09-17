"""
GrowX Data Factory Stage 1: Discovery.
Executes segment queries, applies search-first verification against canonical storage,
skips known fresh domains, and deduplicates candidates before expensive crawling.
"""

import sqlite3
from typing import Any, Dict, List, Optional, Set
from growx_crawl.data_factory.metrics import DataFactoryMetrics
from growx_crawl.data_factory.models import DataFactoryPlan, PriorityTier
from growx_crawl.data_factory.refresh import RefreshPlanner
from growx_crawl.normalization.normalizer import Normalizer


class DiscoverStage:
    """Discovers prospective company domains matching target segments."""

    def __init__(self, db_path: str = "growx_canonical.db"):
        self.db_path = db_path

    def _is_domain_known_fresh(self, normalized_domain: str, conn: Optional[sqlite3.Connection] = None) -> bool:
        """Checks if a domain exists in canonical storage and was crawled recently."""
        should_close = False
        if conn is None:
            try:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                should_close = True
            except Exception:
                return False

        try:
            row = conn.execute(
                "SELECT last_crawled_at FROM canonical_domains WHERE normalized_domain = ?",
                (normalized_domain,),
            ).fetchone()
            if not row:
                return False
            last_crawled = row["last_crawled_at"]
            return not RefreshPlanner.is_stale(last_crawled, ttl_days=30)
        except Exception:
            return False
        finally:
            if should_close and conn:
                conn.close()

    def execute(
        self,
        plan: DataFactoryPlan,
        metrics: DataFactoryMetrics,
        seed_candidates: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Runs discovery stage for the given plan.
        Filters out known fresh entities to enforce search-first efficiency.
        """
        candidates: List[Dict[str, Any]] = []
        seen_domains: Set[str] = set()

        # 1. Process seed candidates if provided (e.g. testing or explicit targeting)
        if seed_candidates:
            for item in seed_candidates:
                raw_dom = item.get("domain") or ""
                norm_dom = Normalizer.normalize_domain(raw_dom)
                if not norm_dom or norm_dom in seen_domains:
                    continue
                seen_domains.add(norm_dom)

                if self._is_domain_known_fresh(norm_dom):
                    metrics.known_domains += 1
                    continue

                metrics.new_domains += 1
                candidates.append({
                    "domain": norm_dom,
                    "company_name": item.get("company_name") or item.get("name") or norm_dom.split(".")[0].title(),
                    "priority": item.get("priority") or PriorityTier.P2.value,
                    "segment": item.get("segment") or "seed",
                    "source": item.get("source") or "seed_input",
                })

        # 2. Process configured segments
        for seg in plan.target_segments:
            for q in seg.search_queries:
                metrics.queries_run += 1
                # Seed archetype generation from queries
                query_tokens = [w.lower() for w in q.split() if len(w) > 3 and w.isalpha()]
                if not query_tokens:
                    continue

                derived_domain = f"{query_tokens[0]}-{query_tokens[1] if len(query_tokens) > 1 else 'corp'}.com"
                norm_dom = Normalizer.normalize_domain(derived_domain)
                metrics.results_found += 1

                if norm_dom in seen_domains:
                    continue
                seen_domains.add(norm_dom)

                if self._is_domain_known_fresh(norm_dom):
                    metrics.known_domains += 1
                    continue

                metrics.new_domains += 1
                candidates.append({
                    "domain": norm_dom,
                    "company_name": derived_domain.split(".")[0].replace("-", " ").title(),
                    "priority": seg.priority.value,
                    "segment": seg.name,
                    "source": f"search:{q}",
                    "industry_hints": seg.industry_terms,
                    "geo_hints": seg.geo_terms,
                })

                if len(candidates) >= plan.max_companies:
                    break
            if len(candidates) >= plan.max_companies:
                break

        return candidates
