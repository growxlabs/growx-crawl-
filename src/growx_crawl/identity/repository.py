from abc import ABC, abstractmethod
import json
import logging
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from growx_crawl.identity.merge import resolve_canonical_id_chain
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
from growx_crawl.storage.db import get_db
from growx_crawl.storage.sqlite.canonical import init_sqlite_canonical_tables

logger = logging.getLogger("growx_crawl.identity.repository")


class BaseIdentityRepository(ABC):
    # Locations
    @abstractmethod
    def get_location(self, location_id: str) -> Optional[LocationEntity]: ...

    @abstractmethod
    def upsert_location(self, location: LocationEntity) -> LocationEntity: ...

    @abstractmethod
    def link_company_location(self, link: CompanyLocationEntity) -> CompanyLocationEntity: ...

    @abstractmethod
    def list_company_locations(self, company_id: str) -> List[Tuple[CompanyLocationEntity, LocationEntity]]: ...

    # Brands
    @abstractmethod
    def get_brand(self, brand_id: str) -> Optional[BrandEntity]: ...

    @abstractmethod
    def upsert_brand(self, brand: BrandEntity) -> BrandEntity: ...

    @abstractmethod
    def list_company_brands(self, company_id: str) -> List[BrandEntity]: ...

    @abstractmethod
    def get_brand_by_normalized_name(self, company_id: str, normalized_name: str) -> Optional[BrandEntity]: ...

    # Person Aliases
    @abstractmethod
    def add_person_alias(self, alias: PersonAliasEntity) -> PersonAliasEntity: ...

    @abstractmethod
    def list_person_aliases(self, person_id: str) -> List[PersonAliasEntity]: ...

    # Company Relationships
    @abstractmethod
    def upsert_relationship(self, rel: CompanyRelationshipEntity) -> CompanyRelationshipEntity: ...

    @abstractmethod
    def list_relationships(self, company_id: str) -> List[CompanyRelationshipEntity]: ...

    # External Identities
    @abstractmethod
    def get_external_identity(self, provider: str, external_id: str) -> Optional[ExternalIdentityEntity]: ...

    @abstractmethod
    def upsert_external_identity(self, ext: ExternalIdentityEntity) -> ExternalIdentityEntity: ...

    @abstractmethod
    def list_external_identities(self, entity_type: str, entity_id: str) -> List[ExternalIdentityEntity]: ...

    # Identity Keys
    @abstractmethod
    def get_key(self, key_type: str, key_value: str) -> Optional[IdentityKeyEntity]: ...

    @abstractmethod
    def upsert_key(self, key: IdentityKeyEntity) -> IdentityKeyEntity: ...

    # Identity Candidates
    @abstractmethod
    def create_candidate(self, candidate: IdentityCandidateEntity) -> IdentityCandidateEntity: ...

    @abstractmethod
    def get_candidate(self, candidate_id: str) -> Optional[IdentityCandidateEntity]: ...

    @abstractmethod
    def list_candidates(self, status: str = "pending", limit: int = 50) -> List[IdentityCandidateEntity]: ...

    @abstractmethod
    def resolve_candidate(self, candidate_id: str, status: str, resolved_entity_id: Optional[str] = None) -> Optional[IdentityCandidateEntity]: ...

    # Merges & Redirects
    @abstractmethod
    def record_merge(self, merge: EntityMergeEntity) -> EntityMergeEntity: ...

    @abstractmethod
    def get_merge_target(self, source_entity_id: str) -> Optional[str]: ...

    def resolve_canonical_id(self, entity_id: str) -> str:
        return resolve_canonical_id_chain(entity_id, self.get_merge_target)

    # Identity Events
    @abstractmethod
    def record_event(self, event: IdentityEventEntity) -> IdentityEventEntity: ...

    @abstractmethod
    def list_events(self, entity_type: str, entity_id: str, limit: int = 50) -> List[IdentityEventEntity]: ...


