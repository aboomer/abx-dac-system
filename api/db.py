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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS dac_paths (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL UNIQUE,
                notes       TEXT,
                created_at  TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS session_setups (
                id                   INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id           INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
                name                 TEXT NOT NULL,
                gap_mode             TEXT NOT NULL DEFAULT 'fixed'
                                         CHECK (gap_mode IN ('fixed','wait_button')),
                gap_seconds          REAL NOT NULL DEFAULT 3.0,
                vibrate_after_trial  INTEGER NOT NULL DEFAULT 0 CHECK (vibrate_after_trial IN (0,1)),
                identity_mode        TEXT NOT NULL DEFAULT 'blind'
                                         CHECK (identity_mode IN ('blind','alias','visible')),
                num_trials           INTEGER NOT NULL DEFAULT 16,
                play_whole_track     INTEGER NOT NULL DEFAULT 0 CHECK (play_whole_track IN (0,1)),
                randomise_sequence   INTEGER NOT NULL DEFAULT 1 CHECK (randomise_sequence IN (0,1)),
                created_at           TEXT NOT NULL,
                updated_at           TEXT NOT NULL,
                UNIQUE (profile_id, name)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS playlist_songs (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                session_setup_id INTEGER NOT NULL REFERENCES session_setups(id) ON DELETE CASCADE,
                position         INTEGER NOT NULL,
                title            TEXT NOT NULL,
                artist           TEXT,
                album            TEXT,
                service          TEXT,
                uri              TEXT,
                duration_seconds REAL,
                album_art_url    TEXT,
                added_at         TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_playlist_songs_setup ON playlist_songs(session_setup_id)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS playlist_segments (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                song_id        INTEGER NOT NULL REFERENCES playlist_songs(id) ON DELETE CASCADE,
                position       INTEGER NOT NULL,
                start_seconds  REAL,
                end_seconds    REAL,
                description    TEXT,
                created_at     TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_playlist_segments_song ON playlist_segments(song_id)")
        conn.commit()
    finally:
        conn.close()
