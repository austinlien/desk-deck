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
AGENT_ACTIVE_TTL_SECONDS = int(os.getenv("DESK_DECK_AGENT_ACTIVE_TTL_SECONDS", "300"))
SPOTIFY_HOLD_SECONDS = int(os.getenv("DESK_DECK_SPOTIFY_HOLD_SECONDS", "4"))
WEATHER_HOLD_SECONDS = int(os.getenv("DESK_DECK_WEATHER_HOLD_SECONDS", "5"))
TIME_HOLD_SECONDS = int(os.getenv("DESK_DECK_TIME_HOLD_SECONDS", "4"))
SPOTIFY_SCROLL_END_HOLD_SECONDS = int(os.getenv("DESK_DECK_SPOTIFY_SCROLL_END_HOLD_SECONDS", "1"))
SPOTIFY_SCROLL_DISPLAY_SYNC_SECONDS = int(os.getenv("DESK_DECK_SPOTIFY_SCROLL_DISPLAY_SYNC_SECONDS", "0"))
SPOTIFY_INTERRUPT_SECONDS = int(os.getenv("DESK_DECK_SPOTIFY_INTERRUPT_SECONDS", "5"))
LCD_COLUMNS = 16
SCROLL_INTERVAL_SECONDS = 0.4
SCROLL_PAUSE_FRAMES = 2
SCROLL_COMPLETION_BUFFER_FRAMES = 0

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
        backlight="green",
    ),
    "notify": DisplayStatus(
        line1="SERVER TEST",
        line2="NOTICE",
        backlight="purple",
    ),
    "spotify_paused": DisplayStatus(
        line1="PAUSED",
        line2="TEST TRACK",
        backlight="green",
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
agent_updated_at: datetime | None = None
agent_done_at: datetime | None = None
status_inputs = StatusInputs()
calendar_source: CalendarStatusSource | None = None
weather_source: WeatherStatusSource | None = None
spotify_source: SpotifyStatusSource | None = None
default_rotation_key: str | None = None
default_rotation_started_at: datetime | None = None
default_rotation_blocked = False
last_spotify_track_key: str | None = None
spotify_interrupt_track_key: str | None = None
spotify_interrupt_started_at: datetime | None = None
spotify_interrupt_status: DisplayStatus | None = None


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
    global agent_status, agent_updated_at, agent_done_at
    current = now or datetime.now().astimezone()
    agent_status = state
    agent_updated_at = current if state in {"working", "waiting"} else None
    agent_done_at = current if state == "done" else None
    if state in {"working", "waiting"}:
        reset_spotify_interrupt()
        reset_spotify_track_baseline()


def get_agent_status_value(now: datetime | None = None) -> str | None:
    current = now or datetime.now().astimezone()
    if agent_status in {"working", "waiting"} and is_active_agent_status_fresh(current):
        return agent_status
    if agent_status == "done" and agent_done_at is not None:
        if current - agent_done_at < timedelta(seconds=AGENT_DONE_HOLD_SECONDS):
            return "done"
    return None


def is_active_agent_status_fresh(now: datetime) -> bool:
    if agent_updated_at is None:
        return False
    return now - agent_updated_at < timedelta(seconds=AGENT_ACTIVE_TTL_SECONDS)


def set_active_mode(mode_name: str | None) -> None:
    global active_mode
    active_mode = mode_name


def set_status_inputs(inputs: StatusInputs) -> None:
    global status_inputs
    status_inputs = inputs


def reset_state() -> None:
    global active_mode, agent_status, agent_updated_at, agent_done_at, status_inputs
    active_mode = None
    agent_status = None
    agent_updated_at = None
    agent_done_at = None
    status_inputs = StatusInputs()
    reset_spotify_state()


def reset_spotify_state() -> None:
    reset_default_rotation()
    reset_spotify_interrupt()
    reset_spotify_track_baseline()


def reset_default_rotation() -> None:
    global default_rotation_key, default_rotation_started_at, default_rotation_blocked
    default_rotation_key = None
    default_rotation_started_at = None
    default_rotation_blocked = False


def mark_default_rotation_blocked() -> None:
    global default_rotation_blocked
    default_rotation_blocked = True


def reset_spotify_interrupt() -> None:
    global spotify_interrupt_track_key, spotify_interrupt_started_at, spotify_interrupt_status
    spotify_interrupt_track_key = None
    spotify_interrupt_started_at = None
    spotify_interrupt_status = None


def reset_spotify_track_baseline() -> None:
    global last_spotify_track_key
    last_spotify_track_key = None


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
    priority_status = select_priority_status(now)
    spotify = select_spotify_status()
    spotify_interrupt = select_spotify_interrupt(spotify, priority_status, now)
    if spotify_interrupt is not None:
        if priority_status is not None:
            mark_default_rotation_blocked()
        return spotify_interrupt

    if priority_status is not None:
        mark_default_rotation_blocked()
        return priority_status

    if has_debug_status():
        reset_default_rotation()
        return select_debug_status()

    return select_rotating_default_status(spotify, now)


def select_priority_status(now: datetime) -> DisplayStatus | None:
    if active_mode is not None:
        return STATUS_MODES[active_mode]

    calendar = select_calendar_status(now)
    if calendar.status is not None:
        return calendar.status

    if agent_status in {"working", "waiting"} and is_active_agent_status_fresh(now):
        return AGENT_STATUSES[agent_status]
    if agent_status == "done" and agent_done_at is not None:
        if now - agent_done_at < timedelta(seconds=AGENT_DONE_HOLD_SECONDS):
            return AGENT_STATUSES["done"]

    return None


def select_spotify_interrupt(
    spotify: SpotifyState,
    interrupted_status: DisplayStatus | None,
    now: datetime,
) -> DisplayStatus | None:
    global last_spotify_track_key, spotify_interrupt_track_key, spotify_interrupt_started_at, spotify_interrupt_status

    if spotify.status is None:
        reset_spotify_interrupt()
        reset_spotify_track_baseline()
        return None

    track_key = spotify_track_key(spotify)
    if (
        spotify_interrupt_track_key == track_key
        and spotify_interrupt_started_at is not None
        and spotify_interrupt_status is not None
    ):
        if now - spotify_interrupt_started_at < timedelta(seconds=SPOTIFY_INTERRUPT_SECONDS):
            return spotify_interrupt_status
        reset_spotify_interrupt()

    if track_key != last_spotify_track_key:
        previous_track_key = last_spotify_track_key
        last_spotify_track_key = track_key
        reset_spotify_interrupt()
        if previous_track_key is not None and interrupted_status is not None:
            spotify_interrupt_track_key = track_key
            spotify_interrupt_started_at = now
            spotify_interrupt_status = spotify_status_for_interrupt(
                spotify.status,
                interrupted_status.backlight,
            )
            return spotify_interrupt_status

    return None


def select_rotating_default_status(spotify: SpotifyState, now: datetime) -> DisplayStatus:
    global default_rotation_key, default_rotation_started_at, default_rotation_blocked

    rotation_key = spotify_track_key(spotify) if spotify.status is not None else "default"
    if (
        default_rotation_key != rotation_key
        or default_rotation_started_at is None
        or default_rotation_blocked
    ):
        default_rotation_key = rotation_key
        default_rotation_started_at = now
        default_rotation_blocked = False

    phases = default_status_phases(spotify, now)
    cycle_seconds = sum(duration.total_seconds() for _, duration in phases)
    if cycle_seconds <= 0:
        return select_weather_status(now)

    elapsed = now - default_rotation_started_at
    position = elapsed.total_seconds() % cycle_seconds
    for status, duration in phases:
        duration_seconds = duration.total_seconds()
        if position < duration_seconds:
            return status
        position -= duration_seconds
    return phases[-1][0]


def default_status_phases(spotify: SpotifyState, now: datetime) -> list[tuple[DisplayStatus, timedelta]]:
    phases: list[tuple[DisplayStatus, timedelta]] = []
    if spotify.status is not None:
        spotify_status = spotify_status_for_rotation(spotify.status)
        phases.append((spotify_status, spotify_phase_duration(spotify_status)))

    phases.append((select_weather_status(now), timedelta(seconds=WEATHER_HOLD_SECONDS)))
    phases.append((select_time_status(now), timedelta(seconds=TIME_HOLD_SECONDS)))
    return phases


def select_time_status(now: datetime | None = None) -> DisplayStatus:
    current = now or datetime.now().astimezone()
    time_text = current.strftime("%I:%M %p").lstrip("0")
    date_text = current.strftime("%a %b %d").upper()
    return DisplayStatus(line1=time_text, line2=date_text, backlight="green")


def spotify_track_key(spotify: SpotifyState) -> str:
    if spotify.track is not None:
        return f"{spotify.track.title}\n{spotify.track.artist}"
    if spotify.status is None:
        return ""
    return f"{spotify.status.line1}\n{spotify.status.line2}"


def spotify_status_for_rotation(status: DisplayStatus | None) -> DisplayStatus:
    if status is None:
        return STATUS_MODES["online"]

    effect = "scroll_once" if spotify_status_needs_scroll(status) else "solid"
    return DisplayStatus(
        line1=status.line1,
        line2=status.line2,
        backlight=status.backlight,
        effect=effect,
    )


def spotify_status_for_interrupt(status: DisplayStatus, inherited_backlight: str) -> DisplayStatus:
    effect = "scroll_once" if spotify_status_needs_scroll(status) else "solid"
    return DisplayStatus(
        line1=status.line1,
        line2=status.line2,
        backlight=inherited_backlight,
        effect=effect,
    )


def spotify_phase_duration(status: DisplayStatus) -> timedelta:
    overflow = max(len(status.line1), len(status.line2)) - LCD_COLUMNS
    if overflow <= 0:
        return timedelta(seconds=SPOTIFY_HOLD_SECONDS)

    scroll_frames = SCROLL_PAUSE_FRAMES + overflow + SCROLL_COMPLETION_BUFFER_FRAMES
    scroll_seconds = scroll_frames * SCROLL_INTERVAL_SECONDS
    return timedelta(
        seconds=scroll_seconds + SPOTIFY_SCROLL_END_HOLD_SECONDS + SPOTIFY_SCROLL_DISPLAY_SYNC_SECONDS
    )


def spotify_status_needs_scroll(status: DisplayStatus) -> bool:
    return len(status.line1) > LCD_COLUMNS or len(status.line2) > LCD_COLUMNS


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
