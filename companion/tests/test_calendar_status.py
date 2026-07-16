from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app import status_engine
from app.calendar_source import GoogleCalendarSource
from app.main import app
from app.models import CalendarState, DisplayStatus


class FakeCalendarSource:
    def __init__(self, status: DisplayStatus | None) -> None:
        self.status = status

    def select_status(self, now: datetime | None = None) -> CalendarState:
        return CalendarState(enabled=True, available=True, status=self.status)


class FakeWeatherSource:
    def select_status(self, now: datetime | None = None) -> DisplayStatus:
        return DisplayStatus(line1="CHIP 68F", line2="OUT 74F 45%", backlight="green")


class FakeGoogleCalendarSource(GoogleCalendarSource):
    def __init__(self, events: list[dict]) -> None:
        super().__init__()
        self.events = events

    def _fetch_candidate_events(self, now: datetime) -> list[dict]:
        return self.events


def setup_function() -> None:
    status_engine.reset_state()
    status_engine.set_calendar_source(None)
    status_engine.set_spotify_source(None)
    status_engine.set_weather_source(None)


def test_default_status_when_calendar_is_not_configured() -> None:
    status_engine.set_weather_source(FakeWeatherSource())
    client = TestClient(app)

    response = client.get("/api/status")

    assert response.status_code == 200
    assert response.json() == {
        "line1": "CHIP 68F",
        "line2": "OUT 74F 45%",
        "backlight": "green",
        "effect": "solid",
    }


def test_calendar_yellow_when_meeting_is_within_ten_minutes() -> None:
    now = datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)
    status = status_engine.calendar_status_from_event_window(
        now,
        now + timedelta(minutes=9),
        now + timedelta(minutes=39),
    )

    assert status == status_engine.CALENDAR_MEETING_SOON_YELLOW


def test_calendar_red_when_meeting_is_within_five_minutes() -> None:
    now = datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)
    status = status_engine.calendar_status_from_event_window(
        now,
        now + timedelta(minutes=4),
        now + timedelta(minutes=34),
    )

    assert status == status_engine.CALENDAR_MEETING_SOON_RED


def test_calendar_now_when_meeting_has_started() -> None:
    now = datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)
    status = status_engine.calendar_status_from_event_window(
        now,
        now - timedelta(minutes=1),
        now + timedelta(minutes=29),
    )

    assert status == status_engine.CALENDAR_MEETING_STARTED


def test_calendar_status_wins_over_debug_inputs() -> None:
    status_engine.set_calendar_source(FakeCalendarSource(status_engine.CALENDAR_MEETING_SOON_YELLOW))
    status_engine.set_status_inputs(status_engine.StatusInputs(spotify_playing=True))
    client = TestClient(app)

    response = client.get("/api/status")

    assert response.status_code == 200
    assert response.json()["line1"] == "MEETING"
    assert response.json()["line2"] == "SOON"
    assert response.json()["backlight"] == "yellow"
    assert response.json()["effect"] == "solid"


def test_calendar_status_wins_over_agent_status() -> None:
    status_engine.set_calendar_source(FakeCalendarSource(status_engine.CALENDAR_MEETING_STARTED))
    status_engine.set_agent_status_value("working")
    client = TestClient(app)

    response = client.get("/api/status")

    assert response.status_code == 200
    assert response.json() == {
        "line1": "MEETING",
        "line2": "NOW",
        "backlight": "red",
        "effect": "solid",
    }


def test_agent_status_returns_when_calendar_status_clears() -> None:
    status_engine.set_calendar_source(FakeCalendarSource(None))
    status_engine.set_agent_status_value("working")
    client = TestClient(app)

    response = client.get("/api/status")

    assert response.status_code == 200
    assert response.json() == {
        "line1": "AGENT",
        "line2": "WORKING",
        "backlight": "yellow",
        "effect": "solid",
    }


def test_real_calendar_source_ignores_declined_all_day_and_free_events() -> None:
    now = datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)
    source = FakeGoogleCalendarSource(
        [
            {
                "status": "confirmed",
                "start": {"dateTime": (now + timedelta(minutes=4)).isoformat()},
                "end": {"dateTime": (now + timedelta(minutes=34)).isoformat()},
                "attendees": [{"self": True, "responseStatus": "declined"}],
            },
            {
                "status": "confirmed",
                "start": {"date": "2026-07-16"},
                "end": {"date": "2026-07-17"},
                "creator": {"self": True},
            },
            {
                "status": "confirmed",
                "transparency": "transparent",
                "start": {"dateTime": (now + timedelta(minutes=4)).isoformat()},
                "end": {"dateTime": (now + timedelta(minutes=34)).isoformat()},
                "creator": {"self": True},
            },
        ]
    )

    status = source.select_status(now)

    assert status.enabled is True
    assert status.available is True
    assert status.status is None


def test_real_calendar_source_counts_accepted_busy_event() -> None:
    now = datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)
    source = FakeGoogleCalendarSource(
        [
            {
                "status": "confirmed",
                "start": {"dateTime": (now + timedelta(minutes=4)).isoformat()},
                "end": {"dateTime": (now + timedelta(minutes=34)).isoformat()},
                "attendees": [{"self": True, "responseStatus": "accepted"}],
            },
        ]
    )

    status = source.select_status(now)

    assert status.status == status_engine.CALENDAR_MEETING_SOON_RED


def test_calendar_source_caches_events_but_recomputes_status_window() -> None:
    now = datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)

    class CountingCalendarSource(GoogleCalendarSource):
        def __init__(self) -> None:
            super().__init__(cache_seconds=30)
            self.fetch_count = 0

        def _fetch_candidate_events(self, current: datetime) -> list[dict]:
            self.fetch_count += 1
            return [
                {
                    "status": "confirmed",
                    "start": {"dateTime": (now + timedelta(minutes=5, seconds=10)).isoformat()},
                    "end": {"dateTime": (now + timedelta(minutes=35, seconds=10)).isoformat()},
                    "creator": {"self": True},
                }
            ]

    source = CountingCalendarSource()

    assert source.select_status(now).status == status_engine.CALENDAR_MEETING_SOON_YELLOW
    assert source.select_status(now + timedelta(seconds=20)).status == status_engine.CALENDAR_MEETING_SOON_RED
    assert source.fetch_count == 1


def test_calendar_source_caches_fetch_failures_briefly() -> None:
    now = datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)

    class FailingCalendarSource(GoogleCalendarSource):
        def __init__(self) -> None:
            super().__init__(cache_seconds=30)
            self.fetch_count = 0

        def _fetch_candidate_events(self, current: datetime) -> list[dict]:
            self.fetch_count += 1
            raise RuntimeError("calendar unavailable")

    source = FailingCalendarSource()

    first = source.select_status(now)
    second = source.select_status(now + timedelta(seconds=5))

    assert first.available is False
    assert second.available is False
    assert first.detail == "calendar unavailable"
    assert second.detail == "calendar unavailable"
    assert source.fetch_count == 1
