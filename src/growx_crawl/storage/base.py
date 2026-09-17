from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
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


class BaseCompanyRepository(ABC):
    @abstractmethod
    def get(self, company_id: str) -> Optional[CompanyEntity]: ...

    @abstractmethod
    def get_by_normalized_name(self, normalized_name: str) -> Optional[CompanyEntity]: ...

    @abstractmethod
    def get_by_domain(self, domain: str) -> Optional[CompanyEntity]: ...

    @abstractmethod
    def upsert(self, company: CompanyEntity) -> CompanyEntity: ...

    @abstractmethod
    def list(self, limit: int = 50, offset: int = 0) -> List[CompanyEntity]: ...

    @abstractmethod
    def count(self) -> int: ...

    @abstractmethod
    def add_alias(self, alias: CompanyAliasEntity) -> CompanyAliasEntity: ...

    @abstractmethod
    def link_domain(self, link: CompanyDomainEntity) -> CompanyDomainEntity: ...


class BaseDomainRepository(ABC):
    @abstractmethod
    def get(self, domain_id: str) -> Optional[DomainEntity]: ...

    @abstractmethod
    def get_by_normalized_domain(self, normalized_domain: str) -> Optional[DomainEntity]: ...

    @abstractmethod
    def upsert(self, domain: DomainEntity) -> DomainEntity: ...

    @abstractmethod
    def list(self, limit: int = 50, offset: int = 0) -> List[DomainEntity]: ...

    @abstractmethod
    def count(self) -> int: ...


class BasePersonRepository(ABC):
    @abstractmethod
    def get(self, person_id: str) -> Optional[PersonEntity]: ...

    @abstractmethod
    def get_by_normalized_name(self, normalized_name: str) -> Optional[PersonEntity]: ...

    @abstractmethod
    def upsert(self, person: PersonEntity) -> PersonEntity: ...

    @abstractmethod
    def list(self, limit: int = 50, offset: int = 0) -> List[PersonEntity]: ...

    @abstractmethod
    def count(self) -> int: ...


class BaseEmploymentRepository(ABC):
    @abstractmethod
    def get(self, employment_id: str) -> Optional[EmploymentEntity]: ...

    @abstractmethod
    def upsert(self, employment: EmploymentEntity) -> EmploymentEntity: ...

    @abstractmethod
    def list_by_company(self, company_id: str) -> List[EmploymentEntity]: ...

    @abstractmethod
    def list_by_person(self, person_id: str) -> List[EmploymentEntity]: ...

    @abstractmethod
    def count(self) -> int: ...


class BaseSourceRepository(ABC):
    @abstractmethod
    def get(self, source_id: str) -> Optional[SourceEntity]: ...

    @abstractmethod
    def get_by_url(self, url: str) -> Optional[SourceEntity]: ...

    @abstractmethod
    def upsert(self, source: SourceEntity) -> SourceEntity: ...

    @abstractmethod
    def count(self) -> int: ...


class BaseCrawlJobRepository(ABC):
    @abstractmethod
    def get(self, job_id: str) -> Optional[CrawlJobEntity]: ...

    @abstractmethod
    def upsert(self, job: CrawlJobEntity) -> CrawlJobEntity: ...

    @abstractmethod
    def list(self, limit: int = 50, offset: int = 0) -> List[CrawlJobEntity]: ...

    @abstractmethod
    def count(self) -> int: ...


class BaseCrawlRunRepository(ABC):
    @abstractmethod
    def get(self, run_id: str) -> Optional[CrawlRunEntity]: ...

    @abstractmethod
    def create(self, run: CrawlRunEntity) -> CrawlRunEntity: ...

    @abstractmethod
    def list_by_job(self, job_id: str) -> List[CrawlRunEntity]: ...

    @abstractmethod
    def count(self) -> int: ...
