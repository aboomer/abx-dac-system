import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path("/data/db/abx.db")


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db():
    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL UNIQUE,
                created_at  TEXT NOT NULL
            )
        """)
        conn.commit()
    finally:
        conn.close()
