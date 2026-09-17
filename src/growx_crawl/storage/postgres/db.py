from contextlib import contextmanager
import logging
import os
from typing import Any, Generator, Optional

logger = logging.getLogger("growx_crawl.storage.postgres.db")

class StorageConnectionError(Exception):
    """Raised when PostgreSQL / Supabase connection cannot be established in production."""
    pass


class PostgresPool:
    """
    Manages PostgreSQL / Supabase connection pooling using psycopg2 / psycopg.
    """
    _instance: Optional["PostgresPool"] = None
    _pool = None

    def __init__(self, dsn: Optional[str] = None, minconn: int = 2, maxconn: int = 20):
        self.dsn = dsn or os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DATABASE_URL")
        self.minconn = int(os.environ.get("DATABASE_POOL_MIN", minconn))
        self.maxconn = int(os.environ.get("DATABASE_POOL_MAX", maxconn))
        self._init_pool()

    @classmethod
    def get_instance(cls) -> "PostgresPool":
        if cls._instance is None:
            cls._instance = PostgresPool()
        return cls._instance

    def _init_pool(self):
        if not self.dsn:
            logger.debug("No PostgreSQL DATABASE_URL configured yet.")
            return

        try:
            try:
                import psycopg2.pool
                self._pool = psycopg2.pool.ThreadedConnectionPool(
                    minconn=self.minconn,
                    maxconn=self.maxconn,
                    dsn=self.dsn,
                )
                logger.info(f"Initialized PostgreSQL connection pool (min={self.minconn}, max={self.maxconn})")
            except ImportError:
                import psycopg_pool
                self._pool = psycopg_pool.ConnectionPool(
                    conninfo=self.dsn,
                    min_size=self.minconn,
                    max_size=self.maxconn,
                )
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL pool: {e}")
            self._pool = None

    def get_connection(self):
        if not self._pool:
            if not self.dsn:
                raise StorageConnectionError("DATABASE_URL environment variable is not set. Cannot connect to PostgreSQL.")
            self._init_pool()
            if not self._pool:
                raise StorageConnectionError(f"Failed to connect to PostgreSQL / Supabase instance at {self.dsn[:25]}...")
        
        try:
            return self._pool.getconn()
        except Exception as e:
            raise StorageConnectionError(f"Error acquiring connection from PostgreSQL pool: {e}")

    def put_connection(self, conn, close: bool = False):
        if self._pool and conn:
            try:
                self._pool.putconn(conn, close=close)
            except Exception as e:
                logger.warning(f"Error returning connection to pool: {e}")

    def check_health(self) -> bool:
        if not self.dsn:
            return False
        try:
            conn = self.get_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1;")
                    res = cur.fetchone()
                    return bool(res and res[0] == 1)
            finally:
                self.put_connection(conn)
        except Exception as e:
            logger.debug(f"Postgres health check failed: {e}")
            return False


@contextmanager
def get_pg_connection() -> Generator[Any, None, None]:
    """
    Context manager yielding a PostgreSQL connection with automatic commit/rollback.
    """
    pool = PostgresPool.get_instance()
    conn = pool.get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.put_connection(conn)
