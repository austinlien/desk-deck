from datetime import datetime, timedelta, timezone

import httpx

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
            track=SpotifyTrack(title=self.status.line1, artist=self.status.line2, is_playing=True)
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
    def __init__(self, payload: dict | None, clock=None) -> None:
        super().__init__(
            client_id="client",
            client_secret="secret",
            cache_seconds=5,
            error_backoff_seconds=30,
            clock=clock or (lambda: 0.0),
        )
        self.payload = payload
        self.exception: Exception | None = None
        self.fetch_count = 0

    def _access_token(self) -> str:
        return "token"

    def _fetch_payload(self, token: str):
        self.fetch_count += 1
        if self.exception is not None:
            raise self.exception
        return self.payload


def setup_function() -> None:
    status_engine.reset_state()
    status_engine.set_calendar_source(None)
    status_engine.set_spotify_source(None)
    status_engine.set_weather_source(FakeWeatherSource())


def test_spotify_playing_overrides_weather() -> None:
    status_engine.set_spotify_source(
        FakeSpotifySource(DisplayStatus(line1="Song", line2="Artist", backlight="green"))
    )

    status = status_engine.select_status(datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc))

    assert status == DisplayStatus(line1="Song", line2="Artist", backlight="green")


def test_spotify_rotates_to_weather_after_default_hold() -> None:
    now = datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)
    status_engine.set_spotify_source(
        FakeSpotifySource(DisplayStatus(line1="Song", line2="Artist", backlight="green"))
    )

    first = status_engine.select_status(now)
    weather = status_engine.select_status(now + timedelta(seconds=4))
    time_status = status_engine.select_status(now + timedelta(seconds=9))
    next_spotify = status_engine.select_status(now + timedelta(seconds=13))

    assert first == DisplayStatus(line1="Song", line2="Artist", backlight="green")
    assert weather == DisplayStatus(line1="CHIP 68F", line2="OUT 74F 45%", backlight="green")
    assert time_status == DisplayStatus(line1="9:00 AM", line2="THU JUL 16", backlight="green")
    assert next_spotify == DisplayStatus(line1="Song", line2="Artist", backlight="green")


def test_long_spotify_text_uses_one_scroll_pass_before_weather() -> None:
    now = datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)
    status_engine.set_spotify_source(
        FakeSpotifySource(
            DisplayStatus(
                line1="12345678901234567890",
                line2="Artist",
                backlight="green",
                effect="scroll",
            )
        )
    )

    spotify = status_engine.select_status(now)
    still_spotify = status_engine.select_status(now + timedelta(seconds=3.3))
    weather = status_engine.select_status(now + timedelta(seconds=3.4))

    assert spotify == DisplayStatus(
        line1="12345678901234567890",
        line2="Artist",
        backlight="green",
        effect="scroll_once",
    )
    assert still_spotify.effect == "scroll_once"
    assert weather == DisplayStatus(line1="CHIP 68F", line2="OUT 74F 45%", backlight="green")


def test_spotify_track_change_resets_rotation_to_spotify() -> None:
    now = datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)
    source = FakeSpotifySource(DisplayStatus(line1="Song A", line2="Artist", backlight="green"))
    status_engine.set_spotify_source(source)

    assert status_engine.select_status(now).line1 == "Song A"
    assert status_engine.select_status(now + timedelta(seconds=4)).line1 == "CHIP 68F"

    source.status = DisplayStatus(line1="Song B", line2="Artist", backlight="green")

    assert status_engine.select_status(now + timedelta(seconds=9)) == DisplayStatus(
        line1="Song B",
        line2="Artist",
        backlight="green",
    )


