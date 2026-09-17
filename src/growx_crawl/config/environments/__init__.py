"""
Environment management and configuration access for GrowX.
"""

import os
from typing import Optional

from growx_crawl.config.environments.base import AppEnvironmentConfig, EnvironmentType
from growx_crawl.config.environments.development import get_development_config
from growx_crawl.config.environments.staging import get_staging_config
from growx_crawl.config.environments.production import get_production_config

_active_config: Optional[AppEnvironmentConfig] = None


def get_active_environment() -> EnvironmentType:
    env_str = os.environ.get("GROWX_ENV", "development").strip().lower()
    if env_str in ("prod", "production", "production-internal"):
        return EnvironmentType.PRODUCTION
    if env_str in ("stage", "staging"):
        return EnvironmentType.STAGING
    return EnvironmentType.DEVELOPMENT


def get_active_config(force_refresh: bool = False) -> AppEnvironmentConfig:
    global _active_config
    if _active_config is not None and not force_refresh:
        return _active_config

    env = get_active_environment()
    if env == EnvironmentType.PRODUCTION:
        _active_config = get_production_config()
    elif env == EnvironmentType.STAGING:
        _active_config = get_staging_config()
    else:
        _active_config = get_development_config()

    return _active_config


active_config = get_active_config()

__all__ = [
    "EnvironmentType",
    "AppEnvironmentConfig",
    "get_active_environment",
    "get_active_config",
    "active_config",
]
