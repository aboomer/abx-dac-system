import asyncio
import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from api.clicker import watch_clicker
from api.db import init_db
from api.volumio_backend import VolumioBackend
from api import routes_profiles

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

SESSION_CONFIG_PATH = Path("/data/session_config.json")
TRACKS_PATH = Path("/data/tracks.json")

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


def load_backend_config() -> dict:
    if SESSION_CONFIG_PATH.exists():
        return json.loads(SESSION_CONFIG_PATH.read_text())
    return {"active_backend": "volumio", "volumio_host": "volumio.local", "volumio_port": 3000}


def load_tracks() -> list:
    if TRACKS_PATH.exists():
        return json.loads(TRACKS_PATH.read_text())
    return []


def save_tracks(tracks: list):
    TRACKS_PATH.write_text(json.dumps(tracks, indent=2))


@asynccontextmanager
async def lifespan(app: FastAPI):
    global backend

    init_db()

    clicker_task = asyncio.create_task(watch_clicker(next_trial, replay_trial, reveal, hide))

    config = load_backend_config()
    if config["active_backend"] == "volumio":
        backend = VolumioBackend(config["volumio_host"], config["volumio_port"])
        await backend.connect()
    else:
        raise NotImplementedError(f"Unknown active_backend: {config['active_backend']}")

    yield

    clicker_task.cancel()
    if backend:
        await backend.disconnect()


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static", html=True), name="static")
app.include_router(routes_profiles.router, prefix="/api/profiles")


@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/api/tracks")
async def get_tracks():
    return load_tracks()


@app.post("/api/tracks/add-current")
async def add_current_track():
    now_playing = await backend.get_now_playing()
    if not now_playing.get("uri"):
        return {"error": "Nothing currently playing on the backend"}

    track = {
        "id": now_playing["uri"],
        "title": now_playing.get("title", "Unknown title"),
        "artist": now_playing.get("artist", "Unknown artist"),
        "duration_seconds": now_playing.get("duration"),
        "seek_seconds": round(now_playing.get("seek", 0) / 1000),
        "album_art_url": now_playing.get("albumart"),
    }

    tracks = load_tracks()
    tracks = [t for t in tracks if t["id"] != track["id"]]  # replace if already added
    tracks.append(track)
    save_tracks(tracks)

    logger.info("added current track: %s - %s", track["artist"], track["title"])
    await broadcast_state({"event": "tracks_updated", "tracks": tracks})
    return track


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_clients.discard(websocket)
