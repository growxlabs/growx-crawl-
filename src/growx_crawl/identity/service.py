import logging
from typing import Any, Dict, List, Optional, Tuple

from growx_crawl.identity.events import create_identity_event
from growx_crawl.identity.ids import generate_identity_id
from growx_crawl.identity.keys import (
    build_domain_key,
    build_external_id_key,
    build_linkedin_key,
    build_person_email_key,
)
from growx_crawl.identity.merge import create_entity_merge
from growx_crawl.identity.models import (
    BrandEntity,
    CompanyLocationEntity,
    CompanyRelationshipEntity,
    EntityMergeEntity,
    ExternalIdentityEntity,
    IdentityCandidateEntity,
    IdentityEventEntity,
    IdentityKeyEntity,
    LocationEntity,
    PersonAliasEntity,
)
from growx_crawl.identity.normalization import (
    normalize_company_name,
    normalize_domain,
    normalize_person_name,
)
from growx_crawl.identity.repository import BaseIdentityRepository, SqliteIdentityRepository
from growx_crawl.storage.base import (
    BaseCompanyRepository,
    BaseDomainRepository,
    BaseEmploymentRepository,
    BasePersonRepository,
)
from growx_crawl.storage.entities import (
    CompanyAliasEntity,
    CompanyDomainEntity,
    CompanyEntity,
    DomainEntity,
    EmploymentEntity,
    PersonEntity,
)
from growx_crawl.storage.factory import StorageFactory

logger = logging.getLogger("growx_crawl.identity.service")


