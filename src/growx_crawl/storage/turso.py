import logging
from typing import Optional, Dict, Any, List
import libsql_client
from growx_crawl.core.config import settings
from growx_crawl.storage.schema import SCHEMA_SQL
from growx_crawl.storage.sqlite.canonical import SQLITE_CANONICAL_SCHEMA_SQL

logger = logging.getLogger("growx_crawl.storage.turso")


def get_turso_endpoint() -> Optional[str]:
    """
    Returns the HTTPS endpoint for Turso LibSQL client.
    Converts libsql:// protocol to https://.
    """
    url = settings.turso_database_url
    if not url:
        return None
    url = url.strip()
    if url.startswith("libsql://"):
        return url.replace("libsql://", "https://", 1)
    return url


def get_turso_client() -> libsql_client.ClientSync:
    """
    Creates and returns a synchronous LibSQL client connected to Turso.
    Raises ValueError if credentials are not configured.
    """
    endpoint = get_turso_endpoint()
    token = settings.turso_auth_token

    if not endpoint or not token:
        raise ValueError(
            "Turso is not fully configured. Set TURSO_DATABASE_URL and TURSO_AUTH_TOKEN in .env"
        )

    return libsql_client.create_client_sync(
        url=endpoint,
        auth_token=token.strip(),
    )


def check_turso_health() -> Dict[str, Any]:
    """
    Performs a lightweight health check against Turso.
    Returns status, sqlite_version, and query duration.
    """
    if not settings.is_turso_configured:
        return {
            "status": "unconfigured",
            "message": "TURSO_DATABASE_URL or TURSO_AUTH_TOKEN is missing",
        }

    try:
        client = get_turso_client()
        res = client.execute("SELECT sqlite_version() as version, datetime('now') as server_time;")
        client.close()

        version = res.rows[0][0] if res.rows else "unknown"
        server_time = res.rows[0][1] if res.rows else "unknown"

        return {
            "status": "healthy",
            "sqlite_version": version,
            "server_time": server_time,
            "endpoint": get_turso_endpoint(),
        }
    except Exception as exc:
        logger.error(f"Turso health check failed: {exc}")
        return {
            "status": "error",
            "message": str(exc),
        }


def init_turso_schema(client: Optional[libsql_client.ClientSync] = None) -> List[str]:
    """
    Initializes both operational and canonical schemas on Turso.
    Executes all DDL statements in SCHEMA_SQL and SQLITE_CANONICAL_SCHEMA_SQL.
    Returns the list of created/verified tables and indexes.
    """
    should_close = False
    if client is None:
        client = get_turso_client()
        should_close = True

    applied = []
    # Combine operational + canonical schemas
    all_sql = f"{SCHEMA_SQL}\n{SQLITE_CANONICAL_SCHEMA_SQL}"
    statements = [stmt.strip() for stmt in all_sql.split(";") if stmt.strip()]

    try:
        for stmt in statements:
            client.execute(stmt)
            tokens = stmt.split()
            if len(tokens) >= 3:
                name = tokens[2]
                if tokens[1].upper() == "INDEX":
                    name = tokens[4] if "IF" in tokens[2].upper() else tokens[2]
                applied.append(name)
        return applied
    finally:
        if should_close:
            client.close()
