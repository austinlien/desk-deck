from datetime import datetime, timezone

from app import status_engine
from app.models import DisplayStatus, SpotifyState, SpotifyTrack
from app.spotify_source import SpotifySource


class FakeSpotifySource:
    def __init__(self, status: DisplayStatus | None) -> None:
        self.status = status

    def select_status(self) -> SpotifyState:
        return SpotifyState(
            enabled=True,
            configured=True,
            available=True,
            track=SpotifyTrack(title="Test Track", artist="Test Artist", is_playing=True)
            if self.status is not None
            else None,
            status=self.status,
        )


class FakeWeatherSource:
    def select_status(self, now: datetime | None = None) -> DisplayStatus:
        return DisplayStatus(line1="CHIP 68F", line2="OUT 74F 45%", backlight="green")


class FakeCalendarSource:
    def select_status(self, now: datetime | None = None):
        from app.models import CalendarState

        return CalendarState(
            enabled=True,
            available=True,
            status=DisplayStatus(line1="MEETING", line2="NOW", backlight="red"),
        )


class FakeHttpSpotifySource(SpotifySource):
    def __init__(self, payload: dict | None) -> None:
        super().__init__(client_id="client", client_secret="secret")
        self.payload = payload

    def _access_token(self) -> str:
        return "token"

    def _fetch_payload(self, token: str):
        return self.payload


def setup_function() -> None:
    status_engine.reset_state()
    status_engine.set_calendar_source(None)
    status_engine.set_spotify_source(None)
    status_engine.set_weather_source(FakeWeatherSource())


def test_spotify_playing_overrides_weather() -> None:
    status_engine.set_spotify_source(
        FakeSpotifySource(DisplayStatus(line1="Song", line2="Artist", backlight="blue"))
    )

    status = status_engine.select_status(datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc))

    assert status == DisplayStatus(line1="Song", line2="Artist", backlight="blue")


def test_spotify_paused_or_absent_falls_back_to_weather() -> None:
    status_engine.set_spotify_source(FakeSpotifySource(None))

    status = status_engine.select_status(datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc))

    assert status == DisplayStatus(line1="CHIP 68F", line2="OUT 74F 45%", backlight="green")


def test_agent_status_overrides_spotify() -> None:
    status_engine.set_spotify_source(
        FakeSpotifySource(DisplayStatus(line1="Song", line2="Artist", backlight="blue"))
    )
    status_engine.set_agent_status_value("working")

    status = status_engine.select_status(datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc))

    assert status == status_engine.AGENT_STATUSES["working"]


def test_calendar_status_overrides_spotify() -> None:
    status_engine.set_calendar_source(FakeCalendarSource())
    status_engine.set_spotify_source(
        FakeSpotifySource(DisplayStatus(line1="Song", line2="Artist", backlight="blue"))
    )

    status = status_engine.select_status(datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc))

    assert status == DisplayStatus(line1="MEETING", line2="NOW", backlight="red")


def test_manual_mode_overrides_spotify() -> None:
    status_engine.set_spotify_source(
        FakeSpotifySource(DisplayStatus(line1="Song", line2="Artist", backlight="blue"))
    )
    status_engine.set_active_mode("idle")

    status = status_engine.select_status(datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc))

    assert status == status_engine.STATUS_MODES["idle"]


def test_spotify_source_formats_playing_track_for_firmware_scroll() -> None:
    source = FakeHttpSpotifySource(
        {
            "is_playing": True,
            "currently_playing_type": "track",
            "item": {
                "name": "A Very Long Track Title",
                "artists": [{"name": "A Very Long Artist Name"}],
            },
        }
    )

    state = source.select_status()

    assert state.status == DisplayStatus(
        line1="A Very Long Track Title",
        line2="A Very Long Artist Name",
        backlight="blue",
        effect="scroll",
    )


def test_spotify_source_ignores_paused_playback() -> None:
    source = FakeHttpSpotifySource(
        {
            "is_playing": False,
            "currently_playing_type": "track",
            "item": {
                "name": "Paused Track",
                "artists": [{"name": "Artist"}],
            },
        }
    )

    state = source.select_status()

    assert state.status is None
