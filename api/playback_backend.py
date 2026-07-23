class PlaybackBackend:
    """Abstraction over the playback source (Volumio now, Roon later).

    UI and session logic should only ever talk to this interface, never to
    a specific backend directly - see the guide's "Playback Backend
    Abstraction" section. Swapping VolumioBackend for RoonBackend later
    (Phase 7) should require no changes here or in session/UI code.
    """

    async def play(self):
        raise NotImplementedError

    async def stop(self):
        raise NotImplementedError

    async def seek(self, seconds: float):
        raise NotImplementedError

    async def get_now_playing(self) -> dict:
        raise NotImplementedError

    async def queue_track(self, track_uri: str):
        raise NotImplementedError
