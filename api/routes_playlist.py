from fastapi import APIRouter, HTTPException, Request

from api.db import get_connection, utcnow_iso
from api.models import SongOut, SegmentOut, SegmentPatch

router = APIRouter()


@router.post("/session-setups/{setup_id}/songs", response_model=SongOut)
async def add_song(setup_id: int, request: Request):
    backend = request.app.state.backend
    now_playing = await backend.get_now_playing()
    if not now_playing.get("uri"):
        raise HTTPException(status_code=409, detail="Nothing currently playing on the backend")

    conn = get_connection()
    try:
        setup = conn.execute(
            "SELECT id FROM session_setups WHERE id = ?", (setup_id,)
        ).fetchone()
        if not setup:
            raise HTTPException(status_code=404, detail="Session setup not found")

        position = conn.execute(
            "SELECT COUNT(*) FROM playlist_songs WHERE session_setup_id = ?", (setup_id,)
        ).fetchone()[0]

        cur = conn.execute(
            """INSERT INTO playlist_songs
               (session_setup_id, position, title, artist, album, service, uri,
                duration_seconds, album_art_url, added_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                setup_id,
                position,
                now_playing.get("title", "Unknown title"),
                now_playing.get("artist"),
                now_playing.get("album"),
                now_playing.get("service"),
                now_playing.get("uri"),
                now_playing.get("duration"),
                now_playing.get("albumart"),
                utcnow_iso(),
            ),
        )
        conn.commit()

        row = conn.execute(
            "SELECT * FROM playlist_songs WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        song = dict(row)
        song["segments"] = []
        return song
    finally:
        conn.close()


@router.delete("/songs/{song_id}")
async def delete_song(song_id: int):
    conn = get_connection()
    try:
        cur = conn.execute("DELETE FROM playlist_songs WHERE id = ?", (song_id,))
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Song not found")
        return {"deleted": song_id}
    finally:
        conn.close()


@router.post("/songs/{song_id}/segments/mark-start", response_model=SegmentOut)
async def mark_segment_start(song_id: int, request: Request):
    backend = request.app.state.backend

    conn = get_connection()
    try:
        song = conn.execute("SELECT * FROM playlist_songs WHERE id = ?", (song_id,)).fetchone()
        if not song:
            raise HTTPException(status_code=404, detail="Song not found")

        now_playing = await backend.get_now_playing()
        if song["uri"] and now_playing.get("uri") != song["uri"]:
            raise HTTPException(
                status_code=409,
                detail=(
                    f'Currently playing "{now_playing.get("title", "unknown")}", '
                    f'but marking a segment for "{song["title"]}". '
                    "Play the right track before marking."
                ),
            )

        start_seconds = round(now_playing.get("seek", 0) / 1000, 1)
        position = conn.execute(
            "SELECT COUNT(*) FROM playlist_segments WHERE song_id = ?", (song_id,)
        ).fetchone()[0]

        cur = conn.execute(
            """INSERT INTO playlist_segments (song_id, position, start_seconds, created_at)
               VALUES (?, ?, ?, ?)""",
            (song_id, position, start_seconds, utcnow_iso()),
        )
        conn.commit()

        row = conn.execute(
            "SELECT * FROM playlist_segments WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return dict(row)
    finally:
        conn.close()


@router.patch("/segments/{segment_id}/mark-end", response_model=SegmentOut)
async def mark_segment_end(segment_id: int, request: Request):
    backend = request.app.state.backend

    conn = get_connection()
    try:
        segment = conn.execute(
            "SELECT * FROM playlist_segments WHERE id = ?", (segment_id,)
        ).fetchone()
        if not segment:
            raise HTTPException(status_code=404, detail="Segment not found")

        song = conn.execute(
            "SELECT * FROM playlist_songs WHERE id = ?", (segment["song_id"],)
        ).fetchone()

        now_playing = await backend.get_now_playing()
        if song["uri"] and now_playing.get("uri") != song["uri"]:
            raise HTTPException(
                status_code=409,
                detail=(
                    f'Currently playing "{now_playing.get("title", "unknown")}", '
                    f'but marking a segment for "{song["title"]}". '
                    "Play the right track before marking."
                ),
            )

        end_seconds = round(now_playing.get("seek", 0) / 1000, 1)
        conn.execute(
            "UPDATE playlist_segments SET end_seconds = ? WHERE id = ?",
            (end_seconds, segment_id),
        )
        conn.commit()

        row = conn.execute(
            "SELECT * FROM playlist_segments WHERE id = ?", (segment_id,)
        ).fetchone()
        return dict(row)
    finally:
        conn.close()


@router.patch("/segments/{segment_id}", response_model=SegmentOut)
async def patch_segment(segment_id: int, patch: SegmentPatch):
    conn = get_connection()
    try:
        segment = conn.execute(
            "SELECT * FROM playlist_segments WHERE id = ?", (segment_id,)
        ).fetchone()
        if not segment:
            raise HTTPException(status_code=404, detail="Segment not found")

        description = segment["description"]
        start_seconds = segment["start_seconds"]
        end_seconds = segment["end_seconds"]

        if patch.description is not None:
            description = patch.description
        if patch.start_delta is not None and start_seconds is not None:
            start_seconds = max(0, start_seconds + patch.start_delta)
        if patch.end_delta is not None and end_seconds is not None:
            end_seconds = max(0, end_seconds + patch.end_delta)

        conn.execute(
            "UPDATE playlist_segments SET description = ?, start_seconds = ?, end_seconds = ? WHERE id = ?",
            (description, start_seconds, end_seconds, segment_id),
        )
        conn.commit()

        row = conn.execute(
            "SELECT * FROM playlist_segments WHERE id = ?", (segment_id,)
        ).fetchone()
        return dict(row)
    finally:
        conn.close()


@router.delete("/segments/{segment_id}")
async def delete_segment(segment_id: int):
    conn = get_connection()
    try:
        cur = conn.execute("DELETE FROM playlist_segments WHERE id = ?", (segment_id,))
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Segment not found")
        return {"deleted": segment_id}
    finally:
        conn.close()
