"""
SQLite connection handling.

Every service call does:
    with database.session() as conn:
        ...
which commits on success and rolls back on any error.
"""
import sqlite3
from contextlib import contextmanager

from app import config
from app.models import ALL_MODELS

EXTRA_SQL = [
    # Auth (see app/services/auth_service.py)
    """
    CREATE TABLE IF NOT EXISTS user_credentials (
        user_id INTEGER PRIMARY KEY REFERENCES app_users(id) ON DELETE CASCADE,
        salt TEXT NOT NULL,
        password_hash TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS auth_tokens (
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
        expires_at TEXT NOT NULL
    );
    """,
    # Prediction log (see app/services/prediction_log_service.py)
    """
    CREATE TABLE IF NOT EXISTS prediction_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        kind TEXT NOT NULL,
        request TEXT NOT NULL,
        response TEXT NOT NULL
    );
    """,
]


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def session():
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create all tables and indexes (safe to run many times)."""
    with session() as conn:
        for model in ALL_MODELS:
            conn.execute(model.CREATE_SQL)
            for statement in model.INDEX_SQL:
                conn.execute(statement)
        for statement in EXTRA_SQL:
            conn.execute(statement)


def reset_db() -> None:
    """Drop every table and recreate them. Used by the seed script."""
    with session() as conn:
        conn.execute("PRAGMA foreign_keys = OFF")
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        for table in tables:
            conn.execute(f"DROP TABLE IF EXISTS {table}")
    init_db()