class IdentityService:
    """
    Core identity service facade coordinating deterministic resolution,
    key generation, entity deduplication, candidate queuing, and merge redirects.
    
    Rule: Raw names are observations. Canonical IDs are identity.
    """

    def __init__(
        self,
        company_repo: Optional[BaseCompanyRepository] = None,
        domain_repo: Optional[BaseDomainRepository] = None,
        person_repo: Optional[BasePersonRepository] = None,
        employment_repo: Optional[BaseEmploymentRepository] = None,
        identity_repo: Optional[BaseIdentityRepository] = None,
    ):
        self._company_repo = company_repo
        self._domain_repo = domain_repo
        self._person_repo = person_repo
        self._employment_repo = employment_repo
        self._identity_repo = identity_repo

    @property
    def company_repo(self) -> BaseCompanyRepository:
        if self._company_repo is None:
            self._company_repo = StorageFactory.get_company_repository()
        return self._company_repo

    @property
    def domain_repo(self) -> BaseDomainRepository:
        if self._domain_repo is None:
            self._domain_repo = StorageFactory.get_domain_repository()
        return self._domain_repo

    @property
    def person_repo(self) -> BasePersonRepository:
        if self._person_repo is None:
            self._person_repo = StorageFactory.get_person_repository()
        return self._person_repo

    @property
    def employment_repo(self) -> BaseEmploymentRepository:
        if self._employment_repo is None:
            self._employment_repo = StorageFactory.get_employment_repository()
        return self._employment_repo

    @property
    def identity_repo(self) -> BaseIdentityRepository:
        if self._identity_repo is None:
            self._identity_repo = SqliteIdentityRepository()
        return self._identity_repo

    # -------------------------------------------------------------------------
    # Domains
    # -------------------------------------------------------------------------
    def get_or_create_domain(
        self,
        url_or_domain: str,
        source_id: Optional[str] = None,
    ) -> DomainEntity:
        """
        Deterministically normalizes and resolves or creates a canonical domain.
        """
        hostname, reg_domain = normalize_domain(url_or_domain)
        if not hostname:
            raise ValueError(f"Invalid URL or domain string: {url_or_domain}")

        existing = self.domain_repo.get_by_normalized_domain(hostname)
        if existing:
            return existing

        domain_id = generate_identity_id("dom_")
        new_domain = DomainEntity(
            id=domain_id,
            registrable_domain=reg_domain or hostname,
            hostname=hostname,
            normalized_domain=hostname,
            scheme="https",
            status="active",
        )
        saved = self.domain_repo.upsert(new_domain)

        # Register lookup key
        key_str = build_domain_key(hostname)
        if key_str:
            self.identity_repo.upsert_key(
                IdentityKeyEntity(
                    id=generate_identity_id("ext_"),
                    entity_type="domain",
                    entity_id=saved.id,
                    key_type="domain",
                    key_value=hostname,
                    is_unique=True,
                )
            )

        # Audit event
        self.identity_repo.record_event(
            create_identity_event(
                entity_type="domain",
                entity_id=saved.id,
                event_type="entity_created",
                payload={"hostname": hostname, "registrable_domain": reg_domain},
                source_id=source_id,
            )
        )
        return saved

    # -------------------------------------------------------------------------
    # Companies
    # -------------------------------------------------------------------------
    def get_or_create_company(
        self,
        name: str,
        domain: Optional[str] = None,
        legal_name: Optional[str] = None,
        source_id: Optional[str] = None,
        industry: Optional[str] = None,
        employee_range: Optional[str] = None,
        country_code: Optional[str] = None,
    ) -> CompanyEntity:
        """
        Resolves or creates a canonical company using deterministic identity rules:
        1. If a domain is provided:
           - If domain is already linked to a company, resolve canonical company ID (following redirects).
             If observed name is an alias, save alias and return canonical company.
           - If domain is not linked to any company:
             - If a company with normalized_name exists without a primary domain, attach this domain.
             - If a company with normalized_name exists with a DIFFERENT primary domain, do NOT auto-merge!
               Queue as identity_candidate and create distinct company entity.
             - If no company with normalized_name exists, create new company and link domain.
        2. If no domain is provided:
           - Match by normalized_name if found; otherwise create unattached company entity.
        """
        norm_name = normalize_company_name(name)
        if not norm_name:
            raise ValueError("Company name cannot be empty")

        if domain:
            dom_entity = self.get_or_create_domain(domain, source_id=source_id)
            linked_company = self.company_repo.get_by_domain(dom_entity.normalized_domain)

            if linked_company:
                # Follow merge redirects if company was previously merged
                surviving_id = self.resolve_canonical_id(linked_company.id)
                if surviving_id != linked_company.id:
                    canon_comp = self.company_repo.get(surviving_id)
                    if canon_comp:
                        linked_company = canon_comp

                # If name differs, record as alias
                if norm_name != linked_company.normalized_name:
                    alias = CompanyAliasEntity(
                        id=generate_identity_id("ext_"),
                        company_id=linked_company.id,
                        alias=name,
                        normalized_alias=norm_name,
                        source_id=source_id,
                    )
                    self.company_repo.add_alias(alias)
                    self.identity_repo.record_event(
                        create_identity_event(
                            entity_type="company",
                            entity_id=linked_company.id,
                            event_type="alias_added",
                            payload={"alias": name, "normalized_alias": norm_name},
                            source_id=source_id,
                        )
                    )
                return linked_company

            # Domain is not yet linked to any company
            existing_by_name = self.company_repo.get_by_normalized_name(norm_name)
            if existing_by_name:
                surviving_id = self.resolve_canonical_id(existing_by_name.id)
                if surviving_id != existing_by_name.id:
                    canon_comp = self.company_repo.get(surviving_id)
                    if canon_comp:
                        existing_by_name = canon_comp

                if not existing_by_name.primary_domain_id:
                    # Company exists without a primary domain — attach this domain
                    existing_by_name.primary_domain_id = dom_entity.id
                    self.company_repo.upsert(existing_by_name)
                    self.company_repo.link_domain(
                        CompanyDomainEntity(
                            company_id=existing_by_name.id,
                            domain_id=dom_entity.id,
                            relationship_type="primary",
                            is_primary=True,
                            confidence=1.0,
                        )
                    )
                    self.identity_repo.record_event(
                        create_identity_event(
                            entity_type="company",
                            entity_id=existing_by_name.id,
                            event_type="domain_linked",
                            payload={"domain_id": dom_entity.id, "domain": dom_entity.normalized_domain},
                            source_id=source_id,
                        )
                    )
                    return existing_by_name
                elif existing_by_name.primary_domain_id != dom_entity.id:
                    # AMBIGUOUS: Name matches existing company, but domain is completely different!
                    # Section 13: Do NOT auto-merge across distinct domains. Queue candidate.
                    logger.info(
                        "Ambiguous company match: '%s' exists on domain_id %s, new observation on domain %s. Queuing candidate.",
                        norm_name,
                        existing_by_name.primary_domain_id,
                        dom_entity.normalized_domain,
                    )
                    self.create_candidate(
                        entity_type="company",
                        candidate_key=f"name:{norm_name}",
                        payload={
                            "name": name,
                            "normalized_name": norm_name,
                            "domain": dom_entity.normalized_domain,
                            "existing_company_id": existing_by_name.id,
                            "existing_primary_domain_id": existing_by_name.primary_domain_id,
                        },
                        source_id=source_id,
                    )
                    # Proceed to create distinct company to maintain safe partition
                    pass

            # Create new company with linked primary domain
            company_id = generate_identity_id("cmp_")
            comp = CompanyEntity(
                id=company_id,
                canonical_name=name,
                legal_name=legal_name,
                normalized_name=norm_name,
                primary_domain_id=dom_entity.id,
                industry=industry,
                employee_range=employee_range,
                country_code=country_code,
            )
            saved = self.company_repo.upsert(comp)
            self.company_repo.link_domain(
                CompanyDomainEntity(
                    company_id=saved.id,
                    domain_id=dom_entity.id,
                    relationship_type="primary",
                    is_primary=True,
                    confidence=1.0,
                )
            )
            self.identity_repo.record_event(
                create_identity_event(
                    entity_type="company",
                    entity_id=saved.id,
                    event_type="entity_created",
                    payload={"canonical_name": name, "normalized_name": norm_name, "domain_id": dom_entity.id},
                    source_id=source_id,
                )
            )
            return saved

        # No domain provided
        existing_by_name = self.company_repo.get_by_normalized_name(norm_name)
        if existing_by_name:
            surviving_id = self.resolve_canonical_id(existing_by_name.id)
            if surviving_id != existing_by_name.id:
                canon_comp = self.company_repo.get(surviving_id)
                if canon_comp:
                    return canon_comp
            return existing_by_name

        company_id = generate_identity_id("cmp_")
        comp = CompanyEntity(
            id=company_id,
            canonical_name=name,
            legal_name=legal_name,
            normalized_name=norm_name,
            industry=industry,
            employee_range=employee_range,
            country_code=country_code,
        )
        saved = self.company_repo.upsert(comp)
        self.identity_repo.record_event(
            create_identity_event(
                entity_type="company",
                entity_id=saved.id,
                event_type="entity_created",
                payload={"canonical_name": name, "normalized_name": norm_name},
                source_id=source_id,
            )
        )
        return saved

    # -------------------------------------------------------------------------
    # People & Employments
    # -------------------------------------------------------------------------
    def get_or_create_person(
        self,
        full_name: str,
        company_id: Optional[str] = None,
        title: Optional[str] = None,
        email: Optional[str] = None,
        linkedin_url: Optional[str] = None,
        location_text: Optional[str] = None,
        source_id: Optional[str] = None,
    ) -> Tuple[PersonEntity, Optional[EmploymentEntity]]:
        """
        Deterministically resolves or creates a person entity.
        Prioritizes verified unique keys (email, linkedin), then employment linkage.
        """
        norm_name = normalize_person_name(full_name)
        if not norm_name:
            raise ValueError("Person name cannot be empty")

        person: Optional[PersonEntity] = None

        # 1. Lookup by verified email key
        if email:
            clean_email = email.strip().lower()
            key_rec = self.identity_repo.get_key("email", clean_email)
            if key_rec and key_rec.entity_type == "person":
                person = self.person_repo.get(key_rec.entity_id)

        # 2. Lookup by LinkedIn external identity key
        if not person and linkedin_url:
            clean_handle = build_linkedin_key(linkedin_url)
            if clean_handle:
                slug = clean_handle.split(":")[-1]
                ext = self.identity_repo.get_external_identity("linkedin", slug)
                if ext and ext.entity_type == "person":
                    person = self.person_repo.get(ext.entity_id)

        # 3. Lookup by company employment + normalized name
        if not person and company_id:
            canon_company_id = self.resolve_canonical_id(company_id)
            employments = self.employment_repo.list_by_company(canon_company_id)
            for emp in employments:
                candidate_person = self.person_repo.get(emp.person_id)
                if candidate_person and candidate_person.normalized_name == norm_name:
                    person = candidate_person
                    break

        # 4. If not found, create person entity
        if not person:
            parts = full_name.strip().split()
            first_name = parts[0] if parts else None
            last_name = parts[-1] if len(parts) > 1 else None

            person_id = generate_identity_id("per_")
            new_person = PersonEntity(
                id=person_id,
                full_name=full_name,
                normalized_name=norm_name,
                first_name=first_name,
                last_name=last_name,
                location_text=location_text,
            )
            person = self.person_repo.upsert(new_person)
            self.identity_repo.record_event(
                create_identity_event(
                    entity_type="person",
                    entity_id=person.id,
                    event_type="entity_created",
                    payload={"full_name": full_name, "normalized_name": norm_name},
                    source_id=source_id,
                )
            )

        # Register email key & external identity if provided
        if email:
            clean_email = email.strip().lower()
            self.identity_repo.upsert_key(
                IdentityKeyEntity(
                    id=generate_identity_id("ext_"),
                    entity_type="person",
                    entity_id=person.id,
                    key_type="email",
                    key_value=clean_email,
                    is_unique=True,
                )
            )
            self.identity_repo.upsert_external_identity(
                ExternalIdentityEntity(
                    id=generate_identity_id("ext_"),
                    entity_type="person",
                    entity_id=person.id,
                    provider="email",
                    external_id=clean_email,
                )
            )

        # Register LinkedIn external identity if provided
        if linkedin_url:
            clean_handle = build_linkedin_key(linkedin_url)
            if clean_handle:
                slug = clean_handle.split(":")[-1]
                self.identity_repo.upsert_external_identity(
                    ExternalIdentityEntity(
                        id=generate_identity_id("ext_"),
                        entity_type="person",
                        entity_id=person.id,
                        provider="linkedin",
                        external_id=slug,
                        external_url=linkedin_url,
                    )
                )

        # 5. Link employment if company and title are specified
        employment: Optional[EmploymentEntity] = None
        if company_id:
            canon_company_id = self.resolve_canonical_id(company_id)
            emp_title = title or "Team Member"
            norm_title = emp_title.strip().lower()
            emp_id = generate_identity_id("rel_")
            emp = EmploymentEntity(
                id=emp_id,
                person_id=person.id,
                company_id=canon_company_id,
                title=emp_title,
                normalized_title=norm_title,
                is_current=True,
                source_id=source_id,
            )
            employment = self.employment_repo.upsert(emp)

        return person, employment

    # -------------------------------------------------------------------------
    # Locations
    # -------------------------------------------------------------------------
    def add_location(
        self,
        company_id: str,
        name: str,
        city: Optional[str] = None,
        region: Optional[str] = None,
        country_code: Optional[str] = None,
        postal_code: Optional[str] = None,
        is_primary: bool = True,
        location_type: str = "office",
        source_id: Optional[str] = None,
    ) -> LocationEntity:
        """
        Creates and links a location entity to a canonical company.
        """
        canon_company_id = self.resolve_canonical_id(company_id)
        norm_name = name.strip().lower()

        location_id = generate_identity_id("loc_")
        location = LocationEntity(
            id=location_id,
            name=name,
            normalized_name=norm_name,
            city=city,
            region=region,
            country_code=country_code.upper() if country_code else None,
            postal_code=postal_code,
            location_type=location_type,
        )
        saved_loc = self.identity_repo.upsert_location(location)

        link = CompanyLocationEntity(
            company_id=canon_company_id,
            location_id=saved_loc.id,
            relationship_type=location_type,
            is_primary=is_primary,
            confidence=1.0,
        )
        self.identity_repo.link_company_location(link)

        self.identity_repo.record_event(
            create_identity_event(
                entity_type="company",
                entity_id=canon_company_id,
                event_type="location_added",
                payload={"location_id": saved_loc.id, "city": city, "country_code": country_code},
                source_id=source_id,
            )
        )
        return saved_loc

    # -------------------------------------------------------------------------
    # Brands
    # -------------------------------------------------------------------------
    def add_brand(
        self,
        company_id: str,
        brand_name: str,
        domain: Optional[str] = None,
        source_id: Optional[str] = None,
    ) -> BrandEntity:
        """
        Creates and associates a brand with a canonical company.
        """
        canon_company_id = self.resolve_canonical_id(company_id)
        norm_brand = normalize_company_name(brand_name)

        existing = self.identity_repo.get_brand_by_normalized_name(canon_company_id, norm_brand)
        if existing:
            return existing

        primary_dom_id = None
        if domain:
            dom_ent = self.get_or_create_domain(domain, source_id=source_id)
            primary_dom_id = dom_ent.id

        brand_id = generate_identity_id("brd_")
        brand = BrandEntity(
            id=brand_id,
            canonical_name=brand_name,
            normalized_name=norm_brand,
            company_id=canon_company_id,
            primary_domain_id=primary_dom_id,
        )
        saved_brand = self.identity_repo.upsert_brand(brand)

        self.identity_repo.record_event(
            create_identity_event(
                entity_type="company",
                entity_id=canon_company_id,
                event_type="brand_created",
                payload={"brand_id": saved_brand.id, "brand_name": brand_name},
                source_id=source_id,
            )
        )
        return saved_brand

    # -------------------------------------------------------------------------
    # Company Relationships
    # -------------------------------------------------------------------------
    def add_company_relationship(
        self,
        from_company_id: str,
        to_company_id: str,
        relationship_type: str,
        confidence: float = 1.0,
        source_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CompanyRelationshipEntity:
        """
        Establishes a relationship link between two canonical companies (e.g. parent, subsidiary, partner).
        """
        canon_from = self.resolve_canonical_id(from_company_id)
        canon_to = self.resolve_canonical_id(to_company_id)

        rel_id = generate_identity_id("rel_")
        rel = CompanyRelationshipEntity(
            id=rel_id,
            from_company_id=canon_from,
            to_company_id=canon_to,
            relationship_type=relationship_type,
            confidence=confidence,
            source_id=source_id,
            metadata_json=metadata or {},
        )
        saved_rel = self.identity_repo.upsert_relationship(rel)

        self.identity_repo.record_event(
            create_identity_event(
                entity_type="company",
                entity_id=canon_from,
                event_type="relationship_added",
                payload={"to_company_id": canon_to, "relationship_type": relationship_type},
                source_id=source_id,
            )
        )
        return saved_rel

    # -------------------------------------------------------------------------
    # Entity Merges & Redirects
    # -------------------------------------------------------------------------
    def merge_entities(
        self,
        entity_type: str,
        source_entity_id: str,
        target_entity_id: str,
        reason: str,
        method: str = "manual",
        confidence: float = 1.0,
        created_by: str = "system",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EntityMergeEntity:
        """
        Records a merge redirection from source_entity_id to target_entity_id.
        CRITICAL RULE: The source entity is NEVER deleted.
        """
        if source_entity_id == target_entity_id:
            raise ValueError("Cannot merge an entity into itself")

        # Resolve surviving target in case target was also merged
        target_entity_id = self.resolve_canonical_id(target_entity_id)

        merge = create_entity_merge(
            entity_type=entity_type,
            source_entity_id=source_entity_id,
            target_entity_id=target_entity_id,
            reason=reason,
            method=method,
            confidence=confidence,
            created_by=created_by,
            metadata=metadata,
        )
        saved_merge = self.identity_repo.record_merge(merge)

        # Audit event on source entity
        self.identity_repo.record_event(
            create_identity_event(
                entity_type=entity_type,
                entity_id=source_entity_id,
                event_type="entity_merged",
                payload={"merged_into": target_entity_id, "reason": reason, "method": method},
                actor_type=created_by,
            )
        )
        return saved_merge

    def resolve_canonical_id(self, entity_id: str) -> str:
        """
        Recursively follows entity merge redirects to return the surviving canonical ID.
        """
        if not entity_id:
            return ""
        return self.identity_repo.resolve_canonical_id(entity_id)

    # -------------------------------------------------------------------------
    # Candidates
    # -------------------------------------------------------------------------
    def create_candidate(
        self,
        entity_type: str,
        candidate_key: str,
        payload: Dict[str, Any],
        source_id: Optional[str] = None,
    ) -> IdentityCandidateEntity:
        """
        Queues an ambiguous observation for human or asynchronous resolution.
        """
        cand_id = generate_identity_id("cand_")
        candidate = IdentityCandidateEntity(
            id=cand_id,
            entity_type=entity_type,
            candidate_payload_json=payload,
            candidate_key=candidate_key,
            source_id=source_id,
            status="pending",
        )
        saved = self.identity_repo.create_candidate(candidate)
        self.identity_repo.record_event(
            create_identity_event(
                entity_type="candidate",
                entity_id=saved.id,
                event_type="candidate_created",
                payload={"candidate_key": candidate_key, "entity_type": entity_type},
                source_id=source_id,
            )
        )
        return saved

    def resolve_candidate(
        self,
        candidate_id: str,
        status: str,
        resolved_entity_id: Optional[str] = None,
    ) -> Optional[IdentityCandidateEntity]:
        """
        Resolves or rejects a queued identity candidate.
        """
        resolved = self.identity_repo.resolve_candidate(candidate_id, status, resolved_entity_id)
        if resolved:
            self.identity_repo.record_event(
                create_identity_event(
                    entity_type="candidate",
                    entity_id=candidate_id,
                    event_type="candidate_resolved",
                    payload={"status": status, "resolved_entity_id": resolved_entity_id},
                )
            )
        return resolved


identity_service = IdentityService()
