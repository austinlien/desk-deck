import os
from datetime import datetime, timedelta
from typing import Protocol

from .models import CalendarState, DisplayStatus, SpotifyState, StatusInputs, WeatherState


class CalendarStatusSource(Protocol):
    def select_status(self, now: datetime | None = None) -> CalendarState:
        ...


class WeatherStatusSource(Protocol):
    def select_status(self, now: datetime | None = None) -> DisplayStatus:
        ...

    def get_state(self, now: datetime | None = None) -> WeatherState:
        ...


class SpotifyStatusSource(Protocol):
    def select_status(self) -> SpotifyState:
        ...


AGENT_DONE_HOLD_SECONDS = int(os.getenv("DESK_DECK_AGENT_DONE_HOLD_SECONDS", "5"))

AGENT_STATUSES: dict[str, DisplayStatus] = {
    "working": DisplayStatus(
        line1="AGENT",
        line2="WORKING",
        backlight="yellow",
    ),
    "waiting": DisplayStatus(
        line1="AGENT",
        line2="WAITING",
        backlight="red",
    ),
    "done": DisplayStatus(
        line1="AGENT",
        line2="DONE",
        backlight="green",
    ),
}


STATUS_MODES: dict[str, DisplayStatus] = {
    "online": DisplayStatus(
        line1="DESK DECK",
        line2="ONLINE",
        backlight="green",
    ),
    "idle": DisplayStatus(
        line1="IDLE",
        line2="READY",
        backlight="green",
    ),
    "meeting_soon": DisplayStatus(
        line1="MEETING",
        line2="IN 5",
        backlight="yellow",
    ),
    "meeting": DisplayStatus(
        line1="IN A MEETING",
        line2="BUSY",
        backlight="red",
    ),
    "music": DisplayStatus(
        line1="NOW PLAYING",
        line2="TEST TRACK",
        backlight="blue",
    ),
    "notify": DisplayStatus(
        line1="SERVER TEST",
        line2="NOTICE",
        backlight="purple",
    ),
    "spotify_paused": DisplayStatus(
        line1="PAUSED",
        line2="TEST TRACK",
        backlight="blue",
    ),
}

CALENDAR_MEETING_SOON_YELLOW = DisplayStatus(
    line1="MEETING",
    line2="SOON",
    backlight="yellow",
)
CALENDAR_MEETING_SOON_RED = DisplayStatus(
    line1="MEETING",
    line2="SOON",
    backlight="red",
)
CALENDAR_MEETING_STARTED = DisplayStatus(
    line1="MEETING",
    line2="NOW",
    backlight="red",
)

active_mode: str | None = None
agent_status: str | None = None
agent_done_at: datetime | None = None
status_inputs = StatusInputs()
calendar_source: CalendarStatusSource | None = None
weather_source: WeatherStatusSource | None = None
spotify_source: SpotifyStatusSource | None = None


def set_calendar_source(source: CalendarStatusSource | None) -> None:
    global calendar_source
    calendar_source = source


def set_weather_source(source: WeatherStatusSource | None) -> None:
    global weather_source
    weather_source = source


def set_spotify_source(source: SpotifyStatusSource | None) -> None:
    global spotify_source
    spotify_source = source


def set_agent_status_value(state: str | None, now: datetime | None = None) -> None:
    global agent_status, agent_done_at
    agent_status = state
    agent_done_at = (now or datetime.now().astimezone()) if state == "done" else None


def set_active_mode(mode_name: str | None) -> None:
    global active_mode
    active_mode = mode_name


def set_status_inputs(inputs: StatusInputs) -> None:
    global status_inputs
    status_inputs = inputs


def reset_state() -> None:
    global active_mode, agent_status, agent_done_at, status_inputs
    active_mode = None
    agent_status = None
    agent_done_at = None
    status_inputs = StatusInputs()


def select_debug_status() -> DisplayStatus:
    if status_inputs.meeting_soon:
        return STATUS_MODES["meeting_soon"]
    if status_inputs.active_meeting:
        return STATUS_MODES["meeting"]
    if status_inputs.notification:
        return STATUS_MODES["notify"]
    if status_inputs.spotify_playing:
        return STATUS_MODES["music"]
    if status_inputs.spotify_paused:
        return STATUS_MODES["spotify_paused"]
    return STATUS_MODES["online"]


def has_debug_status() -> bool:
    return any(
        (
            status_inputs.meeting_soon,
            status_inputs.active_meeting,
            status_inputs.notification,
            status_inputs.spotify_playing,
            status_inputs.spotify_paused,
        )
    )


def select_calendar_status(now: datetime | None = None) -> CalendarState:
    if calendar_source is None:
        return CalendarState(enabled=False, available=False, detail="Calendar source is not configured.")
    return calendar_source.select_status(now)


def select_weather_status(now: datetime | None = None) -> DisplayStatus:
    if weather_source is None:
        return STATUS_MODES["online"]
    return weather_source.select_status(now)


def get_weather_state(now: datetime | None = None) -> WeatherState | None:
    if weather_source is None:
        return None
    return weather_source.get_state(now)


def select_spotify_status() -> SpotifyState:
    if spotify_source is None:
        return SpotifyState(
            enabled=False,
            configured=False,
            available=False,
            detail="Spotify source is not configured.",
        )
    return spotify_source.select_status()


def select_status(now: datetime | None = None) -> DisplayStatus:
    now = now or datetime.now().astimezone()
    if active_mode is not None:
        return STATUS_MODES[active_mode]

    calendar = select_calendar_status(now)
    if calendar.status is not None:
        return calendar.status

    if agent_status in {"working", "waiting"}:
        return AGENT_STATUSES[agent_status]
    if agent_status == "done" and agent_done_at is not None:
        if now - agent_done_at < timedelta(seconds=AGENT_DONE_HOLD_SECONDS):
            return AGENT_STATUSES["done"]

    spotify = select_spotify_status()
    if spotify.status is not None:
        return spotify.status

    if has_debug_status():
        return select_debug_status()

    return select_weather_status(now)


def calendar_status_from_event_window(
    now: datetime,
    event_start: datetime,
    event_end: datetime,
) -> DisplayStatus | None:
    if event_start <= now < event_end:
        return CALENDAR_MEETING_STARTED

    minutes_until_start = event_start - now
    if timedelta(minutes=5) >= minutes_until_start >= timedelta(0):
        return CALENDAR_MEETING_SOON_RED
    if timedelta(minutes=10) >= minutes_until_start > timedelta(minutes=5):
        return CALENDAR_MEETING_SOON_YELLOW
    return None
