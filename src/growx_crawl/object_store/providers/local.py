import asyncio
from datetime import datetime, timezone
import hashlib
import hmac
import json
import logging
import os
from pathlib import Path
import time
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from growx_crawl.object_store.base import ObjectStore
from growx_crawl.object_store.errors import ObjectNotFound, ObjectStoreError
from growx_crawl.object_store.hashing import compute_sha256, maybe_compress, maybe_decompress
from growx_crawl.object_store.models import ObjectStat

logger = logging.getLogger("growx_crawl.object_store.local")

SIGN_SECRET = os.environ.get("GROWX_SIGN_SECRET", "gx_local_signed_secret_2026")


class LocalObjectStore(ObjectStore):
    """
    Filesystem-backed ObjectStore implementation for local development, offline mode, and testing.
    Stores data in `./data/objects/<bucket>/<key>` with `.meta.json` sidecars.
    """

    def __init__(self, root_dir: Optional[str] = None):
        self.root = Path(root_dir or os.environ.get("LOCAL_OBJECT_ROOT", "./data/objects")).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _get_paths(self, bucket: str, key: str) -> tuple[Path, Path]:
        clean_key = key.lstrip("/\\").replace("\\", "/")
        obj_path = (self.root / bucket / clean_key).resolve()
        # Security check against path traversal
        if not str(obj_path).startswith(str(self.root)):
            raise ObjectStoreError(f"Path traversal detected: {key}")
        meta_path = obj_path.with_name(obj_path.name + ".meta.json")
        return obj_path, meta_path

    async def put(
        self,
        bucket: str,
        key: str,
        data: Union[bytes, str],
        *,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        compress: bool = True,
    ) -> ObjectStat:
        ct = content_type or "application/octet-stream"
        raw_bytes = data.encode("utf-8") if isinstance(data, str) else data
        content_hash = compute_sha256(raw_bytes)

        payload_to_write, is_compressed = maybe_compress(raw_bytes, ct, enable_compression=compress)
        encoding = "gzip" if is_compressed else None

        obj_path, meta_path = self._get_paths(bucket, key)

        def _sync_write():
            obj_path.parent.mkdir(parents=True, exist_ok=True)
            with open(obj_path, "wb") as f:
                f.write(payload_to_write)

            stat_info = {
                "bucket": bucket,
                "key": key,
                "size_bytes": len(raw_bytes),
                "stored_size_bytes": len(payload_to_write),
                "content_type": ct,
                "content_encoding": encoding,
                "content_hash": content_hash,
                "last_modified": datetime.now(timezone.utc).isoformat(),
                "metadata": metadata or {},
            }
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(stat_info, f, indent=2)

            return stat_info

        stat_dict = await asyncio.to_thread(_sync_write)
        return ObjectStat(**stat_dict)

    async def get(self, bucket: str, key: str) -> bytes:
        obj_path, meta_path = self._get_paths(bucket, key)
        if not obj_path.exists():
            raise ObjectNotFound(f"Object not found: {bucket}/{key}")

        def _sync_read():
            with open(obj_path, "rb") as f:
                raw_payload = f.read()

            encoding = None
            if meta_path.exists():
                try:
                    with open(meta_path, "r", encoding="utf-8") as mf:
                        encoding = json.load(mf).get("content_encoding")
                except Exception:
                    pass

            return maybe_decompress(raw_payload, encoding or "")

        return await asyncio.to_thread(_sync_read)

    async def stream(self, bucket: str, key: str, chunk_size: int = 65536) -> AsyncIterator[bytes]:
        full_bytes = await self.get(bucket, key)
        for i in range(0, len(full_bytes), chunk_size):
            yield full_bytes[i : i + chunk_size]

    async def delete(self, bucket: str, key: str) -> bool:
        obj_path, meta_path = self._get_paths(bucket, key)

        def _sync_delete():
            deleted = False
            if obj_path.exists():
                obj_path.unlink()
                deleted = True
            if meta_path.exists():
                meta_path.unlink()
            return deleted

        return await asyncio.to_thread(_sync_delete)

    async def exists(self, bucket: str, key: str) -> bool:
        obj_path, _ = self._get_paths(bucket, key)
        return await asyncio.to_thread(obj_path.exists)

    async def stat(self, bucket: str, key: str) -> ObjectStat:
        obj_path, meta_path = self._get_paths(bucket, key)
        if not obj_path.exists():
            raise ObjectNotFound(f"Object not found: {bucket}/{key}")

        def _sync_stat():
            if meta_path.exists():
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    pass

            size = obj_path.stat().st_size
            mtime = datetime.fromtimestamp(obj_path.stat().st_mtime, timezone.utc).isoformat()
            with open(obj_path, "rb") as f:
                content_hash = compute_sha256(f.read())

            return {
                "bucket": bucket,
                "key": key,
                "size_bytes": size,
                "content_type": "application/octet-stream",
                "content_encoding": None,
                "content_hash": content_hash,
                "last_modified": mtime,
                "metadata": {},
            }

        stat_dict = await asyncio.to_thread(_sync_stat)
        return ObjectStat(**stat_dict)

    async def list(self, bucket: str, prefix: str = "", *, limit: int = 1000) -> List[ObjectStat]:
        bucket_dir = self.root / bucket
        if not bucket_dir.exists():
            return []

        def _sync_list():
            stats = []
            clean_prefix = prefix.lstrip("/\\").replace("\\", "/")
            for root, _, files in os.walk(bucket_dir):
                for f in files:
                    if f.endswith(".meta.json"):
                        continue
                    full_p = Path(root) / f
                    rel_key = full_p.relative_to(bucket_dir).as_posix()
                    if rel_key.startswith(clean_prefix):
                        meta_p = full_p.with_name(full_p.name + ".meta.json")
                        meta_info = {}
                        if meta_p.exists():
                            try:
                                with open(meta_p, "r", encoding="utf-8") as mf:
                                    meta_info = json.load(mf)
                            except Exception:
                                pass

                        stats.append(
                            ObjectStat(
                                bucket=bucket,
                                key=rel_key,
                                size_bytes=meta_info.get("size_bytes", full_p.stat().st_size),
                                content_type=meta_info.get("content_type", "application/octet-stream"),
                                content_encoding=meta_info.get("content_encoding"),
                                content_hash=meta_info.get("content_hash", ""),
                                last_modified=meta_info.get(
                                    "last_modified",
                                    datetime.fromtimestamp(full_p.stat().st_mtime, timezone.utc).isoformat(),
                                ),
                                metadata=meta_info.get("metadata", {}),
                            )
                        )
                        if len(stats) >= limit:
                            return stats
            return stats

        return await asyncio.to_thread(_sync_list)

    async def presign_get(self, bucket: str, key: str, *, expires_in: int = 900) -> str:
        """
        Generates a local signed URL for downloading/inspecting objects.
        Valid for `expires_in` seconds (default 15 minutes).
        """
        expires_at = int(time.time()) + expires_in
        payload = f"{bucket}/{key}:{expires_at}"
        sig = hmac.new(SIGN_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
        return f"/v1/objects/{bucket}/{key}?expires={expires_at}&sig={sig}"

    async def presign_put(self, bucket: str, key: str, *, expires_in: int = 900) -> str:
        expires_at = int(time.time()) + expires_in
        payload = f"PUT:{bucket}/{key}:{expires_at}"
        sig = hmac.new(SIGN_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
        return f"/v1/objects/{bucket}/{key}?method=PUT&expires={expires_at}&sig={sig}"
