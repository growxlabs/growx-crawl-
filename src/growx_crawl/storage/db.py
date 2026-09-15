import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator
from growx_crawl.core.config import settings


def get_db_connection(db_path: str = None) -> sqlite3.Connection:
    if db_path is None:
        db_path = settings.db_path
    
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA busy_timeout=10000;")
    return conn


@contextmanager
def get_db(db_path: str = None) -> Generator[sqlite3.Connection, None, None]:
    conn = get_db_connection(db_path)
    # Run migration checks to ensure latest schema tables exist
    from growx_crawl.storage.schema import _migrate_columns
    _migrate_columns(conn)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
