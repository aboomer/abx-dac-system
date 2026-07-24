from pydantic import BaseModel


class ProfileIn(BaseModel):
    name: str


class ProfileOut(BaseModel):
    id: int
    name: str
    created_at: str


class DacPathIn(BaseModel):
    name: str
    notes: str | None = None


class DacPathPatch(BaseModel):
    name: str | None = None
    notes: str | None = None


class DacPathOut(BaseModel):
    id: int
    name: str
    notes: str | None
    created_at: str


class SessionSetupIn(BaseModel):
    name: str
    test_type: str  # 'difference' | 'preference'


class SessionSetupPatch(BaseModel):
    name: str | None = None
    test_type: str | None = None
    loop_mode: str | None = None
    position_mode: str | None = None
    vibrate_after_trial: bool | None = None
    num_trials: int | None = None


class SessionSetupOut(BaseModel):
    id: int
    profile_id: int
    name: str
    test_type: str
    loop_mode: str
    position_mode: str
    vibrate_after_trial: bool
    num_trials: int
    created_at: str
    updated_at: str


class SegmentOut(BaseModel):
    id: int
    song_id: int
    position: int
    start_seconds: float | None
    end_seconds: float | None
    description: str | None
    created_at: str


class SongOut(BaseModel):
    id: int
    session_setup_id: int
    position: int
    title: str
    artist: str | None
    album: str | None
    service: str | None
    uri: str | None
    duration_seconds: float | None
    album_art_url: str | None
    added_at: str
    segments: list[SegmentOut] = []


class SessionSetupDetailOut(SessionSetupOut):
    songs: list[SongOut] = []


class SegmentPatch(BaseModel):
    description: str | None = None
    start_delta: float | None = None
    end_delta: float | None = None


class ModeIn(BaseModel):
    mode: str
