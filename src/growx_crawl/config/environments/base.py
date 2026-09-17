"""
Base environment configuration schema for GrowX Crawl & AutoGTM Platform.
"""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentType(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class DatabaseConfig(BaseModel):
    database_url: Optional[str] = None
    supabase_url: Optional[str] = None
    pool_min: int = 2
    pool_max: int = 20
    pool_timeout_seconds: float = 30.0
    ssl_mode: str = "prefer"


class ObjectStorageConfig(BaseModel):
    provider: str = "local"  # "local" | "r2"
    account_id: Optional[str] = None
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    bucket_raw: str = "growx-raw"
    bucket_private: str = "growx-private"
    bucket_exports: str = "growx-exports"
    local_root_dir: str = "./data/objects"


class WorkerConfig(BaseModel):
    crawler_concurrency: int = 10
    browser_concurrency: int = 3
    browser_memory_limit_mb: int = 1024
    browser_recycle_pages: int = 50
    lease_timeout_seconds: int = 300
    heartbeat_interval_seconds: int = 30
    max_retries_per_job: int = 3


class NightlyConfig(BaseModel):
    enabled: bool = True
    schedule_cron: str = "0 2 * * *"  # 02:00 AM UTC
    timezone: str = "UTC"
    execution_window_hours: int = 6
    default_segments: List[str] = Field(default_factory=lambda: ["manufacturing_india", "us_b2b_saas"])


class AuthConfig(BaseModel):
    jwt_secret: str = "growx_insecure_dev_secret_change_in_prod"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours
    admin_api_key: Optional[str] = None
    service_tokens: List[str] = Field(default_factory=lambda: ["growx_svc_crawler", "growx_svc_browser", "growx_svc_intelligence", "growx_svc_verification", "growx_svc_coordinator"])


class AlertsConfig(BaseModel):
    slack_webhook_url: Optional[str] = None
    alert_email: Optional[str] = None
    min_alert_interval_seconds: int = 300


class AppEnvironmentConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="GROWX_",
    )

    environment: EnvironmentType = EnvironmentType.DEVELOPMENT
    app_version: str = "1.0.0"
    api_host: str = "0.0.0.0"
    api_port: int = 7411
    log_level: str = "INFO"
    structured_logging: bool = False

    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    object_store: ObjectStorageConfig = Field(default_factory=ObjectStorageConfig)
    workers: WorkerConfig = Field(default_factory=WorkerConfig)
    nightly: NightlyConfig = Field(default_factory=NightlyConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    alerts: AlertsConfig = Field(default_factory=AlertsConfig)
