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
                test_type            TEXT NOT NULL CHECK (test_type IN ('difference','preference')),
                loop_mode            TEXT NOT NULL DEFAULT 'loop'
                                         CHECK (loop_mode IN ('loop','once')),
                position_mode        TEXT NOT NULL DEFAULT 'restart'
                                         CHECK (position_mode IN ('restart','continuous')),
                vibrate_after_trial  INTEGER NOT NULL DEFAULT 0 CHECK (vibrate_after_trial IN (0,1)),
                num_trials           INTEGER NOT NULL DEFAULT 16
                                         CHECK (num_trials > 0 AND num_trials % 2 = 0),
                created_at           TEXT NOT NULL,
                updated_at           TEXT NOT NULL,
                UNIQUE (profile_id, name),
                CHECK (loop_mode = 'loop' OR position_mode = 'restart')
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

        conn.execute("""
            CREATE TABLE IF NOT EXISTS session_runs (
                id                     INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id             INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
                session_setup_id       INTEGER REFERENCES session_setups(id) ON DELETE SET NULL,
                session_setup_name     TEXT NOT NULL,

                song_id                INTEGER REFERENCES playlist_songs(id) ON DELETE SET NULL,
                song_title             TEXT NOT NULL,
                song_uri               TEXT NOT NULL,

                segment_id             INTEGER REFERENCES playlist_segments(id) ON DELETE SET NULL,
                segment_start_seconds  REAL NOT NULL,
                segment_end_seconds    REAL NOT NULL,
                segment_description    TEXT,

                dac_path_1_id          INTEGER REFERENCES dac_paths(id) ON DELETE SET NULL,
                dac_path_1_name        TEXT NOT NULL,
                dac_path_2_id          INTEGER REFERENCES dac_paths(id) ON DELETE SET NULL,
                dac_path_2_name        TEXT NOT NULL,

                test_type              TEXT NOT NULL CHECK (test_type IN ('difference','preference')),
                loop_mode              TEXT NOT NULL CHECK (loop_mode IN ('loop','once')),
                position_mode          TEXT NOT NULL CHECK (position_mode IN ('restart','continuous')),
                num_trials             INTEGER NOT NULL CHECK (num_trials > 0 AND num_trials % 2 = 0),
                seed                   INTEGER NOT NULL,

                started_at             TEXT NOT NULL,
                completed_at           TEXT,
                status                 TEXT NOT NULL DEFAULT 'in_progress'
                                           CHECK (status IN ('in_progress','completed','abandoned')),

                CHECK (dac_path_1_id IS NULL OR dac_path_2_id IS NULL OR dac_path_1_id != dac_path_2_id)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_session_runs_profile ON session_runs(profile_id)")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS session_run_trials (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                session_run_id    INTEGER NOT NULL REFERENCES session_runs(id) ON DELETE CASCADE,
                trial_index       INTEGER NOT NULL CHECK (trial_index >= 0),

                dac_a_path_id     INTEGER REFERENCES dac_paths(id) ON DELETE SET NULL,
                dac_a_path_name   TEXT NOT NULL,
                dac_b_path_id     INTEGER REFERENCES dac_paths(id) ON DELETE SET NULL,
                dac_b_path_name   TEXT NOT NULL,

                x_identity        TEXT CHECK (x_identity IN ('A','B')),
                vote              TEXT CHECK (vote IN ('A','B','no_preference')),
                correct           INTEGER CHECK (correct IN (0,1)),

                navigation_count  INTEGER NOT NULL DEFAULT 0,
                trial_started_at  TEXT,
                responded_at      TEXT,

                UNIQUE (session_run_id, trial_index),
                CHECK (dac_a_path_id IS NULL OR dac_b_path_id IS NULL OR dac_a_path_id != dac_b_path_id)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_session_run_trials_run ON session_run_trials(session_run_id)")

        conn.commit()
    finally:
        conn.close()