class SqliteIdentityRepository(BaseIdentityRepository):
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def _ensure_schema(self, conn: sqlite3.Connection):
        init_sqlite_canonical_tables(conn)

    # Locations
    def get_location(self, location_id: str) -> Optional[LocationEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute("SELECT * FROM canonical_locations WHERE id = ?", (location_id,)).fetchone()
            if not row:
                return None
            return self._row_to_location(row)

    def upsert_location(self, location: LocationEntity) -> LocationEntity:
        sql = """
            INSERT INTO canonical_locations (
                id, name, normalized_name, city, region, country_code, postal_code,
                latitude, longitude, location_type, created_at, updated_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET
                name = excluded.name,
                normalized_name = excluded.normalized_name,
                city = coalesce(excluded.city, canonical_locations.city),
                region = coalesce(excluded.region, canonical_locations.region),
                country_code = coalesce(excluded.country_code, canonical_locations.country_code),
                postal_code = coalesce(excluded.postal_code, canonical_locations.postal_code),
                latitude = coalesce(excluded.latitude, canonical_locations.latitude),
                longitude = coalesce(excluded.longitude, canonical_locations.longitude),
                location_type = excluded.location_type,
                updated_at = excluded.updated_at,
                metadata_json = excluded.metadata_json;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    location.id,
                    location.name,
                    location.normalized_name,
                    location.city,
                    location.region,
                    location.country_code,
                    location.postal_code,
                    location.latitude,
                    location.longitude,
                    location.location_type,
                    location.created_at,
                    location.updated_at,
                    json.dumps(location.metadata_json),
                ),
            )
        return location

    def link_company_location(self, link: CompanyLocationEntity) -> CompanyLocationEntity:
        sql = """
            INSERT INTO canonical_company_locations (
                company_id, location_id, relationship_type, is_primary, confidence,
                first_seen_at, last_seen_at, last_verified_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (company_id, location_id) DO UPDATE SET
                relationship_type = excluded.relationship_type,
                is_primary = excluded.is_primary,
                confidence = excluded.confidence,
                last_seen_at = excluded.last_seen_at,
                last_verified_at = coalesce(excluded.last_verified_at, canonical_company_locations.last_verified_at);
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    link.company_id,
                    link.location_id,
                    link.relationship_type,
                    1 if link.is_primary else 0,
                    link.confidence,
                    link.first_seen_at,
                    link.last_seen_at,
                    link.last_verified_at,
                ),
            )
        return link

    def list_company_locations(self, company_id: str) -> List[Tuple[CompanyLocationEntity, LocationEntity]]:
        sql = """
            SELECT cl.*, l.* FROM canonical_company_locations cl
            JOIN canonical_locations l ON cl.location_id = l.id
            WHERE cl.company_id = ?
            ORDER BY cl.is_primary DESC, cl.confidence DESC;
        """
        results = []
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(sql, (company_id,)).fetchall()
            for r in rows:
                link = CompanyLocationEntity(
                    company_id=r["company_id"],
                    location_id=r["location_id"],
                    relationship_type=r["relationship_type"],
                    is_primary=bool(r["is_primary"]),
                    confidence=float(r["confidence"]),
                    first_seen_at=r["first_seen_at"],
                    last_seen_at=r["last_seen_at"],
                    last_verified_at=r["last_verified_at"],
                )
                loc = self._row_to_location(r)
                results.append((link, loc))
        return results

    # Brands
    def get_brand(self, brand_id: str) -> Optional[BrandEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute("SELECT * FROM canonical_brands WHERE id = ?", (brand_id,)).fetchone()
            return self._row_to_brand(row) if row else None

    def upsert_brand(self, brand: BrandEntity) -> BrandEntity:
        sql = """
            INSERT INTO canonical_brands (
                id, canonical_name, normalized_name, company_id, primary_domain_id,
                first_seen_at, last_seen_at, created_at, updated_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET
                canonical_name = excluded.canonical_name,
                normalized_name = excluded.normalized_name,
                primary_domain_id = coalesce(excluded.primary_domain_id, canonical_brands.primary_domain_id),
                last_seen_at = excluded.last_seen_at,
                updated_at = excluded.updated_at,
                metadata_json = excluded.metadata_json;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    brand.id,
                    brand.canonical_name,
                    brand.normalized_name,
                    brand.company_id,
                    brand.primary_domain_id,
                    brand.first_seen_at,
                    brand.last_seen_at,
                    brand.created_at,
                    brand.updated_at,
                    json.dumps(brand.metadata_json),
                ),
            )
        return brand

    def list_company_brands(self, company_id: str) -> List[BrandEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute("SELECT * FROM canonical_brands WHERE company_id = ? ORDER BY updated_at DESC", (company_id,)).fetchall()
            return [self._row_to_brand(r) for r in rows]

    def get_brand_by_normalized_name(self, company_id: str, normalized_name: str) -> Optional[BrandEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute(
                "SELECT * FROM canonical_brands WHERE company_id = ? AND normalized_name = ? LIMIT 1",
                (company_id, normalized_name),
            ).fetchone()
            return self._row_to_brand(row) if row else None

    # Person Aliases
    def add_person_alias(self, alias: PersonAliasEntity) -> PersonAliasEntity:
        sql = """
            INSERT INTO canonical_person_aliases (
                id, person_id, alias, normalized_alias, alias_type, source_id, confidence, first_seen_at, last_seen_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET
                alias = excluded.alias,
                normalized_alias = excluded.normalized_alias,
                alias_type = excluded.alias_type,
                last_seen_at = excluded.last_seen_at;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    alias.id,
                    alias.person_id,
                    alias.alias,
                    alias.normalized_alias,
                    alias.alias_type,
                    alias.source_id,
                    alias.confidence,
                    alias.first_seen_at,
                    alias.last_seen_at,
                ),
            )
        return alias

    def list_person_aliases(self, person_id: str) -> List[PersonAliasEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute("SELECT * FROM canonical_person_aliases WHERE person_id = ?", (person_id,)).fetchall()
            return [
                PersonAliasEntity(
                    id=r["id"],
                    person_id=r["person_id"],
                    alias=r["alias"],
                    normalized_alias=r["normalized_alias"],
                    alias_type=r["alias_type"],
                    source_id=r["source_id"],
                    confidence=float(r["confidence"]),
                    first_seen_at=r["first_seen_at"],
                    last_seen_at=r["last_seen_at"],
                )
                for r in rows
            ]

    # Company Relationships
    def upsert_relationship(self, rel: CompanyRelationshipEntity) -> CompanyRelationshipEntity:
        sql = """
            INSERT INTO canonical_company_relationships (
                id, from_company_id, to_company_id, relationship_type, confidence,
                source_id, first_seen_at, last_seen_at, last_verified_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET
                relationship_type = excluded.relationship_type,
                confidence = excluded.confidence,
                last_seen_at = excluded.last_seen_at,
                last_verified_at = coalesce(excluded.last_verified_at, canonical_company_relationships.last_verified_at),
                metadata_json = excluded.metadata_json;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    rel.id,
                    rel.from_company_id,
                    rel.to_company_id,
                    rel.relationship_type,
                    rel.confidence,
                    rel.source_id,
                    rel.first_seen_at,
                    rel.last_seen_at,
                    rel.last_verified_at,
                    json.dumps(rel.metadata_json),
                ),
            )
        return rel

    def list_relationships(self, company_id: str) -> List[CompanyRelationshipEntity]:
        sql = """
            SELECT * FROM canonical_company_relationships
            WHERE from_company_id = ? OR to_company_id = ?
            ORDER BY last_seen_at DESC;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(sql, (company_id, company_id)).fetchall()
            return [self._row_to_relationship(r) for r in rows]

    # External Identities
    def get_external_identity(self, provider: str, external_id: str) -> Optional[ExternalIdentityEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute(
                "SELECT * FROM canonical_external_identities WHERE provider = ? AND external_id = ?",
                (provider.strip().lower(), external_id.strip()),
            ).fetchone()
            return self._row_to_external_identity(row) if row else None

    def upsert_external_identity(self, ext: ExternalIdentityEntity) -> ExternalIdentityEntity:
        sql = """
            INSERT INTO canonical_external_identities (
                id, entity_type, entity_id, provider, external_id, external_url,
                first_seen_at, last_seen_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (provider, external_id) DO UPDATE SET
                entity_id = excluded.entity_id,
                external_url = coalesce(excluded.external_url, canonical_external_identities.external_url),
                last_seen_at = excluded.last_seen_at,
                metadata_json = excluded.metadata_json;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    ext.id,
                    ext.entity_type,
                    ext.entity_id,
                    ext.provider.strip().lower(),
                    ext.external_id.strip(),
                    ext.external_url,
                    ext.first_seen_at,
                    ext.last_seen_at,
                    json.dumps(ext.metadata_json),
                ),
            )
        return ext

    def list_external_identities(self, entity_type: str, entity_id: str) -> List[ExternalIdentityEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(
                "SELECT * FROM canonical_external_identities WHERE entity_type = ? AND entity_id = ?",
                (entity_type, entity_id),
            ).fetchall()
            return [self._row_to_external_identity(r) for r in rows]

    # Identity Keys
    def get_key(self, key_type: str, key_value: str) -> Optional[IdentityKeyEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute(
                "SELECT * FROM canonical_identity_keys WHERE key_type = ? AND key_value = ?",
                (key_type.strip().lower(), key_value.strip()),
            ).fetchone()
            if not row:
                return None
            return IdentityKeyEntity(
                id=row["id"],
                entity_type=row["entity_type"],
                entity_id=row["entity_id"],
                key_type=row["key_type"],
                key_value=row["key_value"],
                is_unique=bool(row["is_unique"]),
                created_at=row["created_at"],
                last_verified_at=row["last_verified_at"],
            )

    def upsert_key(self, key: IdentityKeyEntity) -> IdentityKeyEntity:
        sql = """
            INSERT INTO canonical_identity_keys (
                id, entity_type, entity_id, key_type, key_value, is_unique, created_at, last_verified_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (key_type, key_value) DO UPDATE SET
                entity_id = excluded.entity_id,
                last_verified_at = excluded.last_verified_at;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    key.id,
                    key.entity_type,
                    key.entity_id,
                    key.key_type.strip().lower(),
                    key.key_value.strip(),
                    1 if key.is_unique else 0,
                    key.created_at,
                    key.last_verified_at,
                ),
            )
        return key

    # Identity Candidates
    def create_candidate(self, candidate: IdentityCandidateEntity) -> IdentityCandidateEntity:
        sql = """
            INSERT INTO canonical_identity_candidates (
                id, entity_type, candidate_payload_json, candidate_key, source_id,
                status, created_at, resolved_at, resolved_entity_id, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO NOTHING;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    candidate.id,
                    candidate.entity_type,
                    json.dumps(candidate.candidate_payload_json),
                    candidate.candidate_key,
                    candidate.source_id,
                    candidate.status,
                    candidate.created_at,
                    candidate.resolved_at,
                    candidate.resolved_entity_id,
                    json.dumps(candidate.metadata_json),
                ),
            )
        return candidate

    def get_candidate(self, candidate_id: str) -> Optional[IdentityCandidateEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute("SELECT * FROM canonical_identity_candidates WHERE id = ?", (candidate_id,)).fetchone()
            return self._row_to_candidate(row) if row else None

    def list_candidates(self, status: str = "pending", limit: int = 50) -> List[IdentityCandidateEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(
                "SELECT * FROM canonical_identity_candidates WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                (status, limit),
            ).fetchall()
            return [self._row_to_candidate(r) for r in rows]

    def resolve_candidate(self, candidate_id: str, status: str, resolved_entity_id: Optional[str] = None) -> Optional[IdentityCandidateEntity]:
        from datetime import datetime, timezone
        now_iso = datetime.now(timezone.utc).isoformat()
        sql = """
            UPDATE canonical_identity_candidates
            SET status = ?, resolved_at = ?, resolved_entity_id = ?
            WHERE id = ?;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(sql, (status, now_iso, resolved_entity_id, candidate_id))
        return self.get_candidate(candidate_id)

    # Merges & Redirects
    def record_merge(self, merge: EntityMergeEntity) -> EntityMergeEntity:
        sql = """
            INSERT INTO canonical_entity_merges (
                id, entity_type, source_entity_id, target_entity_id, reason,
                method, confidence, created_at, created_by, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO NOTHING;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    merge.id,
                    merge.entity_type,
                    merge.source_entity_id,
                    merge.target_entity_id,
                    merge.reason,
                    merge.method,
                    merge.confidence,
                    merge.created_at,
                    merge.created_by,
                    json.dumps(merge.metadata_json),
                ),
            )
        return merge

    def get_merge_target(self, source_entity_id: str) -> Optional[str]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            row = conn.execute(
                "SELECT target_entity_id FROM canonical_entity_merges WHERE source_entity_id = ? ORDER BY created_at DESC LIMIT 1",
                (source_entity_id,),
            ).fetchone()
            return row["target_entity_id"] if row else None

    # Identity Events
    def record_event(self, event: IdentityEventEntity) -> IdentityEventEntity:
        sql = """
            INSERT INTO canonical_identity_events (
                id, entity_type, entity_id, event_type, payload_json, source_id, created_at, actor_type, actor_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO NOTHING;
        """
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            conn.execute(
                sql,
                (
                    event.id,
                    event.entity_type,
                    event.entity_id,
                    event.event_type,
                    json.dumps(event.payload_json),
                    event.source_id,
                    event.created_at,
                    event.actor_type,
                    event.actor_id,
                ),
            )
        return event

    def list_events(self, entity_type: str, entity_id: str, limit: int = 50) -> List[IdentityEventEntity]:
        with get_db(self.db_path) as conn:
            self._ensure_schema(conn)
            rows = conn.execute(
                "SELECT * FROM canonical_identity_events WHERE entity_type = ? AND entity_id = ? ORDER BY created_at DESC LIMIT ?",
                (entity_type, entity_id, limit),
            ).fetchall()
            return [
                IdentityEventEntity(
                    id=r["id"],
                    entity_type=r["entity_type"],
                    entity_id=r["entity_id"],
                    event_type=r["event_type"],
                    payload_json=json.loads(r["payload_json"]) if isinstance(r["payload_json"], str) else (r["payload_json"] or {}),
                    source_id=r["source_id"],
                    created_at=r["created_at"],
                    actor_type=r["actor_type"],
                    actor_id=r["actor_id"],
                )
                for r in rows
            ]

    # Row Helpers
    def _row_to_location(self, r) -> LocationEntity:
        meta = r["metadata_json"]
        if isinstance(meta, str):
            meta = json.loads(meta)
        return LocationEntity(
            id=r["id"],
            name=r["name"],
            normalized_name=r["normalized_name"],
            city=r["city"],
            region=r["region"],
            country_code=r["country_code"],
            postal_code=r["postal_code"],
            latitude=float(r["latitude"]) if r["latitude"] is not None else None,
            longitude=float(r["longitude"]) if r["longitude"] is not None else None,
            location_type=r["location_type"],
            created_at=r["created_at"],
            updated_at=r["updated_at"],
            metadata_json=meta or {},
        )

    def _row_to_brand(self, r) -> BrandEntity:
        meta = r["metadata_json"]
        if isinstance(meta, str):
            meta = json.loads(meta)
        return BrandEntity(
            id=r["id"],
            canonical_name=r["canonical_name"],
            normalized_name=r["normalized_name"],
            company_id=r["company_id"],
            primary_domain_id=r["primary_domain_id"],
            first_seen_at=r["first_seen_at"],
            last_seen_at=r["last_seen_at"],
            created_at=r["created_at"],
            updated_at=r["updated_at"],
            metadata_json=meta or {},
        )

    def _row_to_relationship(self, r) -> CompanyRelationshipEntity:
        meta = r["metadata_json"]
        if isinstance(meta, str):
            meta = json.loads(meta)
        return CompanyRelationshipEntity(
            id=r["id"],
            from_company_id=r["from_company_id"],
            to_company_id=r["to_company_id"],
            relationship_type=r["relationship_type"],
            confidence=float(r["confidence"]),
            source_id=r["source_id"],
            first_seen_at=r["first_seen_at"],
            last_seen_at=r["last_seen_at"],
            last_verified_at=r["last_verified_at"],
            metadata_json=meta or {},
        )

    def _row_to_external_identity(self, r) -> ExternalIdentityEntity:
        meta = r["metadata_json"]
        if isinstance(meta, str):
            meta = json.loads(meta)
        return ExternalIdentityEntity(
            id=r["id"],
            entity_type=r["entity_type"],
            entity_id=r["entity_id"],
            provider=r["provider"],
            external_id=r["external_id"],
            external_url=r["external_url"],
            first_seen_at=r["first_seen_at"],
            last_seen_at=r["last_seen_at"],
            metadata_json=meta or {},
        )

    def _row_to_candidate(self, r) -> IdentityCandidateEntity:
        payload = r["candidate_payload_json"]
        if isinstance(payload, str):
            payload = json.loads(payload)
        meta = r["metadata_json"]
        if isinstance(meta, str):
            meta = json.loads(meta)
        return IdentityCandidateEntity(
            id=r["id"],
            entity_type=r["entity_type"],
            candidate_payload_json=payload or {},
            candidate_key=r["candidate_key"],
            source_id=r["source_id"],
            status=r["status"],
            created_at=r["created_at"],
            resolved_at=r["resolved_at"],
            resolved_entity_id=r["resolved_entity_id"],
            metadata_json=meta or {},
        )
