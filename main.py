import asyncio
import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from api.clicker import watch_clicker
from api.clicker_modes import manager as clicker_mode_manager, ClickerHandlers
from api.db import init_db
from api.models import ModeIn
from api.volumio_backend import VolumioBackend
from api import (
    routes_profiles,
    routes_dac_paths,
    routes_session_setups,
    routes_playlist,
    routes_free_play,
    routes_calibration,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

SESSION_CONFIG_PATH = Path("/data/session_config.json")

connected_clients: set[WebSocket] = set()
backend: VolumioBackend | None = None


async def broadcast_state(message: dict):
    dead = set()
    for client in connected_clients:
        try:
            await client.send_json(message)
        except Exception:
            dead.add(client)
    connected_clients.difference_update(dead)


async def next_trial():
    # Stub — real trial-advance logic arrives in Phase 5
    logger.info("clicker: next_trial")
    await broadcast_state({"event": "clicker", "action": "next_trial"})


async def replay_trial():
    # Stub — real replay logic arrives in Phase 5
    logger.info("clicker: replay_trial")
    await broadcast_state({"event": "clicker", "action": "replay_trial"})


async def reveal():
    # Stub — pointer button held down; real use TBD
    logger.info("clicker: reveal")
    await broadcast_state({"event": "clicker", "action": "reveal"})


async def hide():
    # Stub — pointer button released; real use TBD
    logger.info("clicker: hide")
    await broadcast_state({"event": "clicker", "action": "hide"})


async def noop():
    pass


def load_backend_config() -> dict:
    if SESSION_CONFIG_PATH.exists():
        return json.loads(SESSION_CONFIG_PATH.read_text())
    return {"active_backend": "volumio", "volumio_host": "volumio.local", "volumio_port": 3000}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global backend

    init_db()

    clicker_mode_manager.register(
        "setup", ClickerHandlers(on_next=noop, on_replay=noop, on_reveal=noop, on_hide=noop)
    )
    clicker_mode_manager.register(
        "active_session",
        ClickerHandlers(on_next=next_trial, on_replay=replay_trial, on_reveal=reveal, on_hide=hide),
    )
    routes_free_play.register_clicker_mode(broadcast_state)
    routes_calibration.register_clicker_mode()
    clicker_mode_manager.set_active("setup")

    clicker_task = asyncio.create_task(watch_clicker(
        clicker_mode_manager.dispatch_next,
        clicker_mode_manager.dispatch_replay,
        clicker_mode_manager.dispatch_reveal,
        clicker_mode_manager.dispatch_hide,
    ))

    config = load_backend_config()
    if config["active_backend"] == "volumio":
        backend = VolumioBackend(config["volumio_host"], config["volumio_port"])
        await backend.connect()
    else:
        raise NotImplementedError(f"Unknown active_backend: {config['active_backend']}")
    app.state.backend = backend

    yield

    clicker_task.cancel()
    if backend:
        await backend.disconnect()


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static", html=True), name="static")
app.include_router(routes_profiles.router, prefix="/api/profiles")
app.include_router(routes_dac_paths.router, prefix="/api/dac-paths")
app.include_router(routes_session_setups.router, prefix="/api")
app.include_router(routes_playlist.router, prefix="/api")
app.include_router(routes_free_play.router, prefix="/api/free-play")
app.include_router(routes_calibration.router, prefix="/api/calibration")


@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")


@app.post("/api/mode")
async def set_mode(body: ModeIn):
    try:
        clicker_mode_manager.set_active(body.mode)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"mode": body.mode}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_clients.discard(websocket)
