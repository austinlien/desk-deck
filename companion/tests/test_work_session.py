from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app import status_engine
from app.main import app
from app.models import CalendarState, DisplayStatus, SpotifyState, SpotifyTrack


class FakeWeatherSource:
    def select_status(self, now: datetime | None = None) -> DisplayStatus:
        return DisplayStatus(line1="CHIP 68F", line2="OUT 74F 45%", backlight="green")


class FakeCalendarSource:
    def __init__(self, status: DisplayStatus | None) -> None:
        self.status = status

    def select_status(self, now: datetime | None = None) -> CalendarState:
        return CalendarState(enabled=True, available=True, status=self.status)


class FakeSpotifySource:
    def __init__(self, title: str) -> None:
        self.title = title

    def select_status(self) -> SpotifyState:
        status = DisplayStatus(line1=self.title, line2="Artist", backlight="green")
        return SpotifyState(
            enabled=True,
            configured=True,
            available=True,
            track=SpotifyTrack(title=self.title, artist="Artist", is_playing=True),
            status=status,
        )


def setup_function() -> None:
    status_engine.reset_state()
    status_engine.set_calendar_source(None)
    status_engine.set_spotify_source(None)
    status_engine.set_weather_source(FakeWeatherSource())


def test_work_session_starts_at_zero_formats_elapsed_time_and_restarts() -> None:
    now = datetime(2026, 7, 17, 9, 0, tzinfo=timezone.utc)

    assert status_engine.start_work_session(now).elapsed_seconds == 0
    assert status_engine.select_status(now) == DisplayStatus(
        line1="WORKING", line2="00:00:00", backlight="yellow"
    )
    assert status_engine.select_status(now + timedelta(seconds=3661)) == DisplayStatus(
        line1="WORKING", line2="01:01:01", backlight="yellow"
    )

    assert status_engine.start_work_session(now + timedelta(seconds=3700)).elapsed_seconds == 0
    assert status_engine.select_status(now + timedelta(seconds=3700)) == DisplayStatus(
        line1="WORKING", line2="00:00:00", backlight="yellow"
    )


def test_agent_and_calendar_override_running_work_session() -> None:
    now = datetime(2026, 7, 17, 9, 0, tzinfo=timezone.utc)
    status_engine.start_work_session(now)
    status_engine.set_agent_status_value("working", now=now)

    assert status_engine.select_status(now) == status_engine.AGENT_STATUSES["working"]

    status_engine.set_calendar_source(
        FakeCalendarSource(DisplayStatus(line1="MEETING", line2="NOW", backlight="red"))
    )
    assert status_engine.select_status(now) == DisplayStatus(
        line1="MEETING", line2="NOW", backlight="red"
    )


def test_work_session_song_skip_interrupts_then_resumes_elapsed_time() -> None:
    now = datetime(2026, 7, 17, 9, 0, tzinfo=timezone.utc)
    spotify = FakeSpotifySource("Song A")
    status_engine.set_spotify_source(spotify)
    status_engine.start_work_session(now)

    assert status_engine.select_status(now).line1 == "WORKING"
    spotify.title = "Song B"
    assert status_engine.select_status(now + timedelta(seconds=1)) == DisplayStatus(
        line1="Song B", line2="Artist", backlight="yellow"
    )
    assert status_engine.select_status(now + timedelta(seconds=6)) == DisplayStatus(
        line1="WORKING", line2="00:00:06", backlight="yellow"
    )


def test_work_stop_completion_overrides_agent_for_five_seconds_then_agent_resumes() -> None:
    now = datetime(2026, 7, 17, 9, 0, tzinfo=timezone.utc)
    status_engine.start_work_session(now)
    stopped_at = now + timedelta(seconds=3723)
    status_engine.set_agent_status_value("working", now=stopped_at)

    state = status_engine.stop_work_session(stopped_at)
    assert state == status_engine.WorkState(
        running=False,
        elapsed_seconds=0,
        completion_elapsed_seconds=3723,
    )
    assert status_engine.select_status(stopped_at) == DisplayStatus(
        line1="SESSION DONE", line2="01:02:03", backlight="green"
    )
    assert status_engine.select_status(stopped_at + timedelta(seconds=5)) == status_engine.AGENT_STATUSES[
        "working"
    ]


def test_manual_mode_and_calendar_override_work_completion() -> None:
    now = datetime(2026, 7, 17, 9, 0, tzinfo=timezone.utc)
    status_engine.start_work_session(now)
    status_engine.stop_work_session(now + timedelta(seconds=60))
    status_engine.set_active_mode("idle")

    assert status_engine.select_status(now + timedelta(seconds=60)) == status_engine.STATUS_MODES["idle"]

    status_engine.set_calendar_source(
        FakeCalendarSource(DisplayStatus(line1="MEETING", line2="NOW", backlight="red"))
    )
    assert status_engine.select_status(now + timedelta(seconds=60)) == DisplayStatus(
        line1="IDLE", line2="READY", backlight="green"
    )

    status_engine.set_active_mode(None)
    assert status_engine.select_status(now + timedelta(seconds=60)) == DisplayStatus(
        line1="MEETING", line2="NOW", backlight="red"
    )


def test_work_endpoints_and_inactive_stop_are_safe() -> None:
    client = TestClient(app)

    assert client.post("/api/work/stop").json() == {
        "running": False,
        "elapsed_seconds": 0,
        "completion_elapsed_seconds": None,
    }
    assert client.post("/api/work/start").json()["running"] is True
    assert client.get("/api/work/status").json()["running"] is True
    assert client.post("/api/work/stop").json()["completion_elapsed_seconds"] is not None
