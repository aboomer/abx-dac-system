import random
import sqlite3

from fastapi import APIRouter, HTTPException

from api import randomization
from api.db import get_connection, utcnow_iso
from api.models import SessionStartIn, SessionRunStartedOut, SessionResultsOut, TrialResultOut

router = APIRouter()

# NOTE: clicker mode-switching and real playback control (TrialPlaybackController)
# are deliberately NOT wired up yet -- that's Stage 5c. This stage is DB plumbing
# only: starting a run creates real, correctly-randomized rows in the database,
# but nothing actually plays yet and the clicker isn't touched.


@router.post("/start", response_model=SessionRunStartedOut)
async def start_session(body: SessionStartIn):
    conn = get_connection()
    try:
        in_progress = conn.execute(
            "SELECT id FROM session_runs WHERE status = 'in_progress'"
        ).fetchone()
        if in_progress:
            raise HTTPException(
                status_code=409,
                detail=f"Session run {in_progress['id']} is already in progress",
            )

        setup = conn.execute(
            "SELECT * FROM session_setups WHERE id = ?", (body.session_setup_id,)
        ).fetchone()
        if not setup:
            raise HTTPException(status_code=404, detail="Session setup not found")

        segment = conn.execute(
            """SELECT playlist_segments.*, playlist_songs.title AS song_title,
                      playlist_songs.uri AS song_uri, playlist_songs.id AS song_id
               FROM playlist_segments
               JOIN playlist_songs ON playlist_songs.id = playlist_segments.song_id
               WHERE playlist_segments.id = ? AND playlist_songs.session_setup_id = ?""",
            (body.segment_id, body.session_setup_id),
        ).fetchone()
        if not segment:
            raise HTTPException(
                status_code=404, detail="Segment not found in this session setup's playlist"
            )
        if segment["start_seconds"] is None or segment["end_seconds"] is None:
            raise HTTPException(
                status_code=400, detail="Segment must have both start and end marked before use"
            )

        if body.dac_path_1_id == body.dac_path_2_id:
            raise HTTPException(status_code=400, detail="dac_path_1_id and dac_path_2_id must differ")

        dac_path_1 = conn.execute(
            "SELECT * FROM dac_paths WHERE id = ?", (body.dac_path_1_id,)
        ).fetchone()
        dac_path_2 = conn.execute(
            "SELECT * FROM dac_paths WHERE id = ?", (body.dac_path_2_id,)
        ).fetchone()
        if not dac_path_1 or not dac_path_2:
            raise HTTPException(status_code=404, detail="One or both DAC paths not found")

        seed = random.Random().randrange(2**31)  # fresh, auto-seeded -- separate from the deterministic generator
        trials = randomization.generate_trial_sequence(
            setup["num_trials"], seed, setup["test_type"], body.dac_path_1_id, body.dac_path_2_id
        )

        dac_name_by_id = {body.dac_path_1_id: dac_path_1["name"], body.dac_path_2_id: dac_path_2["name"]}

        now = utcnow_iso()
        cur = conn.execute(
            """INSERT INTO session_runs
               (profile_id, session_setup_id, session_setup_name,
                song_id, song_title, song_uri,
                segment_id, segment_start_seconds, segment_end_seconds, segment_description,
                dac_path_1_id, dac_path_1_name, dac_path_2_id, dac_path_2_name,
                test_type, loop_mode, position_mode, num_trials, seed,
                started_at, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'in_progress')""",
            (
                setup["profile_id"], setup["id"], setup["name"],
                segment["song_id"], segment["song_title"], segment["song_uri"],
                segment["id"], segment["start_seconds"], segment["end_seconds"], segment["description"],
                body.dac_path_1_id, dac_path_1["name"], body.dac_path_2_id, dac_path_2["name"],
                setup["test_type"], setup["loop_mode"], setup["position_mode"], setup["num_trials"], seed,
                now,
            ),
        )
        run_id = cur.lastrowid

        for trial in trials:
            conn.execute(
                """INSERT INTO session_run_trials
                   (session_run_id, trial_index, dac_a_path_id, dac_a_path_name,
                    dac_b_path_id, dac_b_path_name, x_identity, trial_started_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    run_id, trial["trial_index"],
                    trial["dac_a_path_id"], dac_name_by_id[trial["dac_a_path_id"]],
                    trial["dac_b_path_id"], dac_name_by_id[trial["dac_b_path_id"]],
                    trial["x_identity"],
                    now if trial["trial_index"] == 0 else None,
                ),
            )
        conn.commit()

        return {
            "id": run_id,
            "session_setup_id": setup["id"],
            "session_setup_name": setup["name"],
            "song_title": segment["song_title"],
            "test_type": setup["test_type"],
            "loop_mode": setup["loop_mode"],
            "position_mode": setup["position_mode"],
            "num_trials": setup["num_trials"],
            "started_at": now,
            "status": "in_progress",
        }
    finally:
        conn.close()


@router.post("/{run_id}/abandon")
async def abandon_session(run_id: int):
    conn = get_connection()
    try:
        run = conn.execute("SELECT * FROM session_runs WHERE id = ?", (run_id,)).fetchone()
        if not run:
            raise HTTPException(status_code=404, detail="Session run not found")
        if run["status"] != "in_progress":
            raise HTTPException(status_code=409, detail=f"Session run is already {run['status']}")

        conn.execute(
            "UPDATE session_runs SET status = 'abandoned', completed_at = ? WHERE id = ?",
            (utcnow_iso(), run_id),
        )
        conn.commit()
        return {"id": run_id, "status": "abandoned"}
    finally:
        conn.close()


@router.get("/{run_id}/results", response_model=SessionResultsOut)
async def get_session_results(run_id: int):
    conn = get_connection()
    try:
        run = conn.execute("SELECT * FROM session_runs WHERE id = ?", (run_id,)).fetchone()
        if not run:
            raise HTTPException(status_code=404, detail="Session run not found")
        if run["status"] == "in_progress":
            raise HTTPException(
                status_code=409, detail="Results are only available once a session has completed or been abandoned"
            )

        trial_rows = conn.execute(
            "SELECT * FROM session_run_trials WHERE session_run_id = ? ORDER BY trial_index",
            (run_id,),
        ).fetchall()
        trials = [dict(r) for r in trial_rows]

        correct_count = None
        preference_tally = None
        if run["test_type"] == "difference":
            correct_count = sum(t["correct"] for t in trials if t["correct"] is not None)
        else:
            preference_tally = {run["dac_path_1_name"]: 0, run["dac_path_2_name"]: 0, "no_preference": 0}
            for t in trials:
                if t["vote"] == "A":
                    preference_tally[t["dac_a_path_name"]] += 1
                elif t["vote"] == "B":
                    preference_tally[t["dac_b_path_name"]] += 1
                elif t["vote"] == "no_preference":
                    preference_tally["no_preference"] += 1

        result = dict(run)
        result["trials"] = trials
        result["correct_count"] = correct_count
        result["preference_tally"] = preference_tally
        return result
    finally:
        conn.close()
