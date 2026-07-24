import asyncio
import logging

from fastapi import APIRouter

from api.db import get_connection
from api.clicker_modes import manager, ClickerHandlers

router = APIRouter()
logger = logging.getLogger("free_play")

_state = {"current_index": 0}
_broadcast_fn = None  # injected by register_clicker_mode() at startup

# Placeholder for Phase 4/5's real IR-controlled DAC switching. Called after
# the "currently selected" pointer changes; no-op until that hardware exists.
dac_path_switch_hook = None


def _load_dac_paths_sync() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT id, name FROM dac_paths ORDER BY name").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


async def _load_dac_paths() -> list[dict]:
    # SQLite calls are blocking; run off the event loop so a slow disk access
    # never stalls the evdev clicker listener sharing this loop.
    return await asyncio.to_thread(_load_dac_paths_sync)


async def _broadcast_current_path(paths: list[dict]):
    if not paths:
        await _broadcast_fn({"event": "free_play_dac_path", "dac_path": None})
        return
    idx = _state["current_index"] % len(paths)
    await _broadcast_fn({"event": "free_play_dac_path", "dac_path": paths[idx]})
    if dac_path_switch_hook:
        await dac_path_switch_hook(paths[idx])


async def _on_next():
    logger.info("free_play: next")
    paths = await _load_dac_paths()
    if paths:
        _state["current_index"] = (_state["current_index"] + 1) % len(paths)
    await _broadcast_current_path(paths)


async def _on_replay():
    logger.info("free_play: replay (prev)")
    paths = await _load_dac_paths()
    if paths:
        _state["current_index"] = (_state["current_index"] - 1) % len(paths)
    await _broadcast_current_path(paths)


async def _noop():
    pass


def register_clicker_mode(broadcast_fn):
    global _broadcast_fn
    _broadcast_fn = broadcast_fn
    manager.register(
        "free_play",
        ClickerHandlers(on_next=_on_next, on_replay=_on_replay, on_reveal=_noop, on_hide=_noop),
    )


@router.post("/start")
async def start_free_play():
    _state["current_index"] = 0
    manager.set_active("free_play")
    paths = await _load_dac_paths()
    await _broadcast_current_path(paths)
    return {"mode": "free_play"}


@router.post("/stop")
async def stop_free_play():
    manager.set_active("setup")
    return {"mode": "setup"}
