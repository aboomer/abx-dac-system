import sqlite3

conn = sqlite3.connect("/data/db/abx.db")
conn.execute("DROP TABLE IF EXISTS session_run_trials")
conn.execute("""
    CREATE TABLE session_run_trials (
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
conn.execute("CREATE INDEX idx_session_run_trials_run ON session_run_trials(session_run_id)")
conn.commit()
print("recreated OK")

violations = conn.execute("PRAGMA foreign_key_check").fetchall()
print("foreign_key_check violations:", violations)
conn.close()
