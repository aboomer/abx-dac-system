import sqlite3

from fastapi import APIRouter, HTTPException

from api.db import get_connection, utcnow_iso
from api.models import (
    SessionSetupIn,
    SessionSetupOut,
    SessionSetupPatch,
    SessionSetupDetailOut,
    SongOut,
    SegmentOut,
)

router = APIRouter()


@router.get("/profiles/{profile_id}/session-setups", response_model=list[SessionSetupOut])
async def list_session_setups(profile_id: int):
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM session_setups WHERE profile_id = ? ORDER BY updated_at DESC",
            (profile_id,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


@router.post("/profiles/{profile_id}/session-setups", response_model=SessionSetupOut)
async def create_session_setup(profile_id: int, setup: SessionSetupIn):
    conn = get_connection()
    try:
        profile = conn.execute("SELECT id FROM profiles WHERE id = ?", (profile_id,)).fetchone()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        now = utcnow_iso()
        try:
            cur = conn.execute(
                """INSERT INTO session_setups (profile_id, name, created_at, updated_at)
                   VALUES (?, ?, ?, ?)""",
                (profile_id, setup.name, now, now),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=409, detail="A session setup with this name already exists for this profile"
            )

        row = conn.execute(
            "SELECT * FROM session_setups WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return dict(row)
    finally:
        conn.close()


def _load_setup_detail(conn: sqlite3.Connection, setup_id: int) -> dict:
    setup_row = conn.execute("SELECT * FROM session_setups WHERE id = ?", (setup_id,)).fetchone()
    if not setup_row:
        return None

    setup = dict(setup_row)
    song_rows = conn.execute(
        "SELECT * FROM playlist_songs WHERE session_setup_id = ? ORDER BY position",
        (setup_id,),
    ).fetchall()

    songs = []
    for song_row in song_rows:
        song = dict(song_row)
        segment_rows = conn.execute(
            "SELECT * FROM playlist_segments WHERE song_id = ? ORDER BY position",
            (song["id"],),
        ).fetchall()
        song["segments"] = [dict(r) for r in segment_rows]
        songs.append(song)

    setup["songs"] = songs
    return setup


@router.get("/session-setups/{setup_id}", response_model=SessionSetupDetailOut)
async def get_session_setup(setup_id: int):
    conn = get_connection()
    try:
        detail = _load_setup_detail(conn, setup_id)
        if not detail:
            raise HTTPException(status_code=404, detail="Session setup not found")
        return detail
    finally:
        conn.close()


@router.patch("/session-setups/{setup_id}", response_model=SessionSetupOut)
async def patch_session_setup(setup_id: int, patch: SessionSetupPatch):
    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT * FROM session_setups WHERE id = ?", (setup_id,)
        ).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Session setup not found")

        updates = patch.model_dump(exclude_unset=True)
        if updates:
            fields = ", ".join(f"{k} = ?" for k in updates)
            values = [int(v) if isinstance(v, bool) else v for v in updates.values()]
            try:
                conn.execute(
                    f"UPDATE session_setups SET {fields}, updated_at = ? WHERE id = ?",
                    (*values, utcnow_iso(), setup_id),
                )
                conn.commit()
            except sqlite3.IntegrityError:
                raise HTTPException(
                    status_code=409, detail="A session setup with this name already exists for this profile"
                )

        row = conn.execute("SELECT * FROM session_setups WHERE id = ?", (setup_id,)).fetchone()
        return dict(row)
    finally:
        conn.close()


@router.delete("/session-setups/{setup_id}")
async def delete_session_setup(setup_id: int):
    conn = get_connection()
    try:
        cur = conn.execute("DELETE FROM session_setups WHERE id = ?", (setup_id,))
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Session setup not found")
        return {"deleted": setup_id}
    finally:
        conn.close()
