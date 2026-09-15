import sqlite3
from typing import Optional


SEARCH_SCHEMA_SQL = """
-- 1. Full-Text Search Inverted Index using FTS5 with Porter Stemmer & Unicode61
CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(
    target_id UNINDEXED,
    url UNINDEXED,
    domain,
    title,
    description,
    content,
    tokenize = 'porter unicode61 remove_diacritics 1'
);

-- 2. Structured Document Catalog & Metadata for Fast Lookup and Analytics
CREATE TABLE IF NOT EXISTS search_documents (
    target_id TEXT PRIMARY KEY,
    url TEXT NOT NULL UNIQUE,
    domain TEXT NOT NULL,
    title TEXT,
    description TEXT,
    content_length INTEGER DEFAULT 0,
    word_count INTEGER DEFAULT 0,
    inbound_links INTEGER DEFAULT 0,
    indexed_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_search_docs_domain ON search_documents(domain);
CREATE INDEX IF NOT EXISTS idx_search_docs_indexed ON search_documents(indexed_at);

-- 3. Outlink Graph Table for Inbound Link Counting & Authority Scoring
CREATE TABLE IF NOT EXISTS page_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_url TEXT NOT NULL,
    from_domain TEXT NOT NULL,
    to_url TEXT NOT NULL,
    to_domain TEXT NOT NULL,
    anchor_text TEXT,
    discovered_at TEXT NOT NULL,
    UNIQUE(from_url, to_url)
);

CREATE INDEX IF NOT EXISTS idx_page_links_to_domain ON page_links(to_domain);
CREATE INDEX IF NOT EXISTS idx_page_links_from_domain ON page_links(from_domain);

-- 4. Search Query Telemetry & Performance Tracking
CREATE TABLE IF NOT EXISTS search_telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    hits_count INTEGER NOT NULL,
    latency_ms REAL NOT NULL,
    client_ip TEXT,
    searched_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_search_telemetry_time ON search_telemetry(searched_at);
"""


def init_search_tables(conn: sqlite3.Connection):
    """Ensure search index, document catalog, and link graph tables are initialized."""
    conn.executescript(SEARCH_SCHEMA_SQL)
