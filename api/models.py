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


class SessionStartIn(BaseModel):
    session_setup_id: int
    segment_id: int
    dac_path_1_id: int
    dac_path_2_id: int


class SessionRunStartedOut(BaseModel):
    """Returned by POST /sessions/start and safe to send mid-session --
    deliberately excludes anything that would leak which physical DAC is
    under test (no dac_path_1/2 names, no seed, no per-trial data)."""
    id: int
    session_setup_id: int
    session_setup_name: str
    song_title: str
    test_type: str
    loop_mode: str
    position_mode: str
    num_trials: int
    started_at: str
    status: str
    current_trial_index: int = 0
    current_path: str = "A"


class TrialResultOut(BaseModel):
    trial_index: int
    x_identity: str | None
    vote: str | None
    correct: int | None
    dac_a_path_name: str
    dac_b_path_name: str
    navigation_count: int
    trial_started_at: str | None
    responded_at: str | None


class SessionResultsOut(BaseModel):
    """Only safe to send once a run is completed/abandoned -- this is the
    first point where revealing dac_path_1/2 identity is fine."""
    id: int
    session_setup_name: str
    song_title: str
    segment_description: str | None
    dac_path_1_name: str
    dac_path_2_name: str
    test_type: str
    num_trials: int
    started_at: str
    completed_at: str | None
    status: str
    trials: list[TrialResultOut]
    correct_count: int | None = None       # difference tests only
    preference_tally: dict | None = None   # preference tests only