def test_higher_priority_status_reset_rotation_when_cleared() -> None:
    now = datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)
    status_engine.set_spotify_source(
        FakeSpotifySource(DisplayStatus(line1="Song", line2="Artist", backlight="green"))
    )

    assert status_engine.select_status(now).line1 == "Song"
    status_engine.set_agent_status_value("working")
    assert status_engine.select_status(now + timedelta(seconds=4)).line1 == "AGENT"
    status_engine.set_agent_status_value(None)

    assert status_engine.select_status(now + timedelta(seconds=5)) == DisplayStatus(
        line1="Song",
        line2="Artist",
        backlight="green",
    )


def test_spotify_paused_or_absent_falls_back_to_weather() -> None:
    status_engine.set_spotify_source(FakeSpotifySource(None))

    status = status_engine.select_status(datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc))

    assert status == DisplayStatus(line1="CHIP 68F", line2="OUT 74F 45%", backlight="green")


def test_debug_spotify_track_can_interrupt_agent_working_after_a_song_skip() -> None:
    now = datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)
    status_engine.set_status_inputs(
        status_engine.StatusInputs(
            spotify_playing=True,
            spotify_title="Somebody Told Me",
            spotify_artist="The Killers",
        )
    )
    status_engine.set_agent_status_value("working", now=now)

    assert status_engine.select_status(now) == status_engine.AGENT_STATUSES["working"]

    status_engine.set_status_inputs(
        status_engine.StatusInputs(
            spotify_playing=True,
            spotify_title="Mr. Brightside",
            spotify_artist="The Killers",
        )
    )

    assert status_engine.select_status(now + timedelta(seconds=1)) == DisplayStatus(
        line1="Mr. Brightside",
        line2="The Killers",
        backlight="yellow",
        effect="solid",
    )


def test_demo_default_rotation_suppresses_live_spotify() -> None:
    status_engine.set_spotify_source(
        FakeSpotifySource(DisplayStatus(line1="Live Song", line2="Live Artist", backlight="green"))
    )
    status_engine.set_status_inputs(status_engine.StatusInputs(demo_default_rotation=True))

    status = status_engine.select_status(datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc))

    assert status == DisplayStatus(line1="CHIP 68F", line2="OUT 74F 45%", backlight="green")


def test_debug_meeting_now_flashes() -> None:
    status_engine.set_status_inputs(status_engine.StatusInputs(active_meeting=True))

    assert status_engine.select_debug_status() == DisplayStatus(
        line1="MEETING",
        line2="NOW",
        backlight="red",
        effect="flash",
    )


def test_agent_status_overrides_spotify() -> None:
    status_engine.set_spotify_source(
        FakeSpotifySource(DisplayStatus(line1="Song", line2="Artist", backlight="green"))
    )
    status_engine.set_agent_status_value("working")

    status = status_engine.select_status(datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc))

    assert status == status_engine.AGENT_STATUSES["working"]


def test_calendar_status_overrides_spotify() -> None:
    status_engine.set_calendar_source(FakeCalendarSource())
    status_engine.set_spotify_source(
        FakeSpotifySource(DisplayStatus(line1="Song", line2="Artist", backlight="green"))
    )

    status = status_engine.select_status(datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc))

    assert status == DisplayStatus(line1="MEETING", line2="NOW", backlight="red")


def test_manual_mode_overrides_spotify() -> None:
    status_engine.set_spotify_source(
        FakeSpotifySource(DisplayStatus(line1="Song", line2="Artist", backlight="green"))
    )
    status_engine.set_active_mode("idle")

    status = status_engine.select_status(datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc))

    assert status == status_engine.STATUS_MODES["idle"]


def test_first_seen_spotify_track_does_not_interrupt_agent_status() -> None:
    now = datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)
    status_engine.set_agent_status_value("working")
    status_engine.set_spotify_source(
        FakeSpotifySource(DisplayStatus(line1="Song A", line2="Artist", backlight="green"))
    )

    status = status_engine.select_status(now)

    assert status == status_engine.AGENT_STATUSES["working"]


