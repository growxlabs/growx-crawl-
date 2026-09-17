import logging

logger = logging.getLogger("growx_crawl.storage.postgres.schema")

PG_SCHEMA_SQL = """
-- GrowX Crawl & AutoGTM Platform — Phase 01 Canonical PostgreSQL Schema

CREATE TABLE IF NOT EXISTS domains (
    id VARCHAR(64) PRIMARY KEY,
    registrable_domain TEXT NOT NULL,
    hostname TEXT NOT NULL,
    normalized_domain TEXT UNIQUE NOT NULL,
    scheme VARCHAR(16) DEFAULT 'https',
    status VARCHAR(32) DEFAULT 'active',
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_crawled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata_json JSONB DEFAULT '{}'::jsonb
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_domains_normalized ON domains(normalized_domain);
CREATE INDEX IF NOT EXISTS idx_domains_last_crawled ON domains(last_crawled_at);

CREATE TABLE IF NOT EXISTS companies (
    id VARCHAR(64) PRIMARY KEY,
    canonical_name TEXT NOT NULL,
    legal_name TEXT,
    normalized_name TEXT NOT NULL,
    primary_domain_id VARCHAR(64) REFERENCES domains(id) ON DELETE SET NULL,
    industry TEXT,
    employee_range TEXT,
    country_code VARCHAR(8),
    summary TEXT,
    status VARCHAR(32) DEFAULT 'active',
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_crawled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata_json JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_companies_normalized_name ON companies(normalized_name);
CREATE INDEX IF NOT EXISTS idx_companies_last_seen ON companies(last_seen_at);

CREATE TABLE IF NOT EXISTS company_domains (
    company_id VARCHAR(64) NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    domain_id VARCHAR(64) NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
    relationship_type VARCHAR(32) DEFAULT 'primary',
    confidence REAL DEFAULT 1.0,
    is_primary BOOLEAN DEFAULT TRUE,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_verified_at TIMESTAMPTZ,
    PRIMARY KEY (company_id, domain_id)
);

CREATE INDEX IF NOT EXISTS idx_company_domains_company ON company_domains(company_id);
CREATE INDEX IF NOT EXISTS idx_company_domains_domain ON company_domains(domain_id);

CREATE TABLE IF NOT EXISTS company_aliases (
    id VARCHAR(64) PRIMARY KEY,
    company_id VARCHAR(64) NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    alias TEXT NOT NULL,
    normalized_alias TEXT NOT NULL,
    source_id VARCHAR(64),
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_company_aliases_normalized ON company_aliases(normalized_alias);

CREATE TABLE IF NOT EXISTS people (
    id VARCHAR(64) PRIMARY KEY,
    full_name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    headline TEXT,
    location_text TEXT,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata_json JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_people_normalized_name ON people(normalized_name);

CREATE TABLE IF NOT EXISTS employments (
    id VARCHAR(64) PRIMARY KEY,
    person_id VARCHAR(64) NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    company_id VARCHAR(64) NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    normalized_title TEXT NOT NULL,
    department TEXT,
    seniority VARCHAR(64),
    is_current BOOLEAN DEFAULT TRUE,
    source_id VARCHAR(64),
    confidence REAL DEFAULT 1.0,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_verified_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_employments_person ON employments(person_id);
CREATE INDEX IF NOT EXISTS idx_employments_company ON employments(company_id);
CREATE INDEX IF NOT EXISTS idx_employments_title ON employments(normalized_title);
CREATE INDEX IF NOT EXISTS idx_employments_is_current ON employments(is_current);

CREATE TABLE IF NOT EXISTS sources (
    id VARCHAR(64) PRIMARY KEY,
    source_type VARCHAR(64) NOT NULL,
    url TEXT NOT NULL,
    domain_id VARCHAR(64) REFERENCES domains(id) ON DELETE SET NULL,
    content_hash VARCHAR(128),
    observed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata_json JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_sources_url ON sources(url);
CREATE INDEX IF NOT EXISTS idx_sources_content_hash ON sources(content_hash);

CREATE TABLE IF NOT EXISTS crawl_jobs (
    id VARCHAR(64) PRIMARY KEY,
    target TEXT NOT NULL,
    status VARCHAR(32) NOT NULL,
    config_json JSONB DEFAULT '{}'::jsonb,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    attempts INTEGER DEFAULT 1,
    error_code VARCHAR(64),
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_crawl_jobs_status ON crawl_jobs(status);

CREATE TABLE IF NOT EXISTS crawl_runs (
    id VARCHAR(64) PRIMARY KEY,
    job_id VARCHAR(64) NOT NULL REFERENCES crawl_jobs(id) ON DELETE CASCADE,
    target_url TEXT NOT NULL,
    domain_id VARCHAR(64) REFERENCES domains(id) ON DELETE SET NULL,
    fetcher_type VARCHAR(32) NOT NULL,
    http_status INTEGER,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,
    page_count INTEGER DEFAULT 1,
    success BOOLEAN DEFAULT TRUE,
    error_code VARCHAR(64),
    metadata_json JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_crawl_runs_domain ON crawl_runs(domain_id);
CREATE INDEX IF NOT EXISTS idx_crawl_runs_started ON crawl_runs(started_at);
"""


def init_pg_schema(conn) -> None:
    """
    Executes Phase 01 DDL migration on PostgreSQL/Supabase database connection.
    """
    with conn.cursor() as cur:
        cur.execute(PG_SCHEMA_SQL)
    conn.commit()
    logger.info("Initialized Phase 01 Canonical PostgreSQL Schema successfully.")
