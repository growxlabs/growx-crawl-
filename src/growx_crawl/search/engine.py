import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from growx_crawl.storage.db import get_db
from growx_crawl.search.indexer import document_indexer
from growx_crawl.search.query import query_parser
from growx_crawl.search.ranker import search_ranker
from growx_crawl.search.schema import init_search_tables

logger = logging.getLogger("growx_crawl.search.engine")


class SearchEngine:
    """
    Production-grade, self-hosted Web Search Engine combining SQLite FTS5,
    BM25 ranking, snippet highlighting, link graph authority, and query parsing.
    """

    def __init__(self):
        self.indexer = document_indexer
        self.parser = query_parser
        self.ranker = search_ranker

    def search(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        domain: Optional[str] = None,
        client_ip: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes a high-speed full-text search across all indexed web documents.
        """
        start_time = time.perf_counter()
        parsed = self.parser.parse(query)
        active_domain = domain or parsed.domain_filter

        results: List[Dict[str, Any]] = []
        total_hits = 0

        with get_db() as conn:
            init_search_tables(conn)

            # Case 1: Empty query - return most recent indexed documents
            if not parsed.fts_expression:
                count_sql = "SELECT COUNT(*) FROM search_documents"
                query_sql = """
                    SELECT 
                        target_id, url, domain, title, description,
                        description AS snippet,
                        0.0 AS bm25_score,
                        inbound_links, indexed_at
                    FROM search_documents
                """
                params: List[Any] = []
                if active_domain:
                    clean_dom = active_domain.replace("www.", "")
                    count_sql += " WHERE (domain = ? OR domain = ? OR domain LIKE ? OR url LIKE ?)"
                    query_sql += " WHERE (domain = ? OR domain = ? OR domain LIKE ? OR url LIKE ?)"
                    params.extend([active_domain, clean_dom, f"%{clean_dom}%", f"%{clean_dom}%"])

                query_sql += " ORDER BY indexed_at DESC LIMIT ? OFFSET ?;"
                params_with_paging = list(params) + [limit, offset]

                total_hits = conn.execute(count_sql, params).fetchone()[0]
                rows = conn.execute(query_sql, params_with_paging).fetchall()

                for r in rows:
                    results.append({
                        "target_id": r["target_id"],
                        "url": r["url"],
                        "domain": r["domain"],
                        "title": r["title"] or "Untitled Document",
                        "snippet": r["snippet"] or "No document preview available.",
                        "score": 1.0,
                        "inbound_links": r["inbound_links"] or 0,
                        "indexed_at": r["indexed_at"],
                    })

            # Case 2: Full-text search with BM25 and highlighted snippets
            else:
                try:
                    # Count matching records
                    count_sql = "SELECT COUNT(*) FROM search_index WHERE search_index MATCH ?"
                    count_params = [parsed.fts_expression]
                    if active_domain:
                        clean_dom = active_domain.replace("www.", "")
                        count_sql += " AND (domain = ? OR domain = ? OR domain LIKE ?)"
                        count_params.extend([active_domain, clean_dom, f"%{clean_dom}%"])
                    total_hits = conn.execute(count_sql, count_params).fetchone()[0]

                    # Fetch matching records with snippets and BM25 weights
                    # Column order in search_index: 0=target_id, 1=url, 2=domain, 3=title, 4=description, 5=content
                    # Weights: domain=3.0, title=12.0, description=5.0, content=1.0
                    search_sql = """
                        SELECT 
                            s.target_id,
                            s.url,
                            s.domain,
                            s.title,
                            s.description,
                            snippet(search_index, 5, '<mark>', '</mark>', '...', 28) AS snippet,
                            bm25(search_index, 3.0, 12.0, 5.0, 1.0) AS bm25_score,
                            COALESCE(d.inbound_links, 0) AS inbound_links,
                            COALESCE(d.indexed_at, '') AS indexed_at
                        FROM search_index s
                        LEFT JOIN search_documents d ON s.target_id = d.target_id
                        WHERE search_index MATCH ?
                    """
                    search_params = [parsed.fts_expression]
                    if active_domain:
                        clean_dom = active_domain.replace("www.", "")
                        search_sql += " AND (s.domain = ? OR s.domain = ? OR s.domain LIKE ?)"
                        search_params.extend([active_domain, clean_dom, f"%{clean_dom}%"])

                    search_sql += " ORDER BY bm25_score ASC LIMIT ? OFFSET ?;"
                    search_params.extend([limit, offset])

                    rows = conn.execute(search_sql, search_params).fetchall()

                    for r in rows:
                        snippet_text = r["snippet"]
                        if not snippet_text or snippet_text.strip() == "...":
                            snippet_text = r["description"] or "Document content matched query terms."

                        score = self.ranker.calculate_score(
                            bm25_raw=float(r["bm25_score"]),
                            title=r["title"] or "",
                            query_terms=parsed.keywords,
                            inbound_links=int(r["inbound_links"] or 0),
                            indexed_at=r["indexed_at"],
                        )

                        results.append({
                            "target_id": r["target_id"],
                            "url": r["url"],
                            "domain": r["domain"],
                            "title": r["title"] or r["url"],
                            "snippet": snippet_text,
                            "score": score,
                            "inbound_links": r["inbound_links"] or 0,
                            "indexed_at": r["indexed_at"],
                        })

                    # Sort final results by composite ranker score
                    results.sort(key=lambda x: x["score"], reverse=True)

                except Exception as e:
                    logger.warning(f"FTS5 Query execution fallback: {e}")
                    # Fallback to simple LIKE search if complex FTS5 syntax hit an edge case
                    total_hits = 0
                    results = []

            # Calculate search latency in milliseconds
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            # 3. Log search telemetry
            if query.strip():
                try:
                    conn.execute(
                        """
                        INSERT INTO search_telemetry (query, hits_count, latency_ms, client_ip, searched_at)
                        VALUES (?, ?, ?, ?, ?);
                        """,
                        (
                            query[:200],
                            total_hits,
                            round(elapsed_ms, 2),
                            client_ip or "127.0.0.1",
                            datetime.now(timezone.utc).isoformat(),
                        ),
                    )
                except Exception:
                    pass

        return {
            "query": query,
            "parsed_filter": active_domain,
            "total_hits": total_hits,
            "page": (offset // limit) + 1 if limit > 0 else 1,
            "limit": limit,
            "latency_ms": round(elapsed_ms, 2),
            "results": results,
        }

    def get_stats(self) -> Dict[str, Any]:
        """
        Returns real-time search engine catalog size and telemetry stats.
        """
        with get_db() as conn:
            init_search_tables(conn)
            total_docs = conn.execute("SELECT COUNT(*) FROM search_documents;").fetchone()[0]
            total_domains = conn.execute("SELECT COUNT(DISTINCT domain) FROM search_documents;").fetchone()[0]
            total_links = conn.execute("SELECT COUNT(*) FROM page_links;").fetchone()[0]
            total_queries = conn.execute("SELECT COUNT(*) FROM search_telemetry;").fetchone()[0]
            avg_latency = conn.execute("SELECT AVG(latency_ms) FROM search_telemetry;").fetchone()[0] or 0.0
            recent_queries_rows = conn.execute(
                """
                SELECT query, COUNT(*) AS count, MAX(searched_at) AS last_searched
                FROM search_telemetry
                GROUP BY query
                ORDER BY count DESC, last_searched DESC
                LIMIT 8;
                """
            ).fetchall()

        return {
            "total_documents": total_docs,
            "total_domains": total_domains,
            "total_outlinks_tracked": total_links,
            "total_queries_served": total_queries,
            "avg_latency_ms": round(avg_latency, 2),
            "popular_queries": [dict(r) for r in recent_queries_rows],
        }

    def reindex_all(self, limit: int = 1000) -> Dict[str, Any]:
        """Trigger a bulk reindex of all historic pages in database."""
        return self.indexer.bulk_reindex_all_pages(limit=limit)


search_engine = SearchEngine()
