import json
import logging
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
from growx_crawl.storage.postgres.db import get_pg_connection

logger = logging.getLogger("growx_crawl.storage.postgres.repository")


class PostgresCompanyRepository(BaseCompanyRepository):
    def get(self, company_id: str) -> Optional[CompanyEntity]:
        sql = """
            SELECT id, canonical_name, legal_name, normalized_name, primary_domain_id,
                   industry, employee_range, country_code, summary, status,
                   first_seen_at, last_seen_at, last_crawled_at, created_at, updated_at, metadata_json
            FROM companies WHERE id = %s;
        """
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (company_id,))
                row = cur.fetchone()
                if not row:
                    return None
                return self._row_to_entity(row)

    def get_by_normalized_name(self, normalized_name: str) -> Optional[CompanyEntity]:
        sql = """
            SELECT id, canonical_name, legal_name, normalized_name, primary_domain_id,
                   industry, employee_range, country_code, summary, status,
                   first_seen_at, last_seen_at, last_crawled_at, created_at, updated_at, metadata_json
            FROM companies WHERE normalized_name = %s ORDER BY last_seen_at DESC LIMIT 1;
        """
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (normalized_name,))
                row = cur.fetchone()
                if not row:
                    return None
                return self._row_to_entity(row)

    def get_by_domain(self, domain: str) -> Optional[CompanyEntity]:
        clean_domain = domain.strip().lower().replace("http://", "").replace("https://", "").split("/")[0]
        if clean_domain.startswith("www."):
            clean_domain = clean_domain[4:]
        sql = """
            SELECT c.id, c.canonical_name, c.legal_name, c.normalized_name, c.primary_domain_id,
                   c.industry, c.employee_range, c.country_code, c.summary, c.status,
                   c.first_seen_at, c.last_seen_at, c.last_crawled_at, c.created_at, c.updated_at, c.metadata_json
            FROM companies c
            JOIN company_domains cd ON c.id = cd.company_id
            JOIN domains d ON cd.domain_id = d.id
            WHERE d.normalized_domain = %s
            ORDER BY cd.is_primary DESC, cd.confidence DESC LIMIT 1;
        """
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (clean_domain,))
                row = cur.fetchone()
                if not row:
                    return None
                return self._row_to_entity(row)

    def upsert(self, company: CompanyEntity) -> CompanyEntity:
        sql = """
            INSERT INTO companies (
                id, canonical_name, legal_name, normalized_name, primary_domain_id,
                industry, employee_range, country_code, summary, status,
                first_seen_at, last_seen_at, last_crawled_at, created_at, updated_at, metadata_json
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                canonical_name = EXCLUDED.canonical_name,
                legal_name = COALESCE(EXCLUDED.legal_name, companies.legal_name),
                normalized_name = EXCLUDED.normalized_name,
                primary_domain_id = COALESCE(EXCLUDED.primary_domain_id, companies.primary_domain_id),
                industry = COALESCE(EXCLUDED.industry, companies.industry),
                employee_range = COALESCE(EXCLUDED.employee_range, companies.employee_range),
                country_code = COALESCE(EXCLUDED.country_code, companies.country_code),
                summary = COALESCE(EXCLUDED.summary, companies.summary),
                status = EXCLUDED.status,
                last_seen_at = EXCLUDED.last_seen_at,
                last_crawled_at = COALESCE(EXCLUDED.last_crawled_at, companies.last_crawled_at),
                updated_at = EXCLUDED.updated_at,
                metadata_json = companies.metadata_json || EXCLUDED.metadata_json
            RETURNING id;
        """
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
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
        sql = """
            SELECT id, canonical_name, legal_name, normalized_name, primary_domain_id,
                   industry, employee_range, country_code, summary, status,
                   first_seen_at, last_seen_at, last_crawled_at, created_at, updated_at, metadata_json
            FROM companies ORDER BY updated_at DESC LIMIT %s OFFSET %s;
        """
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (limit, offset))
                rows = cur.fetchall()
                return [self._row_to_entity(r) for r in rows]

    def count(self) -> int:
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM companies;")
                return cur.fetchone()[0]

    def add_alias(self, alias: CompanyAliasEntity) -> CompanyAliasEntity:
        sql = """
            INSERT INTO company_aliases (id, company_id, alias, normalized_alias, source_id, first_seen_at, last_seen_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                alias = EXCLUDED.alias,
                normalized_alias = EXCLUDED.normalized_alias,
                last_seen_at = EXCLUDED.last_seen_at;
        """
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
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
            INSERT INTO company_domains (company_id, domain_id, relationship_type, confidence, is_primary, first_seen_at, last_verified_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (company_id, domain_id) DO UPDATE SET
                relationship_type = EXCLUDED.relationship_type,
                confidence = EXCLUDED.confidence,
                is_primary = EXCLUDED.is_primary,
                last_verified_at = EXCLUDED.last_verified_at;
        """
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    (
                        link.company_id,
                        link.domain_id,
                        link.relationship_type,
                        link.confidence,
                        link.is_primary,
                        link.first_seen_at,
                        link.last_verified_at,
                    ),
                )
        return link

    def _row_to_entity(self, r) -> CompanyEntity:
        meta = r[15]
        if isinstance(meta, str):
            meta = json.loads(meta)
        return CompanyEntity(
            id=r[0],
            canonical_name=r[1],
            legal_name=r[2],
            normalized_name=r[3],
            primary_domain_id=r[4],
            industry=r[5],
            employee_range=r[6],
            country_code=r[7],
            summary=r[8],
            status=r[9],
            first_seen_at=str(r[10]),
            last_seen_at=str(r[11]),
            last_crawled_at=str(r[12]) if r[12] else None,
            created_at=str(r[13]),
            updated_at=str(r[14]),
            metadata_json=meta or {},
        )


class PostgresDomainRepository(BaseDomainRepository):
    def get(self, domain_id: str) -> Optional[DomainEntity]:
        sql = """
            SELECT id, registrable_domain, hostname, normalized_domain, scheme, status,
                   first_seen_at, last_seen_at, last_crawled_at, created_at, updated_at, metadata_json
            FROM domains WHERE id = %s;
        """
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (domain_id,))
                row = cur.fetchone()
                if not row:
                    return None
                return self._row_to_entity(row)

    def get_by_normalized_domain(self, normalized_domain: str) -> Optional[DomainEntity]:
        clean = normalized_domain.strip().lower().replace("www.", "")
        sql = """
            SELECT id, registrable_domain, hostname, normalized_domain, scheme, status,
                   first_seen_at, last_seen_at, last_crawled_at, created_at, updated_at, metadata_json
            FROM domains WHERE normalized_domain = %s;
        """
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (clean,))
                row = cur.fetchone()
                if not row:
                    return None
                return self._row_to_entity(row)

    def upsert(self, domain: DomainEntity) -> DomainEntity:
        sql = """
            INSERT INTO domains (
                id, registrable_domain, hostname, normalized_domain, scheme, status,
                first_seen_at, last_seen_at, last_crawled_at, created_at, updated_at, metadata_json
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (normalized_domain) DO UPDATE SET
                registrable_domain = EXCLUDED.registrable_domain,
                hostname = EXCLUDED.hostname,
                scheme = EXCLUDED.scheme,
                status = EXCLUDED.status,
                last_seen_at = EXCLUDED.last_seen_at,
                last_crawled_at = COALESCE(EXCLUDED.last_crawled_at, domains.last_crawled_at),
                updated_at = EXCLUDED.updated_at,
                metadata_json = domains.metadata_json || EXCLUDED.metadata_json
            RETURNING id;
        """
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
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
                res = cur.fetchone()
                if res:
                    domain.id = res[0]
        return domain

    def list(self, limit: int = 50, offset: int = 0) -> List[DomainEntity]:
        sql = """
            SELECT id, registrable_domain, hostname, normalized_domain, scheme, status,
                   first_seen_at, last_seen_at, last_crawled_at, created_at, updated_at, metadata_json
            FROM domains ORDER BY updated_at DESC LIMIT %s OFFSET %s;
        """
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (limit, offset))
                return [self._row_to_entity(r) for r in cur.fetchall()]

    def count(self) -> int:
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM domains;")
                return cur.fetchone()[0]

    def _row_to_entity(self, r) -> DomainEntity:
        meta = r[11]
        if isinstance(meta, str):
            meta = json.loads(meta)
        return DomainEntity(
            id=r[0],
            registrable_domain=r[1],
            hostname=r[2],
            normalized_domain=r[3],
            scheme=r[4],
            status=r[5],
            first_seen_at=str(r[6]),
            last_seen_at=str(r[7]),
            last_crawled_at=str(r[8]) if r[8] else None,
            created_at=str(r[9]),
            updated_at=str(r[10]),
            metadata_json=meta or {},
        )


class PostgresPersonRepository(BasePersonRepository):
    def get(self, person_id: str) -> Optional[PersonEntity]:
        sql = """
            SELECT id, full_name, normalized_name, first_name, last_name, headline, location_text,
                   first_seen_at, last_seen_at, created_at, updated_at, metadata_json
            FROM people WHERE id = %s;
        """
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (person_id,))
                row = cur.fetchone()
                return self._row_to_entity(row) if row else None

    def get_by_normalized_name(self, normalized_name: str) -> Optional[PersonEntity]:
        sql = """
            SELECT id, full_name, normalized_name, first_name, last_name, headline, location_text,
                   first_seen_at, last_seen_at, created_at, updated_at, metadata_json
            FROM people WHERE normalized_name = %s ORDER BY last_seen_at DESC LIMIT 1;
        """
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (normalized_name,))
                row = cur.fetchone()
                return self._row_to_entity(row) if row else None

    def upsert(self, person: PersonEntity) -> PersonEntity:
        sql = """
            INSERT INTO people (
                id, full_name, normalized_name, first_name, last_name, headline, location_text,
                first_seen_at, last_seen_at, created_at, updated_at, metadata_json
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                full_name = EXCLUDED.full_name,
                normalized_name = EXCLUDED.normalized_name,
                first_name = COALESCE(EXCLUDED.first_name, people.first_name),
                last_name = COALESCE(EXCLUDED.last_name, people.last_name),
                headline = COALESCE(EXCLUDED.headline, people.headline),
                location_text = COALESCE(EXCLUDED.location_text, people.location_text),
                last_seen_at = EXCLUDED.last_seen_at,
                updated_at = EXCLUDED.updated_at,
                metadata_json = people.metadata_json || EXCLUDED.metadata_json
            RETURNING id;
        """
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
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
        sql = """
            SELECT id, full_name, normalized_name, first_name, last_name, headline, location_text,
                   first_seen_at, last_seen_at, created_at, updated_at, metadata_json
            FROM people ORDER BY updated_at DESC LIMIT %s OFFSET %s;
        """
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (limit, offset))
                return [self._row_to_entity(r) for r in cur.fetchall()]

    def count(self) -> int:
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM people;")
                return cur.fetchone()[0]

    def _row_to_entity(self, r) -> PersonEntity:
        meta = r[11]
        if isinstance(meta, str):
            meta = json.loads(meta)
        return PersonEntity(
            id=r[0],
            full_name=r[1],
            normalized_name=r[2],
            first_name=r[3],
            last_name=r[4],
            headline=r[5],
            location_text=r[6],
            first_seen_at=str(r[7]),
            last_seen_at=str(r[8]),
            created_at=str(r[9]),
            updated_at=str(r[10]),
            metadata_json=meta or {},
        )


class PostgresEmploymentRepository(BaseEmploymentRepository):
    def get(self, employment_id: str) -> Optional[EmploymentEntity]:
        sql = """
            SELECT id, person_id, company_id, title, normalized_title, department, seniority,
                   is_current, source_id, confidence, first_seen_at, last_seen_at, last_verified_at
            FROM employments WHERE id = %s;
        """
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (employment_id,))
                row = cur.fetchone()
                return self._row_to_entity(row) if row else None

    def upsert(self, employment: EmploymentEntity) -> EmploymentEntity:
        sql = """
            INSERT INTO employments (
                id, person_id, company_id, title, normalized_title, department, seniority,
                is_current, source_id, confidence, first_seen_at, last_seen_at, last_verified_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                title = EXCLUDED.title,
                normalized_title = EXCLUDED.normalized_title,
                department = COALESCE(EXCLUDED.department, employments.department),
                seniority = COALESCE(EXCLUDED.seniority, employments.seniority),
                is_current = EXCLUDED.is_current,
                confidence = EXCLUDED.confidence,
                last_seen_at = EXCLUDED.last_seen_at,
                last_verified_at = COALESCE(EXCLUDED.last_verified_at, employments.last_verified_at);
        """
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    (
                        employment.id,
                        employment.person_id,
                        employment.company_id,
                        employment.title,
                        employment.normalized_title,
                        employment.department,
                        employment.seniority,
                        employment.is_current,
                        employment.source_id,
                        employment.confidence,
                        employment.first_seen_at,
                        employment.last_seen_at,
                        employment.last_verified_at,
                    ),
                )
        return employment

    def list_by_company(self, company_id: str) -> List[EmploymentEntity]:
        sql = """
            SELECT id, person_id, company_id, title, normalized_title, department, seniority,
                   is_current, source_id, confidence, first_seen_at, last_seen_at, last_verified_at
            FROM employments WHERE company_id = %s ORDER BY is_current DESC, confidence DESC;
        """
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (company_id,))
                return [self._row_to_entity(r) for r in cur.fetchall()]

    def list_by_person(self, person_id: str) -> List[EmploymentEntity]:
        sql = """
            SELECT id, person_id, company_id, title, normalized_title, department, seniority,
                   is_current, source_id, confidence, first_seen_at, last_seen_at, last_verified_at
            FROM employments WHERE person_id = %s ORDER BY is_current DESC;
        """
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (person_id,))
                return [self._row_to_entity(r) for r in cur.fetchall()]

    def count(self) -> int:
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM employments;")
                return cur.fetchone()[0]

    def _row_to_entity(self, r) -> EmploymentEntity:
        return EmploymentEntity(
            id=r[0],
            person_id=r[1],
            company_id=r[2],
            title=r[3],
            normalized_title=r[4],
            department=r[5],
            seniority=r[6],
            is_current=bool(r[7]),
            source_id=r[8],
            confidence=float(r[9]),
            first_seen_at=str(r[10]),
            last_seen_at=str(r[11]),
            last_verified_at=str(r[12]) if r[12] else None,
        )


class PostgresSourceRepository(BaseSourceRepository):
    def get(self, source_id: str) -> Optional[SourceEntity]:
        sql = """
            SELECT id, source_type, url, domain_id, content_hash, observed_at, created_at, metadata_json
            FROM sources WHERE id = %s;
        """
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (source_id,))
                row = cur.fetchone()
                return self._row_to_entity(row) if row else None

    def get_by_url(self, url: str) -> Optional[SourceEntity]:
        sql = """
            SELECT id, source_type, url, domain_id, content_hash, observed_at, created_at, metadata_json
            FROM sources WHERE url = %s LIMIT 1;
        """
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (url,))
                row = cur.fetchone()
                return self._row_to_entity(row) if row else None

    def upsert(self, source: SourceEntity) -> SourceEntity:
        sql = """
            INSERT INTO sources (id, source_type, url, domain_id, content_hash, observed_at, created_at, metadata_json)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                observed_at = EXCLUDED.observed_at,
                content_hash = COALESCE(EXCLUDED.content_hash, sources.content_hash),
                metadata_json = sources.metadata_json || EXCLUDED.metadata_json;
        """
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
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
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM sources;")
                return cur.fetchone()[0]

    def _row_to_entity(self, r) -> SourceEntity:
        meta = r[7]
        if isinstance(meta, str):
            meta = json.loads(meta)
        return SourceEntity(
            id=r[0],
            source_type=r[1],
            url=r[2],
            domain_id=r[3],
            content_hash=r[4],
            observed_at=str(r[5]),
            created_at=str(r[6]),
            metadata_json=meta or {},
        )


class PostgresCrawlJobRepository(BaseCrawlJobRepository):
    def get(self, job_id: str) -> Optional[CrawlJobEntity]:
        sql = """
            SELECT id, target, status, config_json, started_at, completed_at, attempts, error_code, error_message, created_at, updated_at
            FROM crawl_jobs WHERE id = %s;
        """
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (job_id,))
                row = cur.fetchone()
                return self._row_to_entity(row) if row else None

    def upsert(self, job: CrawlJobEntity) -> CrawlJobEntity:
        sql = """
            INSERT INTO crawl_jobs (id, target, status, config_json, started_at, completed_at, attempts, error_code, error_message, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                status = EXCLUDED.status,
                started_at = COALESCE(EXCLUDED.started_at, crawl_jobs.started_at),
                completed_at = COALESCE(EXCLUDED.completed_at, crawl_jobs.completed_at),
                attempts = EXCLUDED.attempts,
                error_code = EXCLUDED.error_code,
                error_message = EXCLUDED.error_message,
                updated_at = EXCLUDED.updated_at,
                config_json = crawl_jobs.config_json || EXCLUDED.config_json;
        """
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
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
        sql = """
            SELECT id, target, status, config_json, started_at, completed_at, attempts, error_code, error_message, created_at, updated_at
            FROM crawl_jobs ORDER BY created_at DESC LIMIT %s OFFSET %s;
        """
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (limit, offset))
                return [self._row_to_entity(r) for r in cur.fetchall()]

    def count(self) -> int:
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM crawl_jobs;")
                return cur.fetchone()[0]

    def _row_to_entity(self, r) -> CrawlJobEntity:
        cfg = r[3]
        if isinstance(cfg, str):
            cfg = json.loads(cfg)
        return CrawlJobEntity(
            id=r[0],
            target=r[1],
            status=r[2],
            config_json=cfg or {},
            started_at=str(r[4]) if r[4] else None,
            completed_at=str(r[5]) if r[5] else None,
            attempts=int(r[6]),
            error_code=r[7],
            error_message=r[8],
            created_at=str(r[9]),
            updated_at=str(r[10]),
        )


class PostgresCrawlRunRepository(BaseCrawlRunRepository):
    def get(self, run_id: str) -> Optional[CrawlRunEntity]:
        sql = """
            SELECT id, job_id, target_url, domain_id, fetcher_type, http_status, started_at, completed_at, duration_ms, page_count, success, error_code, metadata_json
            FROM crawl_runs WHERE id = %s;
        """
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (run_id,))
                row = cur.fetchone()
                return self._row_to_entity(row) if row else None

    def create(self, run: CrawlRunEntity) -> CrawlRunEntity:
        sql = """
            INSERT INTO crawl_runs (id, job_id, target_url, domain_id, fetcher_type, http_status, started_at, completed_at, duration_ms, page_count, success, error_code, metadata_json)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING;
        """
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
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
                        run.success,
                        run.error_code,
                        json.dumps(run.metadata_json),
                    ),
                )
        return run

    def list_by_job(self, job_id: str) -> List[CrawlRunEntity]:
        sql = """
            SELECT id, job_id, target_url, domain_id, fetcher_type, http_status, started_at, completed_at, duration_ms, page_count, success, error_code, metadata_json
            FROM crawl_runs WHERE job_id = %s ORDER BY started_at DESC;
        """
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (job_id,))
                return [self._row_to_entity(r) for r in cur.fetchall()]

    def count(self) -> int:
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM crawl_runs;")
                return cur.fetchone()[0]

    def _row_to_entity(self, r) -> CrawlRunEntity:
        meta = r[12]
        if isinstance(meta, str):
            meta = json.loads(meta)
        return CrawlRunEntity(
            id=r[0],
            job_id=r[1],
            target_url=r[2],
            domain_id=r[3],
            fetcher_type=r[4],
            http_status=r[5],
            started_at=str(r[6]),
            completed_at=str(r[7]) if r[7] else None,
            duration_ms=r[8],
            page_count=int(r[9]),
            success=bool(r[10]),
            error_code=r[11],
            metadata_json=meta or {},
        )


class PostgresObjectRefRepository:
    def get(self, object_id: str) -> Optional[Any]:
        sql = """
            SELECT id, object_type, bucket, object_key, provider, content_type,
                   content_encoding, content_hash, size_bytes, source_url,
                   company_id, domain_id, crawl_run_id, created_at, metadata_json
            FROM object_refs WHERE id = %s;
        """
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (object_id,))
                row = cur.fetchone()
                return self._row_to_dict(row) if row else None

    def get_by_key(self, bucket: str, object_key: str) -> Optional[Any]:
        sql = """
            SELECT id, object_type, bucket, object_key, provider, content_type,
                   content_encoding, content_hash, size_bytes, source_url,
                   company_id, domain_id, crawl_run_id, created_at, metadata_json
            FROM object_refs WHERE bucket = %s AND object_key = %s;
        """
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (bucket, object_key))
                row = cur.fetchone()
                return self._row_to_dict(row) if row else None

    def upsert(self, ref: Any) -> Any:
        sql = """
            INSERT INTO object_refs (
                id, object_type, bucket, object_key, provider, content_type,
                content_encoding, content_hash, size_bytes, source_url,
                company_id, domain_id, crawl_run_id, created_at, metadata_json
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                content_hash = EXCLUDED.content_hash,
                size_bytes = EXCLUDED.size_bytes,
                metadata_json = object_refs.metadata_json || EXCLUDED.metadata_json;
        """
        ref_dict = ref.model_dump() if hasattr(ref, "model_dump") else dict(ref)
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
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
        sql = """
            SELECT id, object_type, bucket, object_key, provider, content_type,
                   content_encoding, content_hash, size_bytes, source_url,
                   company_id, domain_id, crawl_run_id, created_at, metadata_json
            FROM object_refs WHERE crawl_run_id = %s ORDER BY created_at DESC;
        """
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (run_id,))
                return [self._row_to_dict(r) for r in cur.fetchall()]

    def count(self) -> int:
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM object_refs;")
                return cur.fetchone()[0]

    def _row_to_dict(self, r) -> Dict[str, Any]:
        meta = r[14]
        if isinstance(meta, str):
            meta = json.loads(meta)
        return {
            "id": r[0],
            "object_type": r[1],
            "bucket": r[2],
            "object_key": r[3],
            "provider": r[4],
            "content_type": r[5],
            "content_encoding": r[6],
            "content_hash": r[7],
            "size_bytes": int(r[8]),
            "source_url": r[9],
            "company_id": r[10],
            "domain_id": r[11],
            "crawl_run_id": r[12],
            "created_at": str(r[13]),
            "metadata_json": meta or {},
        }

