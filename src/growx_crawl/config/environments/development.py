"""
Development environment configuration.
"""

from growx_crawl.config.environments.base import (
    AppEnvironmentConfig,
    DatabaseConfig,
    EnvironmentType,
    ObjectStorageConfig,
    WorkerConfig,
)


def get_development_config() -> AppEnvironmentConfig:
    config = AppEnvironmentConfig(
        environment=EnvironmentType.DEVELOPMENT,
        structured_logging=False,
        log_level="DEBUG",
        database=DatabaseConfig(
            database_url=None,
            pool_min=1,
            pool_max=5,
            ssl_mode="disable",
        ),
        object_store=ObjectStorageConfig(
            provider="local",
            local_root_dir="./data/objects",
            bucket_raw="growx-dev-raw",
            bucket_private="growx-dev-private",
            bucket_exports="growx-dev-exports",
        ),
        workers=WorkerConfig(
            crawler_concurrency=4,
            browser_concurrency=1,
            browser_memory_limit_mb=512,
            browser_recycle_pages=20,
            lease_timeout_seconds=120,
            heartbeat_interval_seconds=10,
        ),
    )
    return config
