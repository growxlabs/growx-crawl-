import logging
import os
from typing import Optional

from growx_crawl.object_store.base import ObjectStore
from growx_crawl.object_store.errors import ObjectConfigurationError
from growx_crawl.object_store.providers.local import LocalObjectStore
from growx_crawl.object_store.providers.r2 import R2ObjectStore

logger = logging.getLogger("growx_crawl.object_store.factory")

_cached_store: Optional[ObjectStore] = None


def get_active_object_store_type() -> str:
    return os.environ.get("GROWX_OBJECT_STORE", "local").strip().lower()


def get_object_store(force_refresh: bool = False) -> ObjectStore:
    """
    Returns the configured ObjectStore provider (LocalObjectStore or R2ObjectStore).
    Ensures zero cloud SDK coupling across business modules.
    """
    global _cached_store
    if _cached_store is not None and not force_refresh:
        return _cached_store

    store_type = get_active_object_store_type()

    if store_type == "r2":
        account_id = os.environ.get("R2_ACCOUNT_ID")
        access_key = os.environ.get("R2_ACCESS_KEY_ID")
        secret_key = os.environ.get("R2_SECRET_ACCESS_KEY")
        if not access_key or not secret_key:
            raise ObjectConfigurationError(
                "GROWX_OBJECT_STORE is set to 'r2', but R2_ACCESS_KEY_ID or R2_SECRET_ACCESS_KEY is missing. "
                "Configure R2 credentials in .env or set GROWX_OBJECT_STORE=local for offline development."
            )
        _cached_store = R2ObjectStore(
            account_id=account_id,
            access_key_id=access_key,
            secret_access_key=secret_key,
        )
        logger.info("Initialized Cloudflare R2 ObjectStore provider.")
    else:
        root_dir = os.environ.get("LOCAL_OBJECT_ROOT", "./data/objects")
        _cached_store = LocalObjectStore(root_dir=root_dir)
        logger.debug(f"Initialized LocalObjectStore provider at {root_dir}")

    return _cached_store
