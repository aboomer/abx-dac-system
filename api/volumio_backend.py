import logging

import aiohttp
import socketio

from api.playback_backend import PlaybackBackend

logger = logging.getLogger("volumio")


class VolumioBackend(PlaybackBackend):
    def __init__(self, host: str, port: int = 3000):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.sio = socketio.AsyncClient(reconnection=True, reconnection_delay=2)
        self._latest_state: dict = {}
        self._session: aiohttp.ClientSession | None = None

        self.sio.on("pushState", self._on_push_state)
        self.sio.on("connect", self._on_connect)
        self.sio.on("disconnect", self._on_disconnect)

    async def _on_connect(self):
        logger.info("connected to Volumio at %s", self.base_url)
        await self.sio.emit("getState")

    async def _on_disconnect(self):
        logger.warning("disconnected from Volumio at %s", self.base_url)

    async def _on_push_state(self, data):
        self._latest_state = data

    async def connect(self):
        self._session = aiohttp.ClientSession()
        await self.sio.connect(self.base_url, transports=["websocket"])

    async def disconnect(self):
        await self.sio.disconnect()
        if self._session:
            await self._session.close()

    async def _command(self, cmd: str, **params):
        async with self._session.get(
            f"{self.base_url}/api/v1/commands/",
            params={"cmd": cmd, **params},
        ) as resp:
            return await resp.json(content_type=None)

    async def play(self):
        await self._command("play")

    async def stop(self):
        await self._command("stop")

    async def seek(self, seconds: float):
        await self._command("seek", position=int(seconds))

    async def get_now_playing(self) -> dict:
        return self._latest_state

    async def queue_track(self, track_uri: str):
        payload = {
            "item": {"uri": track_uri},
            "list": [{"uri": track_uri}],
            "index": 0,
        }
        async with self._session.post(
            f"{self.base_url}/api/v1/replaceAndPlay", json=payload
        ) as resp:
            return await resp.json(content_type=None)
