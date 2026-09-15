import sqlite3
from growx_crawl.storage.db import get_db

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS crawl_jobs (
    id TEXT PRIMARY KEY,
    query TEXT NOT NULL,
    industry TEXT,
    location TEXT,
    status TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT,
    discovered_count INTEGER DEFAULT 0,
    processed_count INTEGER DEFAULT 0,
    lead_count INTEGER DEFAULT 0,
    duplicate_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    configuration TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS crawl_targets (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    url TEXT NOT NULL,
    domain TEXT NOT NULL,
    source TEXT DEFAULT 'discovery',
    status TEXT NOT NULL,
    depth INTEGER DEFAULT 0,
    retry_count INTEGER DEFAULT 0,
    last_error TEXT,
    discovered_from TEXT,
    query_variant TEXT,
    discovered_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    FOREIGN KEY (job_id) REFERENCES crawl_jobs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_targets_job_status ON crawl_targets(job_id, status);
CREATE INDEX IF NOT EXISTS idx_targets_domain ON crawl_targets(domain);

CREATE TABLE IF NOT EXISTS pages (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    url TEXT NOT NULL,
    status_code INTEGER DEFAULT 200,
    content_type TEXT DEFAULT 'text/html',
    html_content TEXT,
    title TEXT,
    text_content TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (job_id) REFERENCES crawl_jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES crawl_targets(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS companies (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    domain TEXT NOT NULL,
    website TEXT NOT NULL,
    industry TEXT,
    category TEXT,
    description TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    country TEXT,
    source TEXT DEFAULT 'crawl',
    source_url TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    discovered_from TEXT,
    query_variant TEXT,
    rating REAL,
    review_count INTEGER,
    website_missing INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (job_id) REFERENCES crawl_jobs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_companies_domain ON companies(domain);
CREATE INDEX IF NOT EXISTS idx_companies_normalized_name ON companies(normalized_name);

CREATE TABLE IF NOT EXISTS contacts (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    job_id TEXT NOT NULL,
    name TEXT NOT NULL,
    title TEXT,
    email TEXT,
    phone TEXT,
    linkedin_url TEXT,
    source_url TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES crawl_jobs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS emails (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    email TEXT NOT NULL,
    normalized_email TEXT NOT NULL,
    is_generic INTEGER DEFAULT 0,
    source_url TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_emails_normalized ON emails(normalized_email);

CREATE TABLE IF NOT EXISTS phones (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    phone TEXT NOT NULL,
    normalized_phone TEXT NOT NULL,
    raw_phone TEXT NOT NULL,
    country_code TEXT,
    source_url TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_phones_normalized ON phones(normalized_phone);

CREATE TABLE IF NOT EXISTS social_profiles (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    url TEXT NOT NULL,
    normalized_url TEXT NOT NULL,
    handle TEXT,
    source_url TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_social_normalized ON social_profiles(normalized_url);

CREATE TABLE IF NOT EXISTS lead_candidates (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    job_id TEXT NOT NULL,
    score INTEGER NOT NULL,
    priority TEXT NOT NULL,
    score_reasons TEXT,
    status TEXT DEFAULT 'new',
    created_at TEXT NOT NULL,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES crawl_jobs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS dedupe_records (
    id TEXT PRIMARY KEY,
    canonical_company_id TEXT NOT NULL,
    duplicate_company_id TEXT NOT NULL,
    match_signals TEXT NOT NULL,
    confidence REAL NOT NULL,
    decision TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (canonical_company_id) REFERENCES companies(id) ON DELETE CASCADE,
    FOREIGN KEY (duplicate_company_id) REFERENCES companies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS crawl_errors (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    target_id TEXT,
    url TEXT NOT NULL,
    error_type TEXT NOT NULL,
    message TEXT NOT NULL,
    stack_trace TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (job_id) REFERENCES crawl_jobs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS source_events (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    details TEXT,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (job_id) REFERENCES crawl_jobs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS exports (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    file_path TEXT NOT NULL,
    format TEXT NOT NULL,
    lead_count INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (job_id) REFERENCES crawl_jobs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS push_history (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    payload_summary TEXT NOT NULL,
    status TEXT NOT NULL,
    response_message TEXT,
    pushed_at TEXT NOT NULL,
    FOREIGN KEY (job_id) REFERENCES crawl_jobs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS locations (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    name TEXT,
    address TEXT NOT NULL,
    city TEXT,
    state TEXT,
    country TEXT,
    phone TEXT,
    source_url TEXT NOT NULL,
    is_primary INTEGER DEFAULT 0,
    confidence REAL DEFAULT 1.0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS observed_facts (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    source_url TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    extraction_type TEXT DEFAULT 'text',
    observed_at TEXT NOT NULL,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS push_queue (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    company_id TEXT NOT NULL,
    payload_version TEXT DEFAULT '1',
    status TEXT DEFAULT 'pending',
    attempt_count INTEGER DEFAULT 0,
    last_attempt_at TEXT,
    last_error TEXT,
    remote_reference TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (job_id) REFERENCES crawl_jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS crawl_campaigns (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    industry TEXT NOT NULL,
    location_scope TEXT NOT NULL,
    target_leads INTEGER DEFAULT 100,
    status TEXT DEFAULT 'running',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agent_runs (
    id TEXT PRIMARY KEY,
    goal TEXT NOT NULL,
    status TEXT DEFAULT 'planning',
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    current_job_id TEXT,
    current_valid_leads INTEGER DEFAULT 0,
    target_leads INTEGER DEFAULT 100,
    last_action TEXT,
    summary TEXT,
    started_at TEXT NOT NULL,
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS agent_actions (
    id TEXT PRIMARY KEY,
    agent_run_id TEXT NOT NULL,
    action_type TEXT NOT NULL,
    summary TEXT NOT NULL,
    tool_call TEXT,
    tool_result_summary TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (agent_run_id) REFERENCES agent_runs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS api_keys (
    id TEXT PRIMARY KEY,
    key_hash TEXT NOT NULL UNIQUE,
    prefix TEXT NOT NULL,
    name TEXT NOT NULL,
    email TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    tier TEXT NOT NULL DEFAULT 'starter',
    rate_limit_rpm INTEGER DEFAULT 60,
    monthly_quota INTEGER DEFAULT 10000,
    requests_used INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    approved_at TEXT,
    last_used_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_status ON api_keys(status);

CREATE TABLE IF NOT EXISTS robots_cache (
    domain TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    status_code INTEGER DEFAULT 200,
    fetched_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS batch_jobs (
    id TEXT PRIMARY KEY,
    total_urls INTEGER NOT NULL,
    completed_count INTEGER DEFAULT 0,
    status TEXT NOT NULL,
    webhook_url TEXT,
    results TEXT,
    created_at TEXT NOT NULL,
    completed_at TEXT
);
"""


def init_db(db_path: str = None) -> None:
    with get_db(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
        _migrate_columns(conn)


def _migrate_columns(conn: sqlite3.Connection):
    # Ensure new tables exist
    conn.execute("""
    CREATE TABLE IF NOT EXISTS locations (
        id TEXT PRIMARY KEY, company_id TEXT NOT NULL, name TEXT, address TEXT NOT NULL,
        city TEXT, state TEXT, country TEXT, phone TEXT, source_url TEXT NOT NULL,
        is_primary INTEGER DEFAULT 0, confidence REAL DEFAULT 1.0, created_at TEXT NOT NULL,
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
    );""")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS observed_facts (
        id TEXT PRIMARY KEY, company_id TEXT NOT NULL, key TEXT NOT NULL, value TEXT NOT NULL,
        source_url TEXT NOT NULL, confidence REAL DEFAULT 1.0, extraction_type TEXT DEFAULT 'text',
        observed_at TEXT NOT NULL, FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
    );""")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS enrichment_history (
        id TEXT PRIMARY KEY, company_id TEXT NOT NULL, enrichment_version TEXT NOT NULL,
        profile_used TEXT NOT NULL, enriched_at TEXT NOT NULL,
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
    );""")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS push_queue (
        id TEXT PRIMARY KEY, job_id TEXT NOT NULL, company_id TEXT NOT NULL,
        payload_version TEXT DEFAULT '1', status TEXT DEFAULT 'pending',
        attempt_count INTEGER DEFAULT 0, last_attempt_at TEXT, last_error TEXT,
        remote_reference TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
        FOREIGN KEY (job_id) REFERENCES crawl_jobs(id) ON DELETE CASCADE,
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
    );""")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS api_keys (
        id TEXT PRIMARY KEY, key_hash TEXT NOT NULL UNIQUE, prefix TEXT NOT NULL,
        name TEXT NOT NULL, email TEXT, status TEXT NOT NULL DEFAULT 'pending',
        tier TEXT NOT NULL DEFAULT 'starter', rate_limit_rpm INTEGER DEFAULT 60,
        monthly_quota INTEGER DEFAULT 10000, requests_used INTEGER DEFAULT 0,
        created_at TEXT NOT NULL, approved_at TEXT, last_used_at TEXT
    );""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_status ON api_keys(status);")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS robots_cache (
        domain TEXT PRIMARY KEY, content TEXT NOT NULL, status_code INTEGER DEFAULT 200,
        fetched_at TEXT NOT NULL, expires_at TEXT NOT NULL
    );""")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS batch_jobs (
        id TEXT PRIMARY KEY, total_urls INTEGER NOT NULL, completed_count INTEGER DEFAULT 0,
        status TEXT NOT NULL, webhook_url TEXT, results TEXT,
        created_at TEXT NOT NULL, completed_at TEXT
    );""")
    try:
        conn.execute("CREATE INDEX IF NOT EXISTS idx_pages_target_id ON pages(target_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_pages_job_id ON pages(job_id);")
    except Exception:
        pass

    # Migration helper for newly added columns
    try:
        target_cols = [r["name"] for r in conn.execute("PRAGMA table_info(crawl_targets)").fetchall()]
        if target_cols:
            if "discovered_from" not in target_cols:
                conn.execute("ALTER TABLE crawl_targets ADD COLUMN discovered_from TEXT")
            if "query_variant" not in target_cols:
                conn.execute("ALTER TABLE crawl_targets ADD COLUMN query_variant TEXT")

        company_cols = [r["name"] for r in conn.execute("PRAGMA table_info(companies)").fetchall()]
        if company_cols:
            if "discovered_from" not in company_cols:
                conn.execute("ALTER TABLE companies ADD COLUMN discovered_from TEXT")
            if "query_variant" not in company_cols:
                conn.execute("ALTER TABLE companies ADD COLUMN query_variant TEXT")
            if "rating" not in company_cols:
                conn.execute("ALTER TABLE companies ADD COLUMN rating REAL")
            if "review_count" not in company_cols:
                conn.execute("ALTER TABLE companies ADD COLUMN review_count INTEGER")
            if "website_missing" not in company_cols:
                conn.execute("ALTER TABLE companies ADD COLUMN website_missing INTEGER DEFAULT 0")
            if "review_status" not in company_cols:
                conn.execute("ALTER TABLE companies ADD COLUMN review_status TEXT DEFAULT 'pending'")
        
        try:
            job_cols = [r["name"] for r in conn.execute("PRAGMA table_info(crawl_jobs)").fetchall()]
            if job_cols and "campaign_id" not in job_cols:
                conn.execute("ALTER TABLE crawl_jobs ADD COLUMN campaign_id TEXT REFERENCES crawl_campaigns(id)")
        except Exception:
            pass

        contact_cols = [r["name"] for r in conn.execute("PRAGMA table_info(contacts)").fetchall()]
        if contact_cols:
            if "decision_maker_tier" not in contact_cols:
                conn.execute("ALTER TABLE contacts ADD COLUMN decision_maker_tier TEXT")

        # Create performance indexes
        if company_cols:
            conn.execute("CREATE INDEX IF NOT EXISTS idx_companies_job_id ON companies(job_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_companies_review_status ON companies(review_status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_companies_domain ON companies(domain)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_companies_city ON companies(city)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_companies_industry ON companies(industry)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_lead_candidates_score ON lead_candidates(score)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_lead_candidates_priority ON lead_candidates(priority)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_contacts_company_id ON contacts(company_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_contacts_tier ON contacts(decision_maker_tier)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_observed_facts_company_id ON observed_facts(company_id)")
    except Exception:
        pass
