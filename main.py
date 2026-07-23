import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from api.clicker import watch_clicker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

connected_clients: set[WebSocket] = set()


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


@asynccontextmanager
async def lifespan(app: FastAPI):
    clicker_task = asyncio.create_task(watch_clicker(next_trial, replay_trial, reveal, hide))
    yield
    clicker_task.cancel()


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static", html=True), name="static")


@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_clients.discard(websocket)
