import os
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="GROWX_CRAWL_",
    )

    db_path: str = Field(default="data/growx-crawl.db")
    workers: int = Field(default=10)
    max_depth: int = Field(default=2)
    max_pages_per_domain: int = Field(default=10)
    timeout_seconds: float = Field(default=15.0)
    requests_per_second: float = Field(default=2.0)
    user_agent: str = Field(
        default="GrowXCrawl/1.0 (+https://growxlabs.tech/bot)"
    )
    scoring_profile: str = Field(default="jewellery")

    growxlabs_api_base_url: str = Field(
        default="https://growxlabs.tech/api/internal/lead-ingestion"
    )
    growxlabs_api_key: Optional[str] = Field(default=None)

    @property
    def config_dir(self) -> Path:
        return Path(__file__).resolve().parent.parent.parent.parent / "config"


settings = Settings()
