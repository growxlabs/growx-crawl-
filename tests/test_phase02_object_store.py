import os
import pytest
from datetime import datetime, timezone

from growx_crawl.object_store.base import ObjectStore
from growx_crawl.object_store.errors import ObjectConfigurationError, ObjectNotFound
from growx_crawl.object_store.factory import get_object_store, get_active_object_store_type
from growx_crawl.object_store.hashing import compute_sha256
from growx_crawl.object_store.keys import build_object_key, sanitize_filename
from growx_crawl.object_store.models import BucketName, ObjectRefEntity, ObjectType
from growx_crawl.object_store.providers.local import LocalObjectStore
from growx_crawl.storage.factory import StorageFactory


@pytest.mark.asyncio
async def test_local_object_store_crud(tmp_path):
    """Verify LocalObjectStore put, get, stat, exists, stream, and delete."""
    store = LocalObjectStore(root_dir=str(tmp_path / "objects"))
    bucket = BucketName.RAW
    key = "crawl/2026/09/17/cmp_test/run_01/homepage.html"
    content = "<html><body><h1>GrowX Crawl Intelligence</h1></body></html>"

    # 1. Put
    stat = await store.put(
        bucket,
        key,
        content,
        content_type="text/html",
        metadata={"crawler": "fast_http", "status": 200},
        compress=False,
    )
    assert stat.bucket == bucket
    assert stat.key == key
    assert stat.size_bytes == len(content.encode())
    assert stat.content_hash == compute_sha256(content)
    assert stat.metadata.get("crawler") == "fast_http"

    # 2. Exists
    assert await store.exists(bucket, key) is True
    assert await store.exists(bucket, "non/existent/key.bin") is False

    # 3. Get
    retrieved = await store.get(bucket, key)
    assert retrieved.decode("utf-8") == content

    # 4. Stream
    chunks = []
    async for chunk in store.stream(bucket, key, chunk_size=16):
        chunks.append(chunk)
    assert b"".join(chunks).decode("utf-8") == content

    # 5. List
    items = await store.list(bucket, prefix="crawl/2026/09/17")
    assert len(items) == 1
    assert items[0].key == key

    # 6. Delete
    deleted = await store.delete(bucket, key)
    assert deleted is True
    assert await store.exists(bucket, key) is False

    with pytest.raises(ObjectNotFound):
        await store.get(bucket, key)


@pytest.mark.asyncio
async def test_transparent_gzip_compression(tmp_path):
    """Verify text payloads are compressed on disk and transparently decompressed on read."""
    store = LocalObjectStore(root_dir=str(tmp_path / "objects"))
    bucket = BucketName.RAW
    key = "markdown/2026/09/17/cmp_test/run_01/page.md"
    # Large repetitive text that benefits from compression
    content = "# Enterprise Intelligence\n" + ("Fact: GrowX automates B2B pipeline.\n" * 50)

    stat = await store.put(
        bucket,
        key,
        content,
        content_type="text/markdown",
        compress=True,
    )
    assert stat.content_encoding == "gzip"
    assert stat.size_bytes == len(content.encode())

    # Raw file on disk should be smaller than uncompressed bytes
    obj_path, _ = store._get_paths(bucket, key)
    assert obj_path.stat().st_size < len(content.encode())

    # Read should return original uncompressed content
    decompressed = await store.get(bucket, key)
    assert decompressed.decode("utf-8") == content


def test_key_builder_and_sanitization():
    """Verify deterministic key structure and PII/traversal safety."""
    key = build_object_key(
        category="screenshots",
        entity_id="cmp_0191fa2b_a7f92b",
        filename="landing.webp",
        object_id="run_0191fa2b_b8c01a",
        date=datetime(2026, 9, 17, 10, 0, 0, tzinfo=timezone.utc),
    )
    assert key == "screenshots/2026/09/17/cmp_0191fa2b_a7f92b/run_0191fa2b_b8c01a/landing.webp"

    # Traversal sanitization
    unsafe_file = "../../etc/passwd.html"
    clean_file = sanitize_filename(unsafe_file)
    assert ".." not in clean_file
    assert "/" not in clean_file


@pytest.mark.asyncio
async def test_presigned_url_generation(tmp_path):
    """Verify temporary signed URLs contain expiration and cryptographic signature."""
    store = LocalObjectStore(root_dir=str(tmp_path / "objects"))
    bucket = BucketName.EXPORTS
    key = "exports/2026/09/17/leads.xlsx"

    signed_url = await store.presign_get(bucket, key, expires_in=900)
    assert f"/v1/objects/{bucket}/{key}" in signed_url
    assert "expires=" in signed_url
    assert "sig=" in signed_url


def test_factory_and_configuration_safety(monkeypatch):
    """Verify factory respects GROWX_OBJECT_STORE and fails safely on missing R2 keys."""
    monkeypatch.setenv("GROWX_OBJECT_STORE", "local")
    store = get_object_store(force_refresh=True)
    assert isinstance(store, LocalObjectStore)

    monkeypatch.setenv("GROWX_OBJECT_STORE", "r2")
    monkeypatch.delenv("R2_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("R2_SECRET_ACCESS_KEY", raising=False)

    with pytest.raises(ObjectConfigurationError) as exc_info:
        get_object_store(force_refresh=True)
    assert "R2_ACCESS_KEY_ID or R2_SECRET_ACCESS_KEY is missing" in str(exc_info.value)


def test_object_ref_persistence(tmp_path):
    """Verify object reference record can be stored and retrieved in database."""
    db_file = str(tmp_path / "test_obj_refs.db")
    from growx_crawl.storage.sqlite.canonical import SqliteObjectRefRepository
    repo = SqliteObjectRefRepository(db_path=db_file)

    ref = ObjectRefEntity(
        id="obj_0191fa2b_test",
        object_type=ObjectType.RAW_HTML.value,
        bucket=BucketName.RAW,
        object_key="crawl/2026/09/17/cmp_01/run_01/page.html",
        provider="local",
        content_type="text/html",
        content_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        size_bytes=1024,
        source_url="https://growxlabs.tech",
        crawl_run_id="run_0191fa2b_test",
    )
    repo.upsert(ref)

    assert repo.count() == 1
    found = repo.get("obj_0191fa2b_test")
    assert found is not None
    assert found["object_key"] == "crawl/2026/09/17/cmp_01/run_01/page.html"
    assert found["bucket"] == BucketName.RAW
