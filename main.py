from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory="static", html=True), name="static")


@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")

connected_clients: set[WebSocket] = set()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_clients.discard(websocket)


async def broadcast_state(message: dict):
    dead = set()
    for client in connected_clients:
        try:
            await client.send_json(message)
        except Exception:
            dead.add(client)
    connected_clients.difference_update(dead)
