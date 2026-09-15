import pytest
import httpx
from growx_crawl.search.engine import search_engine
from growx_crawl.search.indexer import document_indexer
from growx_crawl.search.query import query_parser
from growx_crawl.search.ranker import search_ranker
from growx_crawl.search.schema import init_search_tables
from growx_crawl.storage.db import get_db
from growx_crawl.web.app import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


def test_search_schema_and_query_parser():
    """Verify search schema initializes and query parser extracts phrases & domain filters."""
    with get_db() as conn:
        init_search_tables(conn)
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        assert "search_documents" in tables
        assert "page_links" in tables
        assert "search_telemetry" in tables

    # Test query parser
    q1 = query_parser.parse('site:growxlabs.tech "AI product studio" python')
    assert q1.domain_filter == "growxlabs.tech"
    assert '"AI product studio"' in q1.fts_expression
    assert '"python"' in q1.fts_expression
    assert "AI product studio" in q1.keywords

    # Test boolean query
    q2 = query_parser.parse("react AND nodejs OR python")
    assert "AND" in q2.fts_expression
    assert "OR" in q2.fts_expression


def test_document_indexer_and_link_extraction():
    """Verify document parser extracts clean text, title, and outlinks."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sovereign Search Architecture</title>
        <meta name="description" content="A self-hosted web search engine designed for high throughput.">
    </head>
    <body>
        <script>console.log('noise');</script>
        <nav><a href="/home">Home</a></nav>
        <h1>Autonomous Crawlers and Search Engines</h1>
        <p>This engine combines BM25 ranking and link graph authority algorithms.</p>
        <a href="https://example.com/docs">Documentation Link</a>
        <a href="https://github.com/growxlabs">GitHub Source</a>
    </body>
    </html>
    """
    url = "https://growxlabs.tech/search-docs"
    target_id = "tgt_test_search_1"

    res = document_indexer.index_document(
        target_id=target_id,
        url=url,
        html=html,
        fallback_title="Search Docs",
    )

    assert res["status"] == "indexed"
    assert res["domain"] == "growxlabs.tech"
    assert res["title"] == "Sovereign Search Architecture"
    assert res["outlinks_count"] >= 2

    # Verify document is in search_documents
    with get_db() as conn:
        row = conn.execute("SELECT * FROM search_documents WHERE target_id = ?", (target_id,)).fetchone()
        assert row is not None
        assert row["domain"] == "growxlabs.tech"
        assert "self-hosted" in row["description"]


def test_search_engine_ranking_and_snippets():
    """Verify FTS5 BM25 search execution, snippet generation, and composite score ranking."""
    # Index a second test document
    html2 = """
    <html>
    <head><title>Machine Learning Engineering Lab</title></head>
    <body><p>Deep neural networks and LLM agent orchestration.</p></body>
    </html>
    """
    document_indexer.index_document(
        target_id="tgt_test_search_2",
        url="https://growxlabs.tech/ml-lab",
        html=html2,
        fallback_title="ML Lab",
    )

    # Search for "Sovereign Search"
    search_res = search_engine.search("Sovereign Search")
    assert search_res["total_hits"] >= 1
    assert search_res["latency_ms"] < 50
    first_result = search_res["results"][0]
    assert "Sovereign" in first_result["title"]
    assert first_result["score"] > 0

    # Search with domain filter
    domain_res = search_engine.search("site:growxlabs.tech Machine Learning")
    assert domain_res["total_hits"] >= 1
    assert domain_res["parsed_filter"] == "growxlabs.tech"

    # Search engine stats
    stats = search_engine.get_stats()
    assert stats["total_documents"] >= 2
    assert stats["total_domains"] >= 1


@pytest.mark.asyncio
async def test_search_api_endpoints():
    """Verify REST API /v1/search, /v1/search/stats, and /v1/search/reindex."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Search endpoint
        res = await client.get(
            "/v1/search?q=Search&limit=5",
            headers={"Authorization": "Bearer gx_live_sandbox_master_key"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "results" in data
        assert "total_hits" in data
        assert "latency_ms" in data

        # 2. Stats endpoint
        stats_res = await client.get(
            "/v1/search/stats",
            headers={"Authorization": "Bearer gx_live_sandbox_master_key"},
        )
        assert stats_res.status_code == 200
        stats = stats_res.json()
        assert "total_documents" in stats
        assert "total_queries_served" in stats

        # 3. Reindex trigger
        reindex_res = await client.post(
            "/v1/search/reindex?limit=10",
            headers={"Authorization": "Bearer gx_live_sandbox_master_key"},
        )
        assert reindex_res.status_code == 200
        assert reindex_res.json()["status"] == "queued"
