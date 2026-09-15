import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class SearchRanker:
    """
    Ranks search results by combining FTS5 BM25 score, Title exact matches,
    Inbound Link Graph authority, and document recency.
    """

    @staticmethod
    def calculate_score(
        bm25_raw: float,
        title: str,
        query_terms: List[str],
        inbound_links: int = 0,
        indexed_at: Optional[str] = None,
    ) -> float:
        # FTS5 bm25() returns negative numbers (e.g. -12.4). Lower is better.
        # We invert so higher number = more relevant.
        relevance = abs(bm25_raw)

        # 1. Exact Match Title Bonus (+8.0)
        title_lower = (title or "").lower()
        title_matches = 0
        for term in query_terms:
            if term.lower() in title_lower:
                title_matches += 1
        title_boost = title_matches * 4.0

        # 2. Inbound Link Graph Authority Bonus (PageRank approximation)
        authority_boost = 0.0
        if inbound_links > 0:
            authority_boost = round(math.log2(1 + inbound_links) * 1.5, 2)

        # 3. Recency Decay Bonus (favor newer documents slightly)
        recency_boost = 0.0
        if indexed_at:
            try:
                dt = datetime.fromisoformat(indexed_at)
                now = datetime.now(timezone.utc)
                age_days = max(0, (now - dt).total_seconds() / 86400)
                if age_days < 7:
                    recency_boost = 2.0
                elif age_days < 30:
                    recency_boost = 1.0
            except Exception:
                pass

        total_score = round(relevance + title_boost + authority_boost + recency_boost, 2)
        return total_score


search_ranker = SearchRanker()
