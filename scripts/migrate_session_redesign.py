import shutil
import sqlite3

DB_PATH = "/data/db/abx.db"
BACKUP_PATH = "/data/db/abx.db.bak-pre-redesign"

shutil.copy(DB_PATH, BACKUP_PATH)
print(f"Backed up to {BACKUP_PATH}")

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = OFF")

conn.execute("""
    CREATE TABLE session_setups_new (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        test_type TEXT NOT NULL CHECK (test_type IN ('difference','preference')),
        loop_mode TEXT NOT NULL DEFAULT 'loop' CHECK (loop_mode IN ('loop','once')),
        position_mode TEXT NOT NULL DEFAULT 'restart' CHECK (position_mode IN ('restart','continuous')),
        vibrate_after_trial INTEGER NOT NULL DEFAULT 0 CHECK (vibrate_after_trial IN (0,1)),
        num_trials INTEGER NOT NULL DEFAULT 16 CHECK (num_trials > 0 AND num_trials % 2 = 0),
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE (profile_id, name),
        CHECK (loop_mode = 'loop' OR position_mode = 'restart')
    )
""")

conn.execute("""
    INSERT INTO session_setups_new
        (id, profile_id, name, test_type, loop_mode, position_mode,
         vibrate_after_trial, num_trials, created_at, updated_at)
    SELECT
        id, profile_id, name, 'difference', 'loop', 'restart',
        vibrate_after_trial, num_trials, created_at, updated_at
    FROM session_setups
""")
migrated = conn.execute("SELECT COUNT(*) FROM session_setups_new").fetchone()[0]
print(f"Migrated {migrated} session_setups row(s), id-preserved")

conn.execute("DROP TABLE session_setups")
conn.execute("ALTER TABLE session_setups_new RENAME TO session_setups")

conn.execute("DROP TABLE IF EXISTS session_run_trials")
conn.execute("DROP TABLE IF EXISTS session_runs")

conn.execute("""
    CREATE TABLE session_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
        session_setup_id INTEGER REFERENCES session_setups(id) ON DELETE SET NULL,
        session_setup_name TEXT NOT NULL,

        song_id INTEGER REFERENCES playlist_songs(id) ON DELETE SET NULL,
        song_title TEXT NOT NULL,
        song_uri TEXT NOT NULL,

        segment_id INTEGER REFERENCES playlist_segments(id) ON DELETE SET NULL,
        segment_start_seconds REAL NOT NULL,
        segment_end_seconds REAL NOT NULL,
        segment_description TEXT,

        dac_path_1_id INTEGER REFERENCES dac_paths(id) ON DELETE SET NULL,
        dac_path_1_name TEXT NOT NULL,
        dac_path_2_id INTEGER REFERENCES dac_paths(id) ON DELETE SET NULL,
        dac_path_2_name TEXT NOT NULL,

        test_type TEXT NOT NULL CHECK (test_type IN ('difference','preference')),
        loop_mode TEXT NOT NULL CHECK (loop_mode IN ('loop','once')),
        position_mode TEXT NOT NULL CHECK (position_mode IN ('restart','continuous')),
        num_trials INTEGER NOT NULL CHECK (num_trials > 0 AND num_trials % 2 = 0),
        seed INTEGER NOT NULL,

        started_at TEXT NOT NULL,
        completed_at TEXT,
        status TEXT NOT NULL DEFAULT 'in_progress' CHECK (status IN ('in_progress','completed','abandoned')),

        CHECK (dac_path_1_id IS NULL OR dac_path_2_id IS NULL OR dac_path_1_id != dac_path_2_id)
    )
""")
conn.execute("CREATE INDEX idx_session_runs_profile ON session_runs(profile_id)")

conn.execute("""
    CREATE TABLE session_run_trials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_run_id INTEGER NOT NULL REFERENCES session_runs(id) ON DELETE CASCADE,
        trial_index INTEGER NOT NULL CHECK (trial_index >= 0),

        dac_a_path_id INTEGER REFERENCES dac_paths(id) ON DELETE SET NULL,
        dac_a_path_name TEXT NOT NULL,
        dac_b_path_id INTEGER REFERENCES dac_paths(id) ON DELETE SET NULL,
        dac_b_path_name TEXT NOT NULL,

        x_identity TEXT CHECK (x_identity IN ('A','B')),
        vote TEXT CHECK (vote IN ('A','B','no_preference')),
        correct INTEGER CHECK (correct IN (0,1)),

        navigation_count INTEGER NOT NULL DEFAULT 0,
        trial_started_at TEXT NOT NULL,
        responded_at TEXT,

        UNIQUE (session_run_id, trial_index),
        CHECK (dac_a_path_id IS NULL OR dac_b_path_id IS NULL OR dac_a_path_id != dac_b_path_id)
    )
""")
conn.execute("CREATE INDEX idx_session_run_trials_run ON session_run_trials(session_run_id)")

conn.commit()

conn.execute("PRAGMA foreign_keys = ON")
violations = conn.execute("PRAGMA foreign_key_check").fetchall()
if violations:
    print("FOREIGN KEY VIOLATIONS FOUND:")
    for v in violations:
        print(v)
    raise SystemExit(1)
else:
    print("PRAGMA foreign_key_check: clean, no violations")

# Sanity: confirm playlist_songs/playlist_segments survived, still linked
songs = conn.execute("SELECT COUNT(*) FROM playlist_songs").fetchone()[0]
segments = conn.execute("SELECT COUNT(*) FROM playlist_segments").fetchone()[0]
print(f"playlist_songs: {songs} row(s) survived")
print(f"playlist_segments: {segments} row(s) survived")

conn.close()
print("Migration complete.")
