from growx_crawl.storage.db import get_db
from growx_crawl.storage.repository import (
    AgentRunRepository,
    CampaignRepository,
    ErrorRepository,
    JobRepository,
    LeadRepository,
    TargetRepository,
)
from growx_crawl.storage.schema import init_db

# Phase 01 Canonical Additions
from growx_crawl.storage.ids import generate_canonical_id, extract_timestamp_from_id
from growx_crawl.storage.entities import (
    CompanyEntity,
    CompanyAliasEntity,
    DomainEntity,
    CompanyDomainEntity,
    PersonEntity,
    EmploymentEntity,
    SourceEntity,
    CrawlJobEntity,
    CrawlRunEntity,
)
from growx_crawl.storage.factory import StorageFactory, get_active_backend
from growx_crawl.storage.postgres.db import StorageConnectionError

__all__ = [
    # Legacy Storage Exports (Preserved 100%)
    "AgentRunRepository",
    "CampaignRepository",
    "ErrorRepository",
    "JobRepository",
    "LeadRepository",
    "TargetRepository",
    "get_db",
    "init_db",
    # Canonical Phase 01 Exports
    "generate_canonical_id",
    "extract_timestamp_from_id",
    "CompanyEntity",
    "CompanyAliasEntity",
    "DomainEntity",
    "CompanyDomainEntity",
    "PersonEntity",
    "EmploymentEntity",
    "SourceEntity",
    "CrawlJobEntity",
    "CrawlRunEntity",
    "StorageFactory",
    "get_active_backend",
    "StorageConnectionError",
]
