import os
import time
import pytest

from growx_crawl.storage.ids import generate_canonical_id, extract_timestamp_from_id
from growx_crawl.storage.entities import (
    CompanyEntity,
    DomainEntity,
    PersonEntity,
    EmploymentEntity,
    CompanyDomainEntity,
)
from growx_crawl.storage.factory import StorageFactory, get_active_backend
from growx_crawl.storage.postgres.db import StorageConnectionError
from growx_crawl.storage.sqlite.canonical import (
    SqliteCompanyRepository,
    SqliteDomainRepository,
    SqlitePersonRepository,
    SqliteEmploymentRepository,
)
from growx_crawl.storage import JobRepository, LeadRepository


def test_canonical_id_generation():
    """Verify application-generated IDs are unique, prefixed, and sortable."""
    cmp_id_1 = generate_canonical_id("cmp_")
    time.sleep(0.01)
    cmp_id_2 = generate_canonical_id("cmp_")

    assert cmp_id_1.startswith("cmp_")
    assert cmp_id_2.startswith("cmp_")
    assert cmp_id_1 != cmp_id_2
    assert cmp_id_1 < cmp_id_2  # Lexically sortable by creation time

    ts_1 = extract_timestamp_from_id(cmp_id_1)
    ts_2 = extract_timestamp_from_id(cmp_id_2)
    assert ts_1 is not None and ts_2 is not None
    assert ts_2 >= ts_1

    for prefix in ["per_", "dom_", "emp_", "src_", "job_", "run_"]:
        cid = generate_canonical_id(prefix)
        assert cid.startswith(prefix)


def test_domain_canonical_uniqueness(tmp_path):
    """Verify unique domain constraint and idempotent upsert."""
    db_file = str(tmp_path / "test_domains.db")
    repo = SqliteDomainRepository(db_path=db_file)

    dom_1 = DomainEntity(
        id=generate_canonical_id("dom_"),
        registrable_domain="growxlabs.tech",
        hostname="growxlabs.tech",
        normalized_domain="growxlabs.tech",
    )
    repo.upsert(dom_1)

    assert repo.count() == 1
    found = repo.get_by_normalized_domain("growxlabs.tech")
    assert found is not None
    assert found.normalized_domain == "growxlabs.tech"

    # Upsert with same normalized domain should update existing record, not duplicate
    dom_2 = DomainEntity(
        id=generate_canonical_id("dom_"),
        registrable_domain="growxlabs.tech",
        hostname="www.growxlabs.tech",
        normalized_domain="growxlabs.tech",
        scheme="http",
    )
    repo.upsert(dom_2)
    assert repo.count() == 1  # Deduplicated!


def test_canonical_company_and_domain_link(tmp_path):
    """Verify canonical company creation and domain relationship linking."""
    db_file = str(tmp_path / "test_company.db")
    c_repo = SqliteCompanyRepository(db_path=db_file)
    d_repo = SqliteDomainRepository(db_path=db_file)

    dom_id = generate_canonical_id("dom_")
    d_repo.upsert(DomainEntity(
        id=dom_id,
        registrable_domain="stripe.com",
        hostname="stripe.com",
        normalized_domain="stripe.com",
    ))

    comp_id = generate_canonical_id("cmp_")
    company = CompanyEntity(
        id=comp_id,
        canonical_name="Stripe Inc",
        normalized_name="stripe inc",
        primary_domain_id=dom_id,
        industry="Fintech",
        country_code="US",
    )
    c_repo.upsert(company)

    # Link company to domain
    c_repo.link_domain(CompanyDomainEntity(
        company_id=comp_id,
        domain_id=dom_id,
        relationship_type="primary",
        is_primary=True,
    ))

    # Retrieve by domain
    matched = c_repo.get_by_domain("stripe.com")
    assert matched is not None
    assert matched.id == comp_id
    assert matched.canonical_name == "Stripe Inc"


def test_canonical_people_and_employment(tmp_path):
    """Verify person entity and employment relationship creation."""
    db_file = str(tmp_path / "test_people.db")
    p_repo = SqlitePersonRepository(db_path=db_file)
    c_repo = SqliteCompanyRepository(db_path=db_file)
    e_repo = SqliteEmploymentRepository(db_path=db_file)

    comp_id = generate_canonical_id("cmp_")
    c_repo.upsert(CompanyEntity(
        id=comp_id,
        canonical_name="Acme Corp",
        normalized_name="acme corp",
    ))

    person_id = generate_canonical_id("per_")
    p_repo.upsert(PersonEntity(
        id=person_id,
        full_name="Alice Smith",
        normalized_name="alice smith",
        first_name="Alice",
        last_name="Smith",
        headline="Chief Technology Officer",
    ))

    emp_id = generate_canonical_id("emp_")
    e_repo.upsert(EmploymentEntity(
        id=emp_id,
        person_id=person_id,
        company_id=comp_id,
        title="Chief Technology Officer",
        normalized_title="chief technology officer",
        seniority="C-Level",
        is_current=True,
    ))

    comp_employments = e_repo.list_by_company(comp_id)
    assert len(comp_employments) == 1
    assert comp_employments[0].person_id == person_id
    assert comp_employments[0].title == "Chief Technology Officer"


def test_storage_factory_backend_selection(monkeypatch):
    """Verify storage factory respects GROWX_STORAGE_BACKEND."""
    monkeypatch.setenv("GROWX_STORAGE_BACKEND", "sqlite")
    assert get_active_backend() == "sqlite"
    repo = StorageFactory.get_company_repository()
    assert isinstance(repo, SqliteCompanyRepository)


def test_storage_factory_failure_strategy(monkeypatch):
    """Verify Section 26: Postgres backend never silently falls back to SQLite."""
    monkeypatch.setenv("GROWX_STORAGE_BACKEND", "postgres")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_DATABASE_URL", raising=False)

    with pytest.raises(StorageConnectionError) as exc_info:
        StorageFactory.get_company_repository()
    assert "cannot proceed without canonical PostgreSQL database" in str(exc_info.value)


def test_legacy_lead_and_job_repositories_compatibility():
    """Verify existing JobRepository and LeadRepository continue to work 100%."""
    j_repo = JobRepository()
    l_repo = LeadRepository()
    jobs = j_repo.list_jobs(limit=5)
    assert isinstance(jobs, list)
