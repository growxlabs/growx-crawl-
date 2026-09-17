"""
GrowX Data Factory Stage 9: Search Indexing.
Updates downstream search representations (SQLite FTS5 / Postgres search)
for trusted canonical entities. Strictly downstream from truth.
"""

from typing import Any, Dict, List, Optional
from growx_crawl.data_factory.metrics import DataFactoryMetrics
from growx_crawl.search.indexer import document_indexer


class IndexStage:
    """Propagates verified and quality-checked entities to the downstream search index."""

    def __init__(self, indexer=None):
        self.indexer = indexer or document_indexer

    def execute(
        self,
        items: List[Dict[str, Any]],
        metrics: DataFactoryMetrics,
    ) -> List[Dict[str, Any]]:
        indexed_items: List[Dict[str, Any]] = []

        for item in items:
            # Only index quality-trusted entities
            if not item.get("quality_trusted", True):
                continue

            domain = item.get("domain", "")
            name = item.get("company_name", domain)
            obs = item.get("observation", {})
            desc = obs.get("description", "")
            cid = item.get("canonical_company_id", domain)
            url = obs.get("source_url", f"https://{domain}")
            html = f"<html><head><title>{name}</title></head><body><h1>{name}</h1><p>{desc}</p><p>{' '.join(obs.get('emails', []))}</p></body></html>"

            try:
                if hasattr(self.indexer, "index_document"):
                    self.indexer.index_document(
                        target_id=cid,
                        url=url,
                        html=html,
                        fallback_title=name,
                    )
                elif hasattr(self.indexer, "index_page"):
                    self.indexer.index_page(
                        url=url,
                        title=name,
                        body_text=f"{name} {desc}",
                        domain=domain,
                    )
                indexed_items.append(item)
            except Exception:
                # Non-fatal error: indexing is strictly downstream
                pass

        return indexed_items
