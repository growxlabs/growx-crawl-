"""
Environment configuration validator for GrowX.
Enforces fail-fast startup checks.
"""

import os
from typing import List, Optional
from growx_crawl.config.environments.base import AppEnvironmentConfig, EnvironmentType


class EnvironmentValidationError(Exception):
    """Raised when critical production configuration is missing or invalid."""
    pass


def validate_environment(config: Optional[AppEnvironmentConfig] = None) -> List[str]:
    """
    Validates the configuration and returns a list of error strings.
    If the list is empty, configuration is valid.
    """
    from growx_crawl.config.environments import get_active_config

    cfg = config or get_active_config()
    errors: List[str] = []

    # Production-specific strict checks
    if cfg.environment == EnvironmentType.PRODUCTION:
        db_url = cfg.database.database_url or os.environ.get("DATABASE_URL")
        if not db_url:
            errors.append("PRODUCTION: Missing canonical PostgreSQL DATABASE_URL.")

        if cfg.object_store.provider == "r2":
            acc_id = cfg.object_store.account_id or os.environ.get("R2_ACCOUNT_ID")
            acc_key = cfg.object_store.access_key_id or os.environ.get("R2_ACCESS_KEY_ID")
            sec_key = cfg.object_store.secret_access_key or os.environ.get("R2_SECRET_ACCESS_KEY")
            if not acc_key or not sec_key:
                errors.append("PRODUCTION: R2 object store enabled, but R2_ACCESS_KEY_ID or R2_SECRET_ACCESS_KEY is missing.")

        if cfg.auth.jwt_secret == "growx_insecure_dev_secret_change_in_prod":
            jwt_env = os.environ.get("GROWX_AUTH_JWT_SECRET") or os.environ.get("JWT_SECRET")
            if not jwt_env or jwt_env == "growx_insecure_dev_secret_change_in_prod":
                errors.append("PRODUCTION: Default insecure JWT secret detected. Set GROWX_AUTH_JWT_SECRET.")

    # General checks for all environments
    if cfg.workers.crawler_concurrency < 1:
        errors.append("Worker crawler_concurrency must be at least 1.")

    if cfg.workers.lease_timeout_seconds < 10:
        errors.append("Worker lease_timeout_seconds must be at least 10 seconds.")

    return errors


def ensure_valid_environment(config: Optional[AppEnvironmentConfig] = None) -> None:
    """Fails fast by raising EnvironmentValidationError if configuration is invalid."""
    errors = validate_environment(config)
    if errors:
        msg = "Environment configuration validation failed:\n" + "\n".join(f"- {e}" for e in errors)
        raise EnvironmentValidationError(msg)
