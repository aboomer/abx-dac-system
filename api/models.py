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


class SessionSetupPatch(BaseModel):
    name: str | None = None
    gap_mode: str | None = None
    gap_seconds: float | None = None
    vibrate_after_trial: bool | None = None
    identity_mode: str | None = None
    num_trials: int | None = None
    play_whole_track: bool | None = None
    randomise_sequence: bool | None = None


class SessionSetupOut(BaseModel):
    id: int
    profile_id: int
    name: str
    gap_mode: str
    gap_seconds: float
    vibrate_after_trial: bool
    identity_mode: str
    num_trials: int
    play_whole_track: bool
    randomise_sequence: bool
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
