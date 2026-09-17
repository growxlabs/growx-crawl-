"""
GrowX Competitor Graph Traversal.
In-memory traversal and formatting of competitive nodes and edges.
"""

from typing import Any, Dict, List, Optional, Set
from growx_crawl.intelligence.competitors.models import (
    CompetitorRelationshipEntity,
    RelationshipStatus,
)
from growx_crawl.intelligence.competitors.repository import BaseCompetitorRepository


class CompetitorGraph:
    """Provides relational graph traversal across competitive edges."""

    def __init__(self, repository: BaseCompetitorRepository):
        self.repo = repository

    def get_competitors(
        self,
        company_id: str,
        relationship_types: Optional[List[str]] = None,
        min_strength: float = 0.0,
        status: Optional[str] = None,
        limit: int = 20,
    ) -> List[CompetitorRelationshipEntity]:
        """Queries immediate competitor relationships for a company."""
        rels = self.repo.list_relationships(
            company_id=company_id,
            status=status,
            min_strength=min_strength,
            limit=limit,
        )
        if relationship_types:
            types_set = {t.lower() for t in relationship_types}
            rels = [r for r in rels if r.relationship_type.lower() in types_set]
        return rels

    def get_graph(
        self,
        company_id: str,
        depth: int = 1,
        min_strength: float = 0.0,
        status_filter: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Traverses competitor edges up to specified depth (1 or 2).
        Returns a JSON-serializable graph with 'nodes' and 'edges'.
        """
        nodes: Dict[str, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        visited_pairs: Set[str] = set()

        # Seed node
        nodes[company_id] = {"id": company_id, "is_root": True}

        # Level 1 traversal
        l1_rels = self.repo.list_relationships(
            company_id=company_id,
            min_strength=min_strength,
            limit=50,
        )
        if status_filter:
            l1_rels = [r for r in l1_rels if r.status in status_filter]

        next_hop_ids: Set[str] = set()

        for r in l1_rels:
            if r.canonical_pair in visited_pairs:
                continue
            visited_pairs.add(r.canonical_pair)

            other_id = (
                r.competitor_company_id if r.company_id == company_id else r.company_id
            )
            nodes[other_id] = {"id": other_id, "is_root": False}
            next_hop_ids.add(other_id)

            edges.append({
                "id": r.id,
                "source": r.company_id,
                "target": r.competitor_company_id,
                "canonical_pair": r.canonical_pair,
                "relationship_type": r.relationship_type,
                "status": r.status,
                "strength": r.strength,
                "confidence": r.confidence,
                "reasons": r.reasons,
            })

        # Level 2 traversal if depth > 1
        if depth > 1:
            for neighbor_id in list(next_hop_ids)[:10]:  # Bound depth-2 fanout
                l2_rels = self.repo.list_relationships(
                    company_id=neighbor_id,
                    min_strength=min_strength,
                    limit=20,
                )
                if status_filter:
                    l2_rels = [r for r in l2_rels if r.status in status_filter]

                for r in l2_rels:
                    if r.canonical_pair in visited_pairs:
                        continue
                    visited_pairs.add(r.canonical_pair)

                    other_id = (
                        r.competitor_company_id if r.company_id == neighbor_id else r.company_id
                    )
                    if other_id not in nodes:
                        nodes[other_id] = {"id": other_id, "is_root": False}

                    edges.append({
                        "id": r.id,
                        "source": r.company_id,
                        "target": r.competitor_company_id,
                        "canonical_pair": r.canonical_pair,
                        "relationship_type": r.relationship_type,
                        "status": r.status,
                        "strength": r.strength,
                        "confidence": r.confidence,
                        "reasons": r.reasons,
                    })

        return {
            "root_company_id": company_id,
            "depth": depth,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "nodes": list(nodes.values()),
            "edges": edges,
        }
