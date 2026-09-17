"""
Staging environment configuration.
"""

from growx_crawl.config.environments.base import (
    AppEnvironmentConfig,
    DatabaseConfig,
    EnvironmentType,
    ObjectStorageConfig,
    WorkerConfig,
)


def get_staging_config() -> AppEnvironmentConfig:
    config = AppEnvironmentConfig(
        environment=EnvironmentType.STAGING,
        structured_logging=True,
        log_level="INFO",
        database=DatabaseConfig(
            pool_min=2,
            pool_max=15,
            ssl_mode="require",
        ),
        object_store=ObjectStorageConfig(
            provider="r2",
            bucket_raw="growx-staging-raw",
            bucket_private="growx-staging-private",
            bucket_exports="growx-staging-exports",
        ),
        workers=WorkerConfig(
            crawler_concurrency=8,
            browser_concurrency=2,
            browser_memory_limit_mb=1024,
            browser_recycle_pages=50,
            lease_timeout_seconds=300,
            heartbeat_interval_seconds=30,
        ),
    )
    return config
