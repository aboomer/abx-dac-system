import sqlite3

from fastapi import APIRouter, HTTPException

from api.db import get_connection, utcnow_iso
from api.models import DacPathIn, DacPathOut, DacPathPatch

router = APIRouter()


@router.get("", response_model=list[DacPathOut])
async def list_dac_paths():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM dac_paths ORDER BY name").fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


@router.post("", response_model=DacPathOut)
async def create_dac_path(dac_path: DacPathIn):
    conn = get_connection()
    try:
        try:
            cur = conn.execute(
                "INSERT INTO dac_paths (name, notes, created_at) VALUES (?, ?, ?)",
                (dac_path.name, dac_path.notes, utcnow_iso()),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=409, detail="DAC path name already exists")
        row = conn.execute(
            "SELECT * FROM dac_paths WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return dict(row)
    finally:
        conn.close()


@router.patch("/{dac_path_id}", response_model=DacPathOut)
async def update_dac_path(dac_path_id: int, patch: DacPathPatch):
    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT * FROM dac_paths WHERE id = ?", (dac_path_id,)
        ).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="DAC path not found")

        name = patch.name if patch.name is not None else existing["name"]
        notes = patch.notes if patch.notes is not None else existing["notes"]
        try:
            conn.execute(
                "UPDATE dac_paths SET name = ?, notes = ? WHERE id = ?",
                (name, notes, dac_path_id),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=409, detail="DAC path name already exists")

        row = conn.execute(
            "SELECT * FROM dac_paths WHERE id = ?", (dac_path_id,)
        ).fetchone()
        return dict(row)
    finally:
        conn.close()


@router.delete("/{dac_path_id}")
async def delete_dac_path(dac_path_id: int):
    conn = get_connection()
    try:
        cur = conn.execute("DELETE FROM dac_paths WHERE id = ?", (dac_path_id,))
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="DAC path not found")
        return {"deleted": dac_path_id}
    finally:
        conn.close()
