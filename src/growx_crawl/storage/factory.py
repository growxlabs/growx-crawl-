import logging
import os
from typing import Optional

from growx_crawl.storage.base import (
    BaseCompanyRepository,
    BaseCrawlJobRepository,
    BaseCrawlRunRepository,
    BaseDomainRepository,
    BaseEmploymentRepository,
    BasePersonRepository,
    BaseSourceRepository,
)
from growx_crawl.storage.postgres.db import PostgresPool, StorageConnectionError
from growx_crawl.storage.postgres.repository import (
    PostgresCompanyRepository,
    PostgresCrawlJobRepository,
    PostgresCrawlRunRepository,
    PostgresDomainRepository,
    PostgresEmploymentRepository,
    PostgresPersonRepository,
    PostgresSourceRepository,
)
from growx_crawl.storage.sqlite.canonical import (
    SqliteCompanyRepository,
    SqliteCrawlJobRepository,
    SqliteCrawlRunRepository,
    SqliteDomainRepository,
    SqliteEmploymentRepository,
    SqlitePersonRepository,
    SqliteSourceRepository,
)

logger = logging.getLogger("growx_crawl.storage.factory")


def get_active_backend() -> str:
    """
    Returns the configured storage backend: 'sqlite' (default for local/offline) or 'postgres' (production).
    """
    return os.environ.get("GROWX_STORAGE_BACKEND", "sqlite").strip().lower()


class StorageFactory:
    """
    Factory resolving active repository implementations based on GROWX_STORAGE_BACKEND.
    Ensures business logic is isolated from underlying database implementation.
    """

    @classmethod
    def get_company_repository(cls) -> BaseCompanyRepository:
        backend = get_active_backend()
        if backend == "postgres":
            cls._verify_postgres_or_fail()
            return PostgresCompanyRepository()
        return SqliteCompanyRepository()

    @classmethod
    def get_domain_repository(cls) -> BaseDomainRepository:
        backend = get_active_backend()
        if backend == "postgres":
            cls._verify_postgres_or_fail()
            return PostgresDomainRepository()
        return SqliteDomainRepository()

    @classmethod
    def get_person_repository(cls) -> BasePersonRepository:
        backend = get_active_backend()
        if backend == "postgres":
            cls._verify_postgres_or_fail()
            return PostgresPersonRepository()
        return SqlitePersonRepository()

    @classmethod
    def get_employment_repository(cls) -> BaseEmploymentRepository:
        backend = get_active_backend()
        if backend == "postgres":
            cls._verify_postgres_or_fail()
            return PostgresEmploymentRepository()
        return SqliteEmploymentRepository()

    @classmethod
    def get_source_repository(cls) -> BaseSourceRepository:
        backend = get_active_backend()
        if backend == "postgres":
            cls._verify_postgres_or_fail()
            return PostgresSourceRepository()
        return SqliteSourceRepository()

    @classmethod
    def get_crawl_job_repository(cls) -> BaseCrawlJobRepository:
        backend = get_active_backend()
        if backend == "postgres":
            cls._verify_postgres_or_fail()
            return PostgresCrawlJobRepository()
        return SqliteCrawlJobRepository()

    @classmethod
    def get_crawl_run_repository(cls) -> BaseCrawlRunRepository:
        backend = get_active_backend()
        if backend == "postgres":
            cls._verify_postgres_or_fail()
            return PostgresCrawlRunRepository()
        return SqliteCrawlRunRepository()

    @classmethod
    def _verify_postgres_or_fail(cls):
        """
        Section 26 Failure Strategy:
        If Postgres is configured for production, NEVER silently fall back to SQLite.
        Raise StorageConnectionError with actionable context.
        """
        pool = PostgresPool.get_instance()
        if not pool.dsn:
            raise StorageConnectionError(
                "GROWX_STORAGE_BACKEND is set to 'postgres', but DATABASE_URL is not configured. "
                "Production cannot proceed without canonical PostgreSQL database. "
                "Set DATABASE_URL or set GROWX_STORAGE_BACKEND=sqlite for local development."
            )
        # Attempt connection check
        if not pool.check_health():
            raise StorageConnectionError(
                "Failed to connect to PostgreSQL / Supabase cluster. "
                "Failing safely per Section 26 Failure Strategy. Zero silent fallback to SQLite in production mode."
            )