def test_spotify_track_change_interrupts_manual_mode_with_inherited_color() -> None:
    now = datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)
    source = FakeSpotifySource(DisplayStatus(line1="Song A", line2="Artist", backlight="green"))
    status_engine.set_spotify_source(source)
    status_engine.set_active_mode("meeting")

    assert status_engine.select_status(now) == status_engine.STATUS_MODES["meeting"]

    source.status = DisplayStatus(line1="Song B", line2="Artist", backlight="green")

    assert status_engine.select_status(now + timedelta(seconds=1)) == DisplayStatus(
        line1="Song B",
        line2="Artist",
        backlight="red",
    )


def test_spotify_track_change_interrupts_calendar_status_with_inherited_color() -> None:
    now = datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)
    source = FakeSpotifySource(DisplayStatus(line1="Song A", line2="Artist", backlight="green"))
    status_engine.set_spotify_source(source)
    status_engine.set_calendar_source(FakeCalendarSource())

    assert status_engine.select_status(now) == DisplayStatus(line1="MEETING", line2="NOW", backlight="red")

    source.status = DisplayStatus(line1="Song B", line2="Artist", backlight="green")

    assert status_engine.select_status(now + timedelta(seconds=1)) == DisplayStatus(
        line1="Song B",
        line2="Artist",
        backlight="red",
    )


def test_spotify_track_change_interrupts_agent_then_returns_to_agent() -> None:
    now = datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)
    source = FakeSpotifySource(DisplayStatus(line1="Song A", line2="Artist", backlight="green"))
    status_engine.set_spotify_source(source)
    status_engine.set_agent_status_value("working")

    assert status_engine.select_status(now) == status_engine.AGENT_STATUSES["working"]

    source.status = DisplayStatus(line1="Song B", line2="Artist", backlight="green")

    assert status_engine.select_status(now + timedelta(seconds=1)) == DisplayStatus(
        line1="Song B",
        line2="Artist",
        backlight="yellow",
    )
    assert status_engine.select_status(now + timedelta(seconds=6)) == status_engine.AGENT_STATUSES["working"]


def test_long_spotify_track_change_interrupts_waiting_agent_status() -> None:
    now = datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)
    source = FakeSpotifySource(DisplayStatus(line1="Song A", line2="Artist", backlight="green"))
    status_engine.set_spotify_source(source)
    status_engine.set_agent_status_value("waiting")
    status_engine.select_status(now)

    source.status = DisplayStatus(line1="12345678901234567890", line2="Artist", backlight="green")

    assert status_engine.select_status(now + timedelta(seconds=1)) == DisplayStatus(
        line1="12345678901234567890",
        line2="Artist",
        backlight="red",
        effect="scroll_once",
    )


def test_agent_status_resets_spotify_baseline_before_interrupts() -> None:
    now = datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)
    source = FakeSpotifySource(DisplayStatus(line1="Song A", line2="Artist", backlight="green"))
    status_engine.set_spotify_source(source)
    assert status_engine.select_status(now).line1 == "Song A"

    source.status = DisplayStatus(line1="Song B", line2="Artist", backlight="green")
    status_engine.set_agent_status_value("working", now=now + timedelta(seconds=1))

    assert status_engine.select_status(now + timedelta(seconds=2)) == status_engine.AGENT_STATUSES["working"]


def test_repeated_agent_working_update_keeps_spotify_skip_baseline() -> None:
    now = datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)
    source = FakeSpotifySource(DisplayStatus(line1="Song A", line2="Artist", backlight="green"))
    status_engine.set_spotify_source(source)
    status_engine.set_agent_status_value("working", now=now)
    assert status_engine.select_status(now) == status_engine.AGENT_STATUSES["working"]

    status_engine.set_agent_status_value("working", now=now + timedelta(seconds=1))
    source.status = DisplayStatus(line1="Song B", line2="Artist", backlight="green")

    assert status_engine.select_status(now + timedelta(seconds=2)) == DisplayStatus(
        line1="Song B",
        line2="Artist",
        backlight="yellow",
    )


