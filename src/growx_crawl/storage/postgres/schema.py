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

CREATE TABLE IF NOT EXISTS object_refs (
    id VARCHAR(64) PRIMARY KEY,
    object_type VARCHAR(32) NOT NULL,
    bucket TEXT NOT NULL,
    object_key TEXT NOT NULL,
    provider VARCHAR(16) NOT NULL,
    content_type TEXT NOT NULL,
    content_encoding VARCHAR(16),
    content_hash VARCHAR(64) NOT NULL,
    size_bytes BIGINT NOT NULL,
    source_url TEXT,
    company_id VARCHAR(64) REFERENCES companies(id) ON DELETE SET NULL,
    domain_id VARCHAR(64) REFERENCES domains(id) ON DELETE SET NULL,
    crawl_run_id VARCHAR(64) REFERENCES crawl_runs(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata_json JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_object_refs_key ON object_refs(object_key);
CREATE INDEX IF NOT EXISTS idx_object_refs_hash ON object_refs(content_hash);
CREATE INDEX IF NOT EXISTS idx_object_refs_run ON object_refs(crawl_run_id);
CREATE INDEX IF NOT EXISTS idx_object_refs_comp ON object_refs(company_id);

-- Phase 03 Canonical Entity Identity Expansion Tables

CREATE TABLE IF NOT EXISTS locations (
    id VARCHAR(64) PRIMARY KEY,
    name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    city TEXT,
    region TEXT,
    country_code VARCHAR(8),
    postal_code VARCHAR(32),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    location_type VARCHAR(32) DEFAULT 'office',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata_json JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_locations_norm_name ON locations(normalized_name);
CREATE INDEX IF NOT EXISTS idx_locations_country ON locations(country_code);

CREATE TABLE IF NOT EXISTS company_locations (
    company_id VARCHAR(64) NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    location_id VARCHAR(64) NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    relationship_type VARCHAR(32) DEFAULT 'office',
    is_primary BOOLEAN DEFAULT TRUE,
    confidence REAL DEFAULT 1.0,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_verified_at TIMESTAMPTZ,
    PRIMARY KEY (company_id, location_id)
);

CREATE INDEX IF NOT EXISTS idx_company_locations_comp ON company_locations(company_id);
CREATE INDEX IF NOT EXISTS idx_company_locations_loc ON company_locations(location_id);

CREATE TABLE IF NOT EXISTS brands (
    id VARCHAR(64) PRIMARY KEY,
    canonical_name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    company_id VARCHAR(64) NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    primary_domain_id VARCHAR(64) REFERENCES domains(id) ON DELETE SET NULL,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata_json JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_brands_company ON brands(company_id);
CREATE INDEX IF NOT EXISTS idx_brands_normalized ON brands(normalized_name);

CREATE TABLE IF NOT EXISTS person_aliases (
    id VARCHAR(64) PRIMARY KEY,
    person_id VARCHAR(64) NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    alias TEXT NOT NULL,
    normalized_alias TEXT NOT NULL,
    alias_type VARCHAR(32) DEFAULT 'name_variant',
    source_id VARCHAR(64),
    confidence REAL DEFAULT 1.0,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_person_aliases_person ON person_aliases(person_id);
CREATE INDEX IF NOT EXISTS idx_person_aliases_normalized ON person_aliases(normalized_alias);

CREATE TABLE IF NOT EXISTS company_relationships (
    id VARCHAR(64) PRIMARY KEY,
    from_company_id VARCHAR(64) NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    to_company_id VARCHAR(64) NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    relationship_type VARCHAR(32) NOT NULL,
    confidence REAL DEFAULT 1.0,
    source_id VARCHAR(64),
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_verified_at TIMESTAMPTZ,
    metadata_json JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_company_rel_from ON company_relationships(from_company_id);
CREATE INDEX IF NOT EXISTS idx_company_rel_to ON company_relationships(to_company_id);
CREATE INDEX IF NOT EXISTS idx_company_rel_type ON company_relationships(relationship_type);

CREATE TABLE IF NOT EXISTS external_identities (
    id VARCHAR(64) PRIMARY KEY,
    entity_type VARCHAR(32) NOT NULL,
    entity_id VARCHAR(64) NOT NULL,
    provider VARCHAR(32) NOT NULL,
    external_id TEXT NOT NULL,
    external_url TEXT,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata_json JSONB DEFAULT '{}'::jsonb,
    CONSTRAINT uq_external_identities UNIQUE (provider, external_id)
);

CREATE INDEX IF NOT EXISTS idx_external_identities_entity ON external_identities(entity_type, entity_id);

CREATE TABLE IF NOT EXISTS identity_keys (
    id VARCHAR(64) PRIMARY KEY,
    entity_type VARCHAR(32) NOT NULL,
    entity_id VARCHAR(64) NOT NULL,
    key_type VARCHAR(32) NOT NULL,
    key_value TEXT NOT NULL,
    is_unique BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_verified_at TIMESTAMPTZ,
    CONSTRAINT uq_identity_keys UNIQUE (key_type, key_value)
);

CREATE INDEX IF NOT EXISTS idx_identity_keys_entity ON identity_keys(entity_type, entity_id);

CREATE TABLE IF NOT EXISTS identity_candidates (
    id VARCHAR(64) PRIMARY KEY,
    entity_type VARCHAR(32) NOT NULL,
    candidate_payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    candidate_key TEXT NOT NULL,
    source_id VARCHAR(64),
    status VARCHAR(32) DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolved_entity_id VARCHAR(64),
    metadata_json JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_identity_candidates_status ON identity_candidates(status);
CREATE INDEX IF NOT EXISTS idx_identity_candidates_key ON identity_candidates(candidate_key);

CREATE TABLE IF NOT EXISTS entity_merges (
    id VARCHAR(64) PRIMARY KEY,
    entity_type VARCHAR(32) NOT NULL,
    source_entity_id VARCHAR(64) NOT NULL,
    target_entity_id VARCHAR(64) NOT NULL,
    reason TEXT NOT NULL,
    method VARCHAR(32) DEFAULT 'manual',
    confidence REAL DEFAULT 1.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(64) DEFAULT 'system',
    metadata_json JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_entity_merges_source ON entity_merges(source_entity_id);
CREATE INDEX IF NOT EXISTS idx_entity_merges_target ON entity_merges(target_entity_id);

CREATE TABLE IF NOT EXISTS identity_events (
    id VARCHAR(64) PRIMARY KEY,
    entity_type VARCHAR(32) NOT NULL,
    entity_id VARCHAR(64) NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    source_id VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actor_type VARCHAR(32) DEFAULT 'system',
    actor_id VARCHAR(64)
);

CREATE INDEX IF NOT EXISTS idx_identity_events_entity ON identity_events(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_identity_events_type ON identity_events(event_type);

-- Phase 04 Fact + Evidence Intelligence Schema

CREATE TABLE IF NOT EXISTS fact_predicates (
    predicate VARCHAR(128) PRIMARY KEY,
    subject_type VARCHAR(32) NOT NULL,
    value_type VARCHAR(32) NOT NULL,
    cardinality VARCHAR(16) NOT NULL DEFAULT 'one',
    verification_policy VARCHAR(32) DEFAULT 'standard',
    freshness_policy VARCHAR(32) DEFAULT '90d',
    merge_policy VARCHAR(32) DEFAULT 'latest_wins',
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS observations (
    id VARCHAR(64) PRIMARY KEY,
    subject_type VARCHAR(32) NOT NULL,
    subject_id VARCHAR(64) NOT NULL,
    predicate VARCHAR(128) NOT NULL REFERENCES fact_predicates(predicate) ON DELETE CASCADE,
    raw_value TEXT,
    normalized_value_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    value_type VARCHAR(32) NOT NULL,
    source_id VARCHAR(64) REFERENCES sources(id) ON DELETE SET NULL,
    object_ref_id VARCHAR(64) REFERENCES object_refs(id) ON DELETE SET NULL,
    observed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    extractor_name VARCHAR(64) NOT NULL,
    extractor_version VARCHAR(32) DEFAULT 'v1.0',
    model_run_id VARCHAR(64),
    confidence REAL DEFAULT 1.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata_json JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_obs_subject ON observations(subject_type, subject_id);
CREATE INDEX IF NOT EXISTS idx_obs_predicate ON observations(predicate);
CREATE INDEX IF NOT EXISTS idx_obs_source ON observations(source_id);
CREATE INDEX IF NOT EXISTS idx_obs_observed_at ON observations(observed_at);

CREATE TABLE IF NOT EXISTS evidence (
    id VARCHAR(64) PRIMARY KEY,
    observation_id VARCHAR(64) NOT NULL REFERENCES observations(id) ON DELETE CASCADE,
    source_id VARCHAR(64) REFERENCES sources(id) ON DELETE SET NULL,
    object_ref_id VARCHAR(64) REFERENCES object_refs(id) ON DELETE SET NULL,
    evidence_type VARCHAR(32) NOT NULL,
    source_url TEXT,
    selector TEXT,
    text_start INTEGER,
    text_end INTEGER,
    page_number INTEGER,
    quoted_text TEXT,
    content_hash VARCHAR(64),
    captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata_json JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_evidence_obs ON evidence(observation_id);
CREATE INDEX IF NOT EXISTS idx_evidence_source ON evidence(source_id);
CREATE INDEX IF NOT EXISTS idx_evidence_obj ON evidence(object_ref_id);

CREATE TABLE IF NOT EXISTS facts (
    id VARCHAR(64) PRIMARY KEY,
    subject_type VARCHAR(32) NOT NULL,
    subject_id VARCHAR(64) NOT NULL,
    predicate VARCHAR(128) NOT NULL REFERENCES fact_predicates(predicate) ON DELETE CASCADE,
    value_type VARCHAR(32) NOT NULL,
    current_value_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    status VARCHAR(32) NOT NULL DEFAULT 'accepted',
    confidence REAL DEFAULT 1.0,
    verification_state VARCHAR(32) NOT NULL DEFAULT 'unverified',
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_verified_at TIMESTAMPTZ,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_to TIMESTAMPTZ,
    scope_type VARCHAR(32) NOT NULL DEFAULT 'global',
    scope_id VARCHAR(64) NOT NULL DEFAULT 'global',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata_json JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_facts_subject ON facts(subject_type, subject_id);
CREATE INDEX IF NOT EXISTS idx_facts_predicate ON facts(predicate);
CREATE INDEX IF NOT EXISTS idx_facts_status ON facts(status);
CREATE INDEX IF NOT EXISTS idx_facts_scope ON facts(scope_type, scope_id);

CREATE TABLE IF NOT EXISTS fact_values (
    id VARCHAR(64) PRIMARY KEY,
    fact_id VARCHAR(64) NOT NULL REFERENCES facts(id) ON DELETE CASCADE,
    value_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    value_type VARCHAR(32) NOT NULL,
    confidence REAL DEFAULT 1.0,
    status VARCHAR(32) NOT NULL DEFAULT 'accepted',
    valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_to TIMESTAMPTZ,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_verified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata_json JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_fact_values_fact ON fact_values(fact_id);
CREATE INDEX IF NOT EXISTS idx_fact_values_valid_from ON fact_values(valid_from);
CREATE INDEX IF NOT EXISTS idx_fact_values_valid_to ON fact_values(valid_to);

CREATE TABLE IF NOT EXISTS fact_evidence (
    fact_id VARCHAR(64) NOT NULL REFERENCES facts(id) ON DELETE CASCADE,
    observation_id VARCHAR(64) NOT NULL REFERENCES observations(id) ON DELETE CASCADE,
    support_type VARCHAR(32) NOT NULL DEFAULT 'supports',
    weight REAL DEFAULT 1.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (fact_id, observation_id)
);

CREATE INDEX IF NOT EXISTS idx_fact_evidence_obs ON fact_evidence(observation_id);

CREATE TABLE IF NOT EXISTS fact_conflicts (
    id VARCHAR(64) PRIMARY KEY,
    subject_type VARCHAR(32) NOT NULL,
    subject_id VARCHAR(64) NOT NULL,
    predicate VARCHAR(128) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'open',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolution_method VARCHAR(32),
    selected_fact_value_id VARCHAR(64) REFERENCES fact_values(id) ON DELETE SET NULL,
    metadata_json JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_fact_conflicts_subj ON fact_conflicts(subject_type, subject_id, predicate);
CREATE INDEX IF NOT EXISTS idx_fact_conflicts_status ON fact_conflicts(status);

CREATE TABLE IF NOT EXISTS observation_rejections (
    id VARCHAR(64) PRIMARY KEY,
    payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    reason_code VARCHAR(64) NOT NULL,
    source_id VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata_json JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_obs_rej_reason ON observation_rejections(reason_code);

CREATE TABLE IF NOT EXISTS fact_events (
    id VARCHAR(64) PRIMARY KEY,
    fact_id VARCHAR(64) NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    actor_type VARCHAR(32) DEFAULT 'system',
    actor_id VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fact_events_fact ON fact_events(fact_id);
CREATE INDEX IF NOT EXISTS idx_fact_events_type ON fact_events(event_type);

CREATE TABLE IF NOT EXISTS verification_policies (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(128) NOT NULL UNIQUE,
    subject_type VARCHAR(64) NOT NULL,
    version VARCHAR(32) NOT NULL DEFAULT 'v1',
    min_confidence DOUBLE PRECISION DEFAULT 0.80,
    required_checks JSONB DEFAULT '[]'::jsonb,
    ttl_hours INTEGER DEFAULT 168,
    config_json JSONB DEFAULT '{}'::jsonb,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS verification_runs (
    id VARCHAR(64) PRIMARY KEY,
    subject_type VARCHAR(64) NOT NULL,
    subject_id VARCHAR(128) NOT NULL,
    verification_type VARCHAR(64) NOT NULL,
    policy_id VARCHAR(64) NOT NULL,
    policy_version VARCHAR(32) NOT NULL DEFAULT 'v1',
    status VARCHAR(32) NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    valid_until TIMESTAMPTZ,
    error_code VARCHAR(64),
    metadata_json JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_ver_runs_subj ON verification_runs(subject_type, subject_id);
CREATE INDEX IF NOT EXISTS idx_ver_runs_status ON verification_runs(status);

CREATE TABLE IF NOT EXISTS verification_checks (
    id VARCHAR(64) PRIMARY KEY,
    verification_run_id VARCHAR(64) NOT NULL REFERENCES verification_runs(id) ON DELETE CASCADE,
    check_type VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL,
    score DOUBLE PRECISION NOT NULL,
    reason_code VARCHAR(64) NOT NULL,
    evidence_ids JSONB DEFAULT '[]'::jsonb,
    duration_ms INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata_json JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_ver_checks_run ON verification_checks(verification_run_id);

CREATE TABLE IF NOT EXISTS verification_state (
    subject_type VARCHAR(64) NOT NULL,
    subject_id VARCHAR(128) NOT NULL,
    verification_type VARCHAR(64) NOT NULL,
    latest_run_id VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    last_verified_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_until TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata_json JSONB DEFAULT '{}'::jsonb,
    PRIMARY KEY (subject_type, subject_id, verification_type)
);

CREATE INDEX IF NOT EXISTS idx_ver_state_lookup ON verification_state(subject_type, subject_id);

CREATE TABLE IF NOT EXISTS model_runs (
    id VARCHAR(64) PRIMARY KEY,
    task VARCHAR(128) NOT NULL,
    provider VARCHAR(64) NOT NULL,
    model VARCHAR(128) NOT NULL,
    prompt_id VARCHAR(128),
    prompt_version VARCHAR(32) NOT NULL DEFAULT 'v1',
    quality_tier VARCHAR(32) NOT NULL DEFAULT 'standard',
    input_hash VARCHAR(64),
    output_hash VARCHAR(64),
    status VARCHAR(32) NOT NULL,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    estimated_cost DOUBLE PRECISION DEFAULT 0.0,
    latency_ms INTEGER DEFAULT 0,
    fallback_used BOOLEAN DEFAULT FALSE,
    fallback_reason TEXT,
    cache_hit BOOLEAN DEFAULT FALSE,
    error_code VARCHAR(64),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    metadata_json JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_model_runs_task ON model_runs(task);
CREATE INDEX IF NOT EXISTS idx_model_runs_prov_model ON model_runs(provider, model);
CREATE INDEX IF NOT EXISTS idx_model_runs_started ON model_runs(started_at);

CREATE TABLE IF NOT EXISTS ai_cost_profiles (
    id VARCHAR(64) PRIMARY KEY,
    provider VARCHAR(64) NOT NULL,
    model VARCHAR(128) NOT NULL,
    input_unit_cost DOUBLE PRECISION NOT NULL,
    output_unit_cost DOUBLE PRECISION NOT NULL,
    effective_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    effective_to TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ai_evaluations (
    id VARCHAR(64) PRIMARY KEY,
    task VARCHAR(128) NOT NULL,
    dataset_version VARCHAR(32) NOT NULL DEFAULT 'v1',
    candidate_config TEXT NOT NULL,
    score_json JSONB DEFAULT '{}'::jsonb,
    cost DOUBLE PRECISION DEFAULT 0.0,
    latency_ms INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ai_evals_task ON ai_evaluations(task);

CREATE TABLE IF NOT EXISTS quality_policies (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(128) NOT NULL UNIQUE,
    gate_type VARCHAR(64) NOT NULL,
    profile VARCHAR(64) NOT NULL,
    version VARCHAR(32) NOT NULL DEFAULT 'v1',
    min_score DOUBLE PRECISION DEFAULT 0.70,
    rules_config JSONB DEFAULT '{}'::jsonb,
    ttl_hours INTEGER DEFAULT 168,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS quality_results (
    id VARCHAR(64) PRIMARY KEY,
    subject_type VARCHAR(64) NOT NULL,
    subject_id VARCHAR(128) NOT NULL,
    gate_type VARCHAR(64) NOT NULL,
    profile VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL,
    score DOUBLE PRECISION NOT NULL,
    policy_id VARCHAR(64) NOT NULL,
    policy_version VARCHAR(32) NOT NULL DEFAULT 'v1',
    reasons JSONB DEFAULT '[]'::jsonb,
    required_actions JSONB DEFAULT '[]'::jsonb,
    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_until TIMESTAMPTZ,
    metadata_json JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_qual_res_subject ON quality_results(subject_type, subject_id);
CREATE INDEX IF NOT EXISTS idx_qual_res_gate ON quality_results(gate_type);

CREATE TABLE IF NOT EXISTS quality_rule_results (
    id VARCHAR(64) PRIMARY KEY,
    quality_result_id VARCHAR(64) NOT NULL REFERENCES quality_results(id) ON DELETE CASCADE,
    rule_name VARCHAR(128) NOT NULL,
    rule_type VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL,
    score_delta DOUBLE PRECISION DEFAULT 0.0,
    reason_code VARCHAR(128) NOT NULL,
    details_json JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_qual_rule_res ON quality_rule_results(quality_result_id);

CREATE TABLE IF NOT EXISTS quality_state (
    subject_type VARCHAR(64) NOT NULL,
    subject_id VARCHAR(128) NOT NULL,
    gate_type VARCHAR(64) NOT NULL,
    latest_result_id VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL,
    score DOUBLE PRECISION NOT NULL,
    valid_until TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (subject_type, subject_id, gate_type)
);

CREATE TABLE IF NOT EXISTS quality_quarantine (
    id VARCHAR(64) PRIMARY KEY,
    subject_type VARCHAR(64) NOT NULL,
    candidate_payload_json JSONB NOT NULL,
    reason_codes JSONB DEFAULT '[]'::jsonb,
    source_id VARCHAR(128),
    status VARCHAR(32) DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata_json JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS prospect_quality_snapshots (
    prospect_id VARCHAR(128) PRIMARY KEY,
    company_score DOUBLE PRECISION DEFAULT 0.0,
    person_score DOUBLE PRECISION DEFAULT 0.0,
    employment_score DOUBLE PRECISION DEFAULT 0.0,
    email_score DOUBLE PRECISION DEFAULT 0.0,
    personalization_score DOUBLE PRECISION DEFAULT 0.0,
    outreach_score DOUBLE PRECISION DEFAULT 0.0,
    overall_status VARCHAR(32) NOT NULL,
    reasons JSONB DEFAULT '[]'::jsonb,
    required_actions JSONB DEFAULT '[]'::jsonb,
    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


def init_pg_schema(conn) -> None:
    """
    Executes Phase 01 DDL migration on PostgreSQL/Supabase database connection.
    """
    with conn.cursor() as cur:
        cur.execute(PG_SCHEMA_SQL)
    conn.commit()
    logger.info("Initialized Phase 01 Canonical PostgreSQL Schema successfully.")
