import sqlite3

from fastapi import APIRouter, HTTPException

from api.db import get_connection, utcnow_iso
from api.models import ProfileIn, ProfileOut

router = APIRouter()


@router.get("", response_model=list[ProfileOut])
async def list_profiles():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM profiles ORDER BY name").fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


@router.post("", response_model=ProfileOut)
async def create_profile(profile: ProfileIn):
    conn = get_connection()
    try:
        try:
            cur = conn.execute(
                "INSERT INTO profiles (name, created_at) VALUES (?, ?)",
                (profile.name, utcnow_iso()),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=409, detail="Profile name already exists")
        row = conn.execute(
            "SELECT * FROM profiles WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return dict(row)
    finally:
        conn.close()


@router.delete("/{profile_id}")
async def delete_profile(profile_id: int):
    conn = get_connection()
    try:
        cur = conn.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Profile not found")
        return {"deleted": profile_id}
    finally:
        conn.close()
