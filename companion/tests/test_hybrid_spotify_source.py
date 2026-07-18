from app.hybrid_spotify_source import HybridSpotifySource
from app.models import DisplayStatus, SpotifyState, SpotifyTrack
from app.windows_media_source import WindowsMediaSpotifySource


class FakeWindowsSource:
    def __init__(self, state: SpotifyState) -> None:
        self.state = state
        self.started = False
        self.stopped = False

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True

    def select_status(self) -> SpotifyState:
        return self.state


class FakeRemoteSource:
    def __init__(self, state: SpotifyState) -> None:
        self.state = state
        self.calls = 0

    def select_status(self) -> SpotifyState:
        self.calls += 1
        return self.state


def _playing_state(title: str, source: str) -> SpotifyState:
    return SpotifyState(
        enabled=True,
        configured=True,
        available=True,
        source=source,
        track=SpotifyTrack(title=title, artist="Artist", is_playing=True),
        status=DisplayStatus(line1=title, line2="Artist", backlight="green", effect="scroll"),
    )


def test_local_windows_playback_suppresses_remote_api_calls() -> None:
    windows = FakeWindowsSource(_playing_state("Local Song", "windows"))
    remote = FakeRemoteSource(_playing_state("Remote Song", "spotify_api"))
    source = HybridSpotifySource(windows, remote)  # type: ignore[arg-type]

    state = source.select_status()

    assert state.source == "windows"
    assert state.track is not None and state.track.title == "Local Song"
    assert remote.calls == 0


def test_paused_or_absent_local_playback_uses_remote_fallback() -> None:
    windows = FakeWindowsSource(
        SpotifyState(enabled=True, configured=True, available=True)
    )
    remote = FakeRemoteSource(_playing_state("Remote Song", "spotify_api"))
    source = HybridSpotifySource(windows, remote)  # type: ignore[arg-type]

    state = source.select_status()

    assert state.source == "spotify_api"
    assert state.track is not None and state.track.title == "Remote Song"
    assert remote.calls == 1


def test_hybrid_reports_remote_or_windows_diagnostic_when_no_track_is_playing() -> None:
    windows = FakeWindowsSource(
        SpotifyState(enabled=True, configured=True, available=False, detail="Windows unavailable")
    )
    remote = FakeRemoteSource(
        SpotifyState(enabled=True, configured=True, available=False, detail="Remote unavailable")
    )
    source = HybridSpotifySource(windows, remote)  # type: ignore[arg-type]

    state = source.select_status()

    assert state.status is None
    assert state.source is None
    assert state.detail == "Remote unavailable"


def test_windows_source_accepts_only_active_spotify_sessions() -> None:
    class PlaybackStatus:
        def __init__(self, name: str) -> None:
            self.name = name

    class Playback:
        def __init__(self, value: str) -> None:
            self.playback_status = PlaybackStatus(value)

    class Session:
        def __init__(self, app_id: str, playback: str) -> None:
            self.source_app_user_model_id = app_id
            self.playback = playback

        def get_playback_info(self) -> Playback:
            return Playback(self.playback)

    other = Session("Microsoft.ZuneMusic", "PLAYING")
    paused_spotify = Session("SpotifyAB.SpotifyMusic", "PAUSED")
    playing_spotify = Session("SpotifyAB.SpotifyMusic", "PLAYING")

    assert WindowsMediaSpotifySource._playing_spotify_session([other, paused_spotify]) is None
    assert WindowsMediaSpotifySource._playing_spotify_session([other, playing_spotify]) is playing_spotify
