from datetime import datetime, timezone
import json
import logging
import os
import re
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from growx_crawl.storage.db import get_db
from growx_crawl.storage.entities import (
    CompanyDomainEntity,
    CompanyEntity,
    DomainEntity,
    EmploymentEntity,
    PersonEntity,
)
from growx_crawl.storage.ids import generate_canonical_id
from growx_crawl.storage.postgres.db import PostgresPool, get_pg_connection
from growx_crawl.storage.postgres.repository import (
    PostgresCompanyRepository,
    PostgresDomainRepository,
    PostgresEmploymentRepository,
    PostgresPersonRepository,
)
from growx_crawl.storage.postgres.schema import init_pg_schema

logger = logging.getLogger("growx_crawl.storage.migrator")


def clean_domain_name(raw: str) -> str:
    if not raw:
        return ""
    clean = raw.strip().lower().replace("https://", "").replace("http://", "").split("/")[0]
    if clean.startswith("www."):
        clean = clean[4:]
    return clean


class SQLiteToPostgresMigrator:
    """
    Resumable, idempotent data migration pipeline from legacy SQLite to canonical PostgreSQL/Supabase.
    """

    def __init__(self, sqlite_path: Optional[str] = None):
        self.sqlite_path = sqlite_path
        self.comp_repo = PostgresCompanyRepository()
        self.dom_repo = PostgresDomainRepository()
        self.per_repo = PostgresPersonRepository()
        self.emp_repo = PostgresEmploymentRepository()

    def run_migration(self, batch_size: int = 500) -> Dict[str, Any]:
        """
        Executes the full migration pipeline, reporting entity counts and conflicts.
        """
        start_time = datetime.now(timezone.utc)
        run_id = generate_canonical_id("mig_")

        stats = {
            "migration_run_id": run_id,
            "started_at": start_time.isoformat(),
            "sqlite_companies_read": 0,
            "sqlite_contacts_read": 0,
            "postgres_companies_created": 0,
            "postgres_domains_created": 0,
            "postgres_people_created": 0,
            "postgres_employments_created": 0,
            "merged_duplicate_domains": 0,
            "rejected_invalid_rows": 0,
            "fatal_errors": 0,
            "completed_at": None,
            "status": "in_progress",
        }

        # Step 1: Ensure Postgres Schema is initialized
        try:
            with get_pg_connection() as conn:
                init_pg_schema(conn)
        except Exception as e:
            logger.error(f"Failed to initialize target Postgres schema: {e}")
            stats["fatal_errors"] += 1
            stats["status"] = "failed"
            stats["error"] = str(e)
            return stats

        domain_cache: Dict[str, str] = {}  # normalized_domain -> domain_id

        # Step 2: Migrate Companies & Domains
        with get_db(self.sqlite_path) as s_conn:
            c_rows = s_conn.execute("SELECT * FROM companies ORDER BY created_at ASC;").fetchall()
            stats["sqlite_companies_read"] = len(c_rows)

            for row in c_rows:
                raw_domain = row["domain"] or ""
                norm_domain = clean_domain_name(raw_domain)
                comp_name = row["name"] or "Unknown Company"
                norm_name = row["normalized_name"] or comp_name.strip().lower()

                if not norm_domain and not norm_name:
                    stats["rejected_invalid_rows"] += 1
                    continue

                domain_id = None
                if norm_domain:
                    # Check in cache or DB
                    if norm_domain in domain_cache:
                        domain_id = domain_cache[norm_domain]
                        stats["merged_duplicate_domains"] += 1
                    else:
                        existing_dom = self.dom_repo.get_by_normalized_domain(norm_domain)
                        if existing_dom:
                            domain_id = existing_dom.id
                            domain_cache[norm_domain] = domain_id
                            stats["merged_duplicate_domains"] += 1
                        else:
                            domain_id = generate_canonical_id("dom_")
                            dom_entity = DomainEntity(
                                id=domain_id,
                                registrable_domain=norm_domain,
                                hostname=norm_domain,
                                normalized_domain=norm_domain,
                                scheme="https",
                                status="active",
                                first_seen_at=row["created_at"] or datetime.now(timezone.utc).isoformat(),
                                last_seen_at=row["updated_at"] or datetime.now(timezone.utc).isoformat(),
                                created_at=row["created_at"] or datetime.now(timezone.utc).isoformat(),
                                updated_at=row["updated_at"] or datetime.now(timezone.utc).isoformat(),
                                metadata_json={"source": row["source"] or "sqlite_migration"},
                            )
                            self.dom_repo.upsert(dom_entity)
                            domain_cache[norm_domain] = domain_id
                            stats["postgres_domains_created"] += 1

                # Upsert Canonical Company
                comp_id = generate_canonical_id("cmp_")
                comp_entity = CompanyEntity(
                    id=comp_id,
                    canonical_name=comp_name,
                    normalized_name=norm_name,
                    primary_domain_id=domain_id,
                    industry=row["industry"],
                    country_code=row["country"][:8] if row["country"] else None,
                    summary=row["description"],
                    status="active",
                    first_seen_at=row["created_at"] or datetime.now(timezone.utc).isoformat(),
                    last_seen_at=row["updated_at"] or datetime.now(timezone.utc).isoformat(),
                    created_at=row["created_at"] or datetime.now(timezone.utc).isoformat(),
                    updated_at=row["updated_at"] or datetime.now(timezone.utc).isoformat(),
                    metadata_json={
                        "legacy_sqlite_id": row["id"],
                        "city": row["city"],
                        "state": row["state"],
                        "address": row["address"],
                        "rating": row["rating"],
                        "review_count": row["review_count"],
                    },
                )
                self.comp_repo.upsert(comp_entity)
                stats["postgres_companies_created"] += 1

                if domain_id:
                    link = CompanyDomainEntity(
                        company_id=comp_id,
                        domain_id=domain_id,
                        relationship_type="primary",
                        confidence=1.0,
                        is_primary=True,
                        first_seen_at=comp_entity.first_seen_at,
                    )
                    self.comp_repo.link_domain(link)

            # Step 3: Migrate Contacts & Employments
            cont_rows = s_conn.execute("SELECT * FROM contacts ORDER BY created_at ASC;").fetchall()
            stats["sqlite_contacts_read"] = len(cont_rows)

            for c in cont_rows:
                full_name = c["name"] or ""
                if not full_name.strip():
                    stats["rejected_invalid_rows"] += 1
                    continue

                norm_p_name = full_name.strip().lower()
                parts = full_name.split()
                first_name = parts[0] if parts else None
                last_name = parts[-1] if len(parts) > 1 else None

                # Check if person already exists
                existing_person = self.per_repo.get_by_normalized_name(norm_p_name)
                if existing_person:
                    person_id = existing_person.id
                else:
                    person_id = generate_canonical_id("per_")
                    person_entity = PersonEntity(
                        id=person_id,
                        full_name=full_name,
                        normalized_name=norm_p_name,
                        first_name=first_name,
                        last_name=last_name,
                        headline=c["title"],
                        first_seen_at=c["created_at"] or datetime.now(timezone.utc).isoformat(),
                        last_seen_at=c["created_at"] or datetime.now(timezone.utc).isoformat(),
                        created_at=c["created_at"] or datetime.now(timezone.utc).isoformat(),
                        updated_at=c["created_at"] or datetime.now(timezone.utc).isoformat(),
                        metadata_json={
                            "legacy_sqlite_id": c["id"],
                            "email": c["email"],
                            "phone": c["phone"],
                            "linkedin_url": c["linkedin_url"],
                        },
                    )
                    self.per_repo.upsert(person_entity)
                    stats["postgres_people_created"] += 1

                # Map employment to canonical company if matched
                legacy_comp_id = c["company_id"]
                matching_comp_row = s_conn.execute("SELECT domain, normalized_name FROM companies WHERE id = ?", (legacy_comp_id,)).fetchone()
                if matching_comp_row:
                    comp_domain = clean_domain_name(matching_comp_row["domain"])
                    canonical_comp = self.comp_repo.get_by_domain(comp_domain) if comp_domain else None
                    if not canonical_comp:
                        canonical_comp = self.comp_repo.get_by_normalized_name(matching_comp_row["normalized_name"])

                    if canonical_comp:
                        emp_id = generate_canonical_id("emp_")
                        emp_entity = EmploymentEntity(
                            id=emp_id,
                            person_id=person_id,
                            company_id=canonical_comp.id,
                            title=c["title"] or "Executive",
                            normalized_title=(c["title"] or "Executive").strip().lower(),
                            is_current=True,
                            confidence=c["confidence"] or 1.0,
                            first_seen_at=c["created_at"] or datetime.now(timezone.utc).isoformat(),
                            last_seen_at=c["created_at"] or datetime.now(timezone.utc).isoformat(),
                        )
                        self.emp_repo.upsert(emp_entity)
                        stats["postgres_employments_created"] += 1

        stats["completed_at"] = datetime.now(timezone.utc).isoformat()
        stats["status"] = "success"
        return stats


sqlite_migrator = SQLiteToPostgresMigrator()
