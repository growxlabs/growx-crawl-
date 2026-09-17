"""
Production environment configuration.
"""

from growx_crawl.config.environments.base import (
    AppEnvironmentConfig,
    DatabaseConfig,
    EnvironmentType,
    ObjectStorageConfig,
    WorkerConfig,
)


def get_production_config() -> AppEnvironmentConfig:
    config = AppEnvironmentConfig(
        environment=EnvironmentType.PRODUCTION,
        structured_logging=True,
        log_level="INFO",
        database=DatabaseConfig(
            pool_min=5,
            pool_max=30,
            pool_timeout_seconds=30.0,
            ssl_mode="require",
        ),
        object_store=ObjectStorageConfig(
            provider="r2",
            bucket_raw="growx-prod-raw",
            bucket_private="growx-prod-private",
            bucket_exports="growx-prod-exports",
        ),
        workers=WorkerConfig(
            crawler_concurrency=16,
            browser_concurrency=4,
            browser_memory_limit_mb=1536,
            browser_recycle_pages=50,
            lease_timeout_seconds=300,
            heartbeat_interval_seconds=30,
        ),
    )
    return config
