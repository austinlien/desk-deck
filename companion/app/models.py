from pydantic import BaseModel


class DisplayStatus(BaseModel):
    line1: str
    line2: str
    backlight: str
    effect: str = "solid"


class StatusInputs(BaseModel):
    meeting_soon: bool = False
    active_meeting: bool = False
    notification: bool = False
    spotify_playing: bool = False
    spotify_paused: bool = False
    spotify_title: str | None = None
    spotify_artist: str | None = None
    demo_default_rotation: bool = False


class DebugState(BaseModel):
    manual_override: str | None
    agent_override: str | None
    inputs: StatusInputs


class CalendarState(BaseModel):
    enabled: bool
    available: bool
    status: DisplayStatus | None = None
    detail: str | None = None


class InsideSensorReading(BaseModel):
    temperature_f: float


class WeatherState(BaseModel):
    enabled: bool
    available: bool
    location: str
    inside_temperature_f: float | None = None
    outside_temperature_f: float | None = None
    outside_humidity_percent: int | None = None
    status: DisplayStatus
    detail: str | None = None


class SpotifyTrack(BaseModel):
    title: str
    artist: str
    is_playing: bool


class SpotifyState(BaseModel):
    enabled: bool
    configured: bool
    available: bool
    source: str | None = None
    track: SpotifyTrack | None = None
    status: DisplayStatus | None = None
    detail: str | None = None