def test_spotify_interrupt_continues_if_manual_status_clears_then_resumes_rotation() -> None:
    now = datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)
    source = FakeSpotifySource(DisplayStatus(line1="Song A", line2="Artist", backlight="green"))
    status_engine.set_spotify_source(source)
    status_engine.set_active_mode("meeting_soon")
    status_engine.select_status(now)

    source.status = DisplayStatus(line1="Song B", line2="Artist", backlight="green")
    assert status_engine.select_status(now + timedelta(seconds=1)).backlight == "yellow"

    status_engine.set_active_mode(None)

    assert status_engine.select_status(now + timedelta(seconds=2)).backlight == "yellow"
    assert status_engine.select_status(now + timedelta(seconds=6)) == DisplayStatus(
        line1="Song B",
        line2="Artist",
        backlight="green",
    )


def test_spotify_pause_resets_interrupt_baseline() -> None:
    now = datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)
    source = FakeSpotifySource(DisplayStatus(line1="Song A", line2="Artist", backlight="green"))
    status_engine.set_spotify_source(source)
    status_engine.set_agent_status_value("working")
    status_engine.select_status(now)

    source.status = None
    assert status_engine.select_status(now + timedelta(seconds=1)) == status_engine.AGENT_STATUSES["working"]

    source.status = DisplayStatus(line1="Song B", line2="Artist", backlight="green")
    assert status_engine.select_status(now + timedelta(seconds=2)) == status_engine.AGENT_STATUSES["working"]


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
        backlight="green",
        effect="scroll",
    )


def test_spotify_source_normalizes_lcd_unsafe_characters() -> None:
    source = FakeHttpSpotifySource(
        {
            "is_playing": True,
            "currently_playing_type": "track",
            "item": {
                "name": "Caf\u00e9 \u2014 th\u1ee7y \u2026",
                "artists": [{"name": "Beyonc\u00e9 \u00d8ffonoff"}],
            },
        }
    )

    state = source.select_status()

    assert state.status == DisplayStatus(
        line1="Cafe - thuy ...",
        line2="Beyonce Offonoff",
        backlight="green",
        effect="scroll",
    )


def test_spotify_source_caches_current_playback_between_status_polls() -> None:
    source = FakeHttpSpotifySource(
        {
            "is_playing": True,
            "currently_playing_type": "track",
            "item": {
                "name": "Cached Song",
                "artists": [{"name": "Cached Artist"}],
            },
        }
    )

    first = source.select_status()
    second = source.select_status()

    assert first.status == DisplayStatus(
        line1="Cached Song",
        line2="Cached Artist",
        backlight="green",
        effect="scroll",
    )
    assert second.status == first.status
    assert source.fetch_count == 1


def test_spotify_source_keeps_last_song_during_rate_limit_backoff() -> None:
    clock_value = [0.0]
    source = FakeHttpSpotifySource(
        {
            "is_playing": True,
            "currently_playing_type": "track",
            "item": {
                "name": "Last Good Song",
                "artists": [{"name": "Last Good Artist"}],
            },
        },
        clock=lambda: clock_value[0],
    )
    first = source.select_status()

    clock_value[0] = 6.0
    source.exception = _spotify_http_error(429, retry_after="10")
    limited = source.select_status()

    clock_value[0] = 7.0
    still_backed_off = source.select_status()

    assert first.status == DisplayStatus(
        line1="Last Good Song",
        line2="Last Good Artist",
        backlight="green",
        effect="scroll",
    )
    assert limited.status == first.status
    assert still_backed_off.status == first.status
    assert source.fetch_count == 2


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


def _spotify_http_error(status_code: int, retry_after: str | None = None) -> httpx.HTTPStatusError:
    request = httpx.Request("GET", "https://api.spotify.com/v1/me/player/currently-playing")
    headers = {}
    if retry_after is not None:
        headers["Retry-After"] = retry_after
    response = httpx.Response(status_code, headers=headers, request=request)
    return httpx.HTTPStatusError(f"HTTP {status_code}", request=request, response=response)
