import json
import logging
import sqlite3
from typing import Any, Dict, List, Optional
from growx_crawl.storage.base import (
    BaseCompanyRepository,
    BaseCrawlJobRepository,
    BaseCrawlRunRepository,
    BaseDomainRepository,
    BaseEmploymentRepository,
    BasePersonRepository,
    BaseSourceRepository,
)
from growx_crawl.storage.db import get_db
from growx_crawl.storage.entities import (
    CompanyAliasEntity,
    CompanyDomainEntity,
    CompanyEntity,
    CrawlJobEntity,
    CrawlRunEntity,
    DomainEntity,
    EmploymentEntity,
    PersonEntity,
    SourceEntity,
)

logger = logging.getLogger("growx_crawl.storage.sqlite.canonical")

SQLITE_CANONICAL_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS canonical_domains (
    id TEXT PRIMARY KEY,
    registrable_domain TEXT NOT NULL,
    hostname TEXT NOT NULL,
    normalized_domain TEXT UNIQUE NOT NULL,
    scheme TEXT DEFAULT 'https',
    status TEXT DEFAULT 'active',
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    last_crawled_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata_json TEXT DEFAULT '{}'
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_canon_domains_norm ON canonical_domains(normalized_domain);

CREATE TABLE IF NOT EXISTS canonical_companies (
    id TEXT PRIMARY KEY,
    canonical_name TEXT NOT NULL,
    legal_name TEXT,
    normalized_name TEXT NOT NULL,
    primary_domain_id TEXT,
    industry TEXT,
    employee_range TEXT,
    country_code TEXT,
    summary TEXT,
    status TEXT DEFAULT 'active',
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    last_crawled_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata_json TEXT DEFAULT '{}',
    FOREIGN KEY (primary_domain_id) REFERENCES canonical_domains(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_canon_companies_norm ON canonical_companies(normalized_name);
CREATE INDEX IF NOT EXISTS idx_canon_companies_seen ON canonical_companies(last_seen_at);

CREATE TABLE IF NOT EXISTS canonical_company_domains (
    company_id TEXT NOT NULL,
    domain_id TEXT NOT NULL,
    relationship_type TEXT DEFAULT 'primary',
    confidence REAL DEFAULT 1.0,
    is_primary INTEGER DEFAULT 1,
    first_seen_at TEXT NOT NULL,
    last_verified_at TEXT,
    PRIMARY KEY (company_id, domain_id),
    FOREIGN KEY (company_id) REFERENCES canonical_companies(id) ON DELETE CASCADE,
    FOREIGN KEY (domain_id) REFERENCES canonical_domains(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS canonical_company_aliases (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    alias TEXT NOT NULL,
    normalized_alias TEXT NOT NULL,
    source_id TEXT,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    FOREIGN KEY (company_id) REFERENCES canonical_companies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS canonical_people (
    id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    headline TEXT,
    location_text TEXT,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata_json TEXT DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_canon_people_norm ON canonical_people(normalized_name);

CREATE TABLE IF NOT EXISTS canonical_employments (
    id TEXT PRIMARY KEY,
    person_id TEXT NOT NULL,
    company_id TEXT NOT NULL,
    title TEXT NOT NULL,
    normalized_title TEXT NOT NULL,
    department TEXT,
    seniority TEXT,
    is_current INTEGER DEFAULT 1,
    source_id TEXT,
    confidence REAL DEFAULT 1.0,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    last_verified_at TEXT,
    FOREIGN KEY (person_id) REFERENCES canonical_people(id) ON DELETE CASCADE,
    FOREIGN KEY (company_id) REFERENCES canonical_companies(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_canon_emp_person ON canonical_employments(person_id);
CREATE INDEX IF NOT EXISTS idx_canon_emp_comp ON canonical_employments(company_id);

CREATE TABLE IF NOT EXISTS canonical_sources (
    id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    url TEXT NOT NULL,
    domain_id TEXT,
    content_hash TEXT,
    observed_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    metadata_json TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS canonical_crawl_jobs (
    id TEXT PRIMARY KEY,
    target TEXT NOT NULL,
    status TEXT NOT NULL,
    config_json TEXT DEFAULT '{}',
    started_at TEXT,
    completed_at TEXT,
    attempts INTEGER DEFAULT 1,
    error_code TEXT,
    error_message TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS canonical_crawl_runs (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    target_url TEXT NOT NULL,
    domain_id TEXT,
    fetcher_type TEXT NOT NULL,
    http_status INTEGER,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    duration_ms INTEGER,
    page_count INTEGER DEFAULT 1,
    success INTEGER DEFAULT 1,
    error_code TEXT,
    metadata_json TEXT DEFAULT '{}',
    FOREIGN KEY (job_id) REFERENCES canonical_crawl_jobs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS canonical_object_refs (
    id TEXT PRIMARY KEY,
    object_type TEXT NOT NULL,
    bucket TEXT NOT NULL,
    object_key TEXT NOT NULL,
    provider TEXT NOT NULL,
    content_type TEXT NOT NULL,
    content_encoding TEXT,
    content_hash TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    source_url TEXT,
    company_id TEXT,
    domain_id TEXT,
    crawl_run_id TEXT,
    created_at TEXT NOT NULL,
    metadata_json TEXT DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_canon_obj_key ON canonical_object_refs(object_key);
CREATE INDEX IF NOT EXISTS idx_canon_obj_hash ON canonical_object_refs(content_hash);
CREATE INDEX IF NOT EXISTS idx_canon_obj_run ON canonical_object_refs(crawl_run_id);

-- Phase 03 Canonical Entity Identity Expansion SQLite Tables

CREATE TABLE IF NOT EXISTS canonical_locations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    city TEXT,
    region TEXT,
    country_code TEXT,
    postal_code TEXT,
    latitude REAL,
    longitude REAL,
    location_type TEXT DEFAULT 'office',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata_json TEXT DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_canon_loc_norm ON canonical_locations(normalized_name);
CREATE INDEX IF NOT EXISTS idx_canon_loc_country ON canonical_locations(country_code);

CREATE TABLE IF NOT EXISTS canonical_company_locations (
    company_id TEXT NOT NULL,
    location_id TEXT NOT NULL,
    relationship_type TEXT DEFAULT 'office',
    is_primary INTEGER DEFAULT 1,
    confidence REAL DEFAULT 1.0,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    last_verified_at TEXT,
    PRIMARY KEY (company_id, location_id),
    FOREIGN KEY (company_id) REFERENCES canonical_companies(id) ON DELETE CASCADE,
    FOREIGN KEY (location_id) REFERENCES canonical_locations(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_canon_comp_loc_comp ON canonical_company_locations(company_id);
CREATE INDEX IF NOT EXISTS idx_canon_comp_loc_loc ON canonical_company_locations(location_id);

CREATE TABLE IF NOT EXISTS canonical_brands (
    id TEXT PRIMARY KEY,
    canonical_name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    company_id TEXT NOT NULL,
    primary_domain_id TEXT,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata_json TEXT DEFAULT '{}',
    FOREIGN KEY (company_id) REFERENCES canonical_companies(id) ON DELETE CASCADE,
    FOREIGN KEY (primary_domain_id) REFERENCES canonical_domains(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_canon_brands_comp ON canonical_brands(company_id);
CREATE INDEX IF NOT EXISTS idx_canon_brands_norm ON canonical_brands(normalized_name);

CREATE TABLE IF NOT EXISTS canonical_person_aliases (
    id TEXT PRIMARY KEY,
    person_id TEXT NOT NULL,
    alias TEXT NOT NULL,
    normalized_alias TEXT NOT NULL,
    alias_type TEXT DEFAULT 'name_variant',
    source_id TEXT,
    confidence REAL DEFAULT 1.0,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    FOREIGN KEY (person_id) REFERENCES canonical_people(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_canon_person_alias_per ON canonical_person_aliases(person_id);
CREATE INDEX IF NOT EXISTS idx_canon_person_alias_norm ON canonical_person_aliases(normalized_alias);

CREATE TABLE IF NOT EXISTS canonical_company_relationships (
    id TEXT PRIMARY KEY,
    from_company_id TEXT NOT NULL,
    to_company_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    source_id TEXT,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    last_verified_at TEXT,
    metadata_json TEXT DEFAULT '{}',
    FOREIGN KEY (from_company_id) REFERENCES canonical_companies(id) ON DELETE CASCADE,
    FOREIGN KEY (to_company_id) REFERENCES canonical_companies(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_canon_rel_from ON canonical_company_relationships(from_company_id);
CREATE INDEX IF NOT EXISTS idx_canon_rel_to ON canonical_company_relationships(to_company_id);

CREATE TABLE IF NOT EXISTS canonical_external_identities (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    external_id TEXT NOT NULL,
    external_url TEXT,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    metadata_json TEXT DEFAULT '{}',
    UNIQUE (provider, external_id)
);

CREATE INDEX IF NOT EXISTS idx_canon_ext_ident ON canonical_external_identities(entity_type, entity_id);

CREATE TABLE IF NOT EXISTS canonical_identity_keys (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    key_type TEXT NOT NULL,
    key_value TEXT NOT NULL,
    is_unique INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    last_verified_at TEXT,
    UNIQUE (key_type, key_value)
);

CREATE INDEX IF NOT EXISTS idx_canon_ident_keys ON canonical_identity_keys(entity_type, entity_id);

CREATE TABLE IF NOT EXISTS canonical_identity_candidates (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    candidate_payload_json TEXT NOT NULL DEFAULT '{}',
    candidate_key TEXT NOT NULL,
    source_id TEXT,
    status TEXT DEFAULT 'pending',
    created_at TEXT NOT NULL,
    resolved_at TEXT,
    resolved_entity_id TEXT,
    metadata_json TEXT DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_canon_cand_status ON canonical_identity_candidates(status);
CREATE INDEX IF NOT EXISTS idx_canon_cand_key ON canonical_identity_candidates(candidate_key);

CREATE TABLE IF NOT EXISTS canonical_entity_merges (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    source_entity_id TEXT NOT NULL,
    target_entity_id TEXT NOT NULL,
    reason TEXT NOT NULL,
    method TEXT DEFAULT 'manual',
    confidence REAL DEFAULT 1.0,
    created_at TEXT NOT NULL,
    created_by TEXT DEFAULT 'system',
    metadata_json TEXT DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_canon_merge_src ON canonical_entity_merges(source_entity_id);
CREATE INDEX IF NOT EXISTS idx_canon_merge_tgt ON canonical_entity_merges(target_entity_id);

CREATE TABLE IF NOT EXISTS canonical_identity_events (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    source_id TEXT,
    created_at TEXT NOT NULL,
    actor_type TEXT DEFAULT 'system',
    actor_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_canon_evt_entity ON canonical_identity_events(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_canon_evt_type ON canonical_identity_events(event_type);
"""


def init_sqlite_canonical_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(SQLITE_CANONICAL_SCHEMA_SQL)


class SqliteCompanyRepository(BaseCompanyRepository):
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def _ensure_schema(self, conn: sqlite3.Connection):
        init_sqlite_canonical_tables(conn)

    def get(self, company_id: str) -> Optional[CompanyEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute("SELECT * FROM canonical_companies WHERE id = ?", (company_id,)).fetchone()
            return self._row_to_entity(row) if row else None

    def get_by_normalized_name(self, normalized_name: str) -> Optional[CompanyEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute(
                "SELECT * FROM canonical_companies WHERE normalized_name = ? ORDER BY last_seen_at DESC LIMIT 1",
                (normalized_name,),
            ).fetchone()
            return self._row_to_entity(row) if row else None

    def get_by_domain(self, domain: str) -> Optional[CompanyEntity]:
        clean = domain.strip().lower().replace("http://", "").replace("https://", "").split("/")[0]
        if clean.startswith("www."):
            clean = clean[4:]
        sql = """
            SELECT c.* FROM canonical_companies c
            JOIN canonical_company_domains cd ON c.id = cd.company_id
            JOIN canonical_domains d ON cd.domain_id = d.id
            WHERE d.normalized_domain = ?
            ORDER BY cd.is_primary DESC, cd.confidence DESC LIMIT 1;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute(sql, (clean,)).fetchone()
            return self._row_to_entity(row) if row else None

    def upsert(self, company: CompanyEntity) -> CompanyEntity:
        sql = """
            INSERT INTO canonical_companies (
                id, canonical_name, legal_name, normalized_name, primary_domain_id,
                industry, employee_range, country_code, summary, status,
                first_seen_at, last_seen_at, last_crawled_at, created_at, updated_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET
                canonical_name = excluded.canonical_name,
                legal_name = coalesce(excluded.legal_name, canonical_companies.legal_name),
                normalized_name = excluded.normalized_name,
                primary_domain_id = coalesce(excluded.primary_domain_id, canonical_companies.primary_domain_id),
                industry = coalesce(excluded.industry, canonical_companies.industry),
                employee_range = coalesce(excluded.employee_range, canonical_companies.employee_range),
                country_code = coalesce(excluded.country_code, canonical_companies.country_code),
                summary = coalesce(excluded.summary, canonical_companies.summary),
                status = excluded.status,
                last_seen_at = excluded.last_seen_at,
                last_crawled_at = coalesce(excluded.last_crawled_at, canonical_companies.last_crawled_at),
                updated_at = excluded.updated_at,
                metadata_json = excluded.metadata_json;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    company.id,
                    company.canonical_name,
                    company.legal_name,
                    company.normalized_name,
                    company.primary_domain_id,
                    company.industry,
                    company.employee_range,
                    company.country_code,
                    company.summary,
                    company.status,
                    company.first_seen_at,
                    company.last_seen_at,
                    company.last_crawled_at,
                    company.created_at,
                    company.updated_at,
                    json.dumps(company.metadata_json),
                ),
            )
        return company

    def list(self, limit: int = 50, offset: int = 0) -> List[CompanyEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(
                "SELECT * FROM canonical_companies ORDER BY updated_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
            return [self._row_to_entity(r) for r in rows]

    def count(self) -> int:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            return conn.execute("SELECT COUNT(*) FROM canonical_companies;").fetchone()[0]

    def add_alias(self, alias: CompanyAliasEntity) -> CompanyAliasEntity:
        sql = """
            INSERT INTO canonical_company_aliases (id, company_id, alias, normalized_alias, source_id, first_seen_at, last_seen_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET
                alias = excluded.alias,
                normalized_alias = excluded.normalized_alias,
                last_seen_at = excluded.last_seen_at;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    alias.id,
                    alias.company_id,
                    alias.alias,
                    alias.normalized_alias,
                    alias.source_id,
                    alias.first_seen_at,
                    alias.last_seen_at,
                ),
            )
        return alias

    def link_domain(self, link: CompanyDomainEntity) -> CompanyDomainEntity:
        sql = """
            INSERT INTO canonical_company_domains (company_id, domain_id, relationship_type, confidence, is_primary, first_seen_at, last_verified_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (company_id, domain_id) DO UPDATE SET
                relationship_type = excluded.relationship_type,
                confidence = excluded.confidence,
                is_primary = excluded.is_primary,
                last_verified_at = excluded.last_verified_at;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    link.company_id,
                    link.domain_id,
                    link.relationship_type,
                    link.confidence,
                    1 if link.is_primary else 0,
                    link.first_seen_at,
                    link.last_verified_at,
                ),
            )
        return link

    def _row_to_entity(self, r) -> CompanyEntity:
        meta = r["metadata_json"]
        if isinstance(meta, str):
            meta = json.loads(meta)
        return CompanyEntity(
            id=r["id"],
            canonical_name=r["canonical_name"],
            legal_name=r["legal_name"],
            normalized_name=r["normalized_name"],
            primary_domain_id=r["primary_domain_id"],
            industry=r["industry"],
            employee_range=r["employee_range"],
            country_code=r["country_code"],
            summary=r["summary"],
            status=r["status"],
            first_seen_at=r["first_seen_at"],
            last_seen_at=r["last_seen_at"],
            last_crawled_at=r["last_crawled_at"],
            created_at=r["created_at"],
            updated_at=r["updated_at"],
            metadata_json=meta or {},
        )


class SqliteDomainRepository(BaseDomainRepository):
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def _ensure_schema(self, conn: sqlite3.Connection):
        init_sqlite_canonical_tables(conn)

    def get(self, domain_id: str) -> Optional[DomainEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute("SELECT * FROM canonical_domains WHERE id = ?", (domain_id,)).fetchone()
            return self._row_to_entity(row) if row else None

    def get_by_normalized_domain(self, normalized_domain: str) -> Optional[DomainEntity]:
        clean = normalized_domain.strip().lower().replace("www.", "")
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute("SELECT * FROM canonical_domains WHERE normalized_domain = ?", (clean,)).fetchone()
            return self._row_to_entity(row) if row else None

    def upsert(self, domain: DomainEntity) -> DomainEntity:
        sql = """
            INSERT INTO canonical_domains (
                id, registrable_domain, hostname, normalized_domain, scheme, status,
                first_seen_at, last_seen_at, last_crawled_at, created_at, updated_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (normalized_domain) DO UPDATE SET
                registrable_domain = excluded.registrable_domain,
                hostname = excluded.hostname,
                scheme = excluded.scheme,
                status = excluded.status,
                last_seen_at = excluded.last_seen_at,
                last_crawled_at = coalesce(excluded.last_crawled_at, canonical_domains.last_crawled_at),
                updated_at = excluded.updated_at,
                metadata_json = excluded.metadata_json;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    domain.id,
                    domain.registrable_domain,
                    domain.hostname,
                    domain.normalized_domain,
                    domain.scheme,
                    domain.status,
                    domain.first_seen_at,
                    domain.last_seen_at,
                    domain.last_crawled_at,
                    domain.created_at,
                    domain.updated_at,
                    json.dumps(domain.metadata_json),
                ),
            )
            existing = conn.execute("SELECT id FROM canonical_domains WHERE normalized_domain = ?", (domain.normalized_domain,)).fetchone()
            if existing:
                domain.id = existing["id"]
        return domain

    def list(self, limit: int = 50, offset: int = 0) -> List[DomainEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(
                "SELECT * FROM canonical_domains ORDER BY updated_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
            return [self._row_to_entity(r) for r in rows]

    def count(self) -> int:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            return conn.execute("SELECT COUNT(*) FROM canonical_domains;").fetchone()[0]

    def _row_to_entity(self, r) -> DomainEntity:
        meta = r["metadata_json"]
        if isinstance(meta, str):
            meta = json.loads(meta)
        return DomainEntity(
            id=r["id"],
            registrable_domain=r["registrable_domain"],
            hostname=r["hostname"],
            normalized_domain=r["normalized_domain"],
            scheme=r["scheme"],
            status=r["status"],
            first_seen_at=r["first_seen_at"],
            last_seen_at=r["last_seen_at"],
            last_crawled_at=r["last_crawled_at"],
            created_at=r["created_at"],
            updated_at=r["updated_at"],
            metadata_json=meta or {},
        )


class SqlitePersonRepository(BasePersonRepository):
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def _ensure_schema(self, conn: sqlite3.Connection):
        init_sqlite_canonical_tables(conn)

    def get(self, person_id: str) -> Optional[PersonEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute("SELECT * FROM canonical_people WHERE id = ?", (person_id,)).fetchone()
            return self._row_to_entity(row) if row else None

    def get_by_normalized_name(self, normalized_name: str) -> Optional[PersonEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute(
                "SELECT * FROM canonical_people WHERE normalized_name = ? ORDER BY last_seen_at DESC LIMIT 1",
                (normalized_name,),
            ).fetchone()
            return self._row_to_entity(row) if row else None

    def upsert(self, person: PersonEntity) -> PersonEntity:
        sql = """
            INSERT INTO canonical_people (
                id, full_name, normalized_name, first_name, last_name, headline, location_text,
                first_seen_at, last_seen_at, created_at, updated_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET
                full_name = excluded.full_name,
                normalized_name = excluded.normalized_name,
                first_name = coalesce(excluded.first_name, canonical_people.first_name),
                last_name = coalesce(excluded.last_name, canonical_people.last_name),
                headline = coalesce(excluded.headline, canonical_people.headline),
                location_text = coalesce(excluded.location_text, canonical_people.location_text),
                last_seen_at = excluded.last_seen_at,
                updated_at = excluded.updated_at,
                metadata_json = excluded.metadata_json;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    person.id,
                    person.full_name,
                    person.normalized_name,
                    person.first_name,
                    person.last_name,
                    person.headline,
                    person.location_text,
                    person.first_seen_at,
                    person.last_seen_at,
                    person.created_at,
                    person.updated_at,
                    json.dumps(person.metadata_json),
                ),
            )
        return person

    def list(self, limit: int = 50, offset: int = 0) -> List[PersonEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(
                "SELECT * FROM canonical_people ORDER BY updated_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
            return [self._row_to_entity(r) for r in rows]

    def count(self) -> int:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            return conn.execute("SELECT COUNT(*) FROM canonical_people;").fetchone()[0]

    def _row_to_entity(self, r) -> PersonEntity:
        meta = r["metadata_json"]
        if isinstance(meta, str):
            meta = json.loads(meta)
        return PersonEntity(
            id=r["id"],
            full_name=r["full_name"],
            normalized_name=r["normalized_name"],
            first_name=r["first_name"],
            last_name=r["last_name"],
            headline=r["headline"],
            location_text=r["location_text"],
            first_seen_at=r["first_seen_at"],
            last_seen_at=r["last_seen_at"],
            created_at=r["created_at"],
            updated_at=r["updated_at"],
            metadata_json=meta or {},
        )


class SqliteEmploymentRepository(BaseEmploymentRepository):
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def _ensure_schema(self, conn: sqlite3.Connection):
        init_sqlite_canonical_tables(conn)

    def get(self, employment_id: str) -> Optional[EmploymentEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute("SELECT * FROM canonical_employments WHERE id = ?", (employment_id,)).fetchone()
            return self._row_to_entity(row) if row else None

    def upsert(self, employment: EmploymentEntity) -> EmploymentEntity:
        sql = """
            INSERT INTO canonical_employments (
                id, person_id, company_id, title, normalized_title, department, seniority,
                is_current, source_id, confidence, first_seen_at, last_seen_at, last_verified_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET
                title = excluded.title,
                normalized_title = excluded.normalized_title,
                department = coalesce(excluded.department, canonical_employments.department),
                seniority = coalesce(excluded.seniority, canonical_employments.seniority),
                is_current = excluded.is_current,
                confidence = excluded.confidence,
                last_seen_at = excluded.last_seen_at,
                last_verified_at = coalesce(excluded.last_verified_at, canonical_employments.last_verified_at);
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    employment.id,
                    employment.person_id,
                    employment.company_id,
                    employment.title,
                    employment.normalized_title,
                    employment.department,
                    employment.seniority,
                    1 if employment.is_current else 0,
                    employment.source_id,
                    employment.confidence,
                    employment.first_seen_at,
                    employment.last_seen_at,
                    employment.last_verified_at,
                ),
            )
        return employment

    def list_by_company(self, company_id: str) -> List[EmploymentEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(
                "SELECT * FROM canonical_employments WHERE company_id = ? ORDER BY is_current DESC, confidence DESC",
                (company_id,),
            ).fetchall()
            return [self._row_to_entity(r) for r in rows]

    def list_by_person(self, person_id: str) -> List[EmploymentEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(
                "SELECT * FROM canonical_employments WHERE person_id = ? ORDER BY is_current DESC",
                (person_id,),
            ).fetchall()
            return [self._row_to_entity(r) for r in rows]

    def count(self) -> int:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            return conn.execute("SELECT COUNT(*) FROM canonical_employments;").fetchone()[0]

    def _row_to_entity(self, r) -> EmploymentEntity:
        return EmploymentEntity(
            id=r["id"],
            person_id=r["person_id"],
            company_id=r["company_id"],
            title=r["title"],
            normalized_title=r["normalized_title"],
            department=r["department"],
            seniority=r["seniority"],
            is_current=bool(r["is_current"]),
            source_id=r["source_id"],
            confidence=float(r["confidence"]),
            first_seen_at=r["first_seen_at"],
            last_seen_at=r["last_seen_at"],
            last_verified_at=r["last_verified_at"],
        )


class SqliteSourceRepository(BaseSourceRepository):
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def _ensure_schema(self, conn: sqlite3.Connection):
        init_sqlite_canonical_tables(conn)

    def get(self, source_id: str) -> Optional[SourceEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute("SELECT * FROM canonical_sources WHERE id = ?", (source_id,)).fetchone()
            return self._row_to_entity(row) if row else None

    def get_by_url(self, url: str) -> Optional[SourceEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute("SELECT * FROM canonical_sources WHERE url = ? LIMIT 1", (url,)).fetchone()
            return self._row_to_entity(row) if row else None

    def upsert(self, source: SourceEntity) -> SourceEntity:
        sql = """
            INSERT INTO canonical_sources (id, source_type, url, domain_id, content_hash, observed_at, created_at, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET
                observed_at = excluded.observed_at,
                content_hash = coalesce(excluded.content_hash, canonical_sources.content_hash),
                metadata_json = excluded.metadata_json;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    source.id,
                    source.source_type,
                    source.url,
                    source.domain_id,
                    source.content_hash,
                    source.observed_at,
                    source.created_at,
                    json.dumps(source.metadata_json),
                ),
            )
        return source

    def count(self) -> int:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            return conn.execute("SELECT COUNT(*) FROM canonical_sources;").fetchone()[0]

    def _row_to_entity(self, r) -> SourceEntity:
        meta = r["metadata_json"]
        if isinstance(meta, str):
            meta = json.loads(meta)
        return SourceEntity(
            id=r["id"],
            source_type=r["source_type"],
            url=r["url"],
            domain_id=r["domain_id"],
            content_hash=r["content_hash"],
            observed_at=r["observed_at"],
            created_at=r["created_at"],
            metadata_json=meta or {},
        )


class SqliteCrawlJobRepository(BaseCrawlJobRepository):
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def _ensure_schema(self, conn: sqlite3.Connection):
        init_sqlite_canonical_tables(conn)

    def get(self, job_id: str) -> Optional[CrawlJobEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute("SELECT * FROM canonical_crawl_jobs WHERE id = ?", (job_id,)).fetchone()
            return self._row_to_entity(row) if row else None

    def upsert(self, job: CrawlJobEntity) -> CrawlJobEntity:
        sql = """
            INSERT INTO canonical_crawl_jobs (id, target, status, config_json, started_at, completed_at, attempts, error_code, error_message, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET
                status = excluded.status,
                started_at = coalesce(excluded.started_at, canonical_crawl_jobs.started_at),
                completed_at = coalesce(excluded.completed_at, canonical_crawl_jobs.completed_at),
                attempts = excluded.attempts,
                error_code = excluded.error_code,
                error_message = excluded.error_message,
                updated_at = excluded.updated_at,
                config_json = excluded.config_json;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    job.id,
                    job.target,
                    job.status,
                    json.dumps(job.config_json),
                    job.started_at,
                    job.completed_at,
                    job.attempts,
                    job.error_code,
                    job.error_message,
                    job.created_at,
                    job.updated_at,
                ),
            )
        return job

    def list(self, limit: int = 50, offset: int = 0) -> List[CrawlJobEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(
                "SELECT * FROM canonical_crawl_jobs ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
            return [self._row_to_entity(r) for r in rows]

    def count(self) -> int:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            return conn.execute("SELECT COUNT(*) FROM canonical_crawl_jobs;").fetchone()[0]

    def _row_to_entity(self, r) -> CrawlJobEntity:
        cfg = r["config_json"]
        if isinstance(cfg, str):
            cfg = json.loads(cfg)
        return CrawlJobEntity(
            id=r["id"],
            target=r["target"],
            status=r["status"],
            config_json=cfg or {},
            started_at=r["started_at"],
            completed_at=r["completed_at"],
            attempts=int(r["attempts"]),
            error_code=r["error_code"],
            error_message=r["error_message"],
            created_at=r["created_at"],
            updated_at=r["updated_at"],
        )


class SqliteCrawlRunRepository(BaseCrawlRunRepository):
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def _ensure_schema(self, conn: sqlite3.Connection):
        init_sqlite_canonical_tables(conn)

    def get(self, run_id: str) -> Optional[CrawlRunEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute("SELECT * FROM canonical_crawl_runs WHERE id = ?", (run_id,)).fetchone()
            return self._row_to_entity(row) if row else None

    def create(self, run: CrawlRunEntity) -> CrawlRunEntity:
        sql = """
            INSERT INTO canonical_crawl_runs (id, job_id, target_url, domain_id, fetcher_type, http_status, started_at, completed_at, duration_ms, page_count, success, error_code, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO NOTHING;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    run.id,
                    run.job_id,
                    run.target_url,
                    run.domain_id,
                    run.fetcher_type,
                    run.http_status,
                    run.started_at,
                    run.completed_at,
                    run.duration_ms,
                    run.page_count,
                    1 if run.success else 0,
                    run.error_code,
                    json.dumps(run.metadata_json),
                ),
            )
        return run

    def list_by_job(self, job_id: str) -> List[CrawlRunEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(
                "SELECT * FROM canonical_crawl_runs WHERE job_id = ? ORDER BY started_at DESC",
                (job_id,),
            ).fetchall()
            return [self._row_to_entity(r) for r in rows]

    def count(self) -> int:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            return conn.execute("SELECT COUNT(*) FROM canonical_crawl_runs;").fetchone()[0]

    def _row_to_entity(self, r) -> CrawlRunEntity:
        meta = r["metadata_json"]
        if isinstance(meta, str):
            meta = json.loads(meta)
        return CrawlRunEntity(
            id=r["id"],
            job_id=r["job_id"],
            target_url=r["target_url"],
            domain_id=r["domain_id"],
            fetcher_type=r["fetcher_type"],
            http_status=r["http_status"],
            started_at=r["started_at"],
            completed_at=r["completed_at"],
            duration_ms=r["duration_ms"],
            page_count=int(r["page_count"]),
            success=bool(r["success"]),
            error_code=r["error_code"],
            metadata_json=meta or {},
        )


class SqliteObjectRefRepository:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def _ensure_schema(self, conn: sqlite3.Connection):
        init_sqlite_canonical_tables(conn)

    def get(self, object_id: str) -> Optional[Any]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute("SELECT * FROM canonical_object_refs WHERE id = ?", (object_id,)).fetchone()
            return dict(row) if row else None

    def get_by_key(self, bucket: str, object_key: str) -> Optional[Any]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute(
                "SELECT * FROM canonical_object_refs WHERE bucket = ? AND object_key = ?",
                (bucket, object_key),
            ).fetchone()
            return dict(row) if row else None

    def upsert(self, ref: Any) -> Any:
        sql = """
            INSERT INTO canonical_object_refs (
                id, object_type, bucket, object_key, provider, content_type,
                content_encoding, content_hash, size_bytes, source_url,
                company_id, domain_id, crawl_run_id, created_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET
                content_hash = excluded.content_hash,
                size_bytes = excluded.size_bytes,
                metadata_json = excluded.metadata_json;
        """
        ref_dict = ref.model_dump() if hasattr(ref, "model_dump") else dict(ref)
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    ref_dict["id"],
                    ref_dict["object_type"],
                    ref_dict["bucket"],
                    ref_dict["object_key"],
                    ref_dict["provider"],
                    ref_dict["content_type"],
                    ref_dict.get("content_encoding"),
                    ref_dict["content_hash"],
                    ref_dict["size_bytes"],
                    ref_dict.get("source_url"),
                    ref_dict.get("company_id"),
                    ref_dict.get("domain_id"),
                    ref_dict.get("crawl_run_id"),
                    ref_dict["created_at"],
                    json.dumps(ref_dict.get("metadata_json", {})),
                ),
            )
        return ref

    def list_by_run(self, run_id: str) -> List[Any]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(
                "SELECT * FROM canonical_object_refs WHERE crawl_run_id = ? ORDER BY created_at DESC",
                (run_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def count(self) -> int:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            return conn.execute("SELECT COUNT(*) FROM canonical_object_refs;").fetchone()[0]

