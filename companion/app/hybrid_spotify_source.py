from __future__ import annotations

from .models import SpotifyState
from .spotify_source import SpotifySource
from .windows_media_source import WindowsMediaSpotifySource


class HybridSpotifySource:
    """Prefers event-driven local Spotify playback, with Web API remote fallback."""

    def __init__(
        self,
        windows_source: WindowsMediaSpotifySource,
        remote_source: SpotifySource | None,
    ) -> None:
        self.windows_source = windows_source
        self.remote_source = remote_source

    @classmethod
    def from_environment(cls) -> "HybridSpotifySource":
        return cls(
            windows_source=WindowsMediaSpotifySource.from_environment(),
            remote_source=SpotifySource.from_environment(),
        )

    def start(self) -> None:
        self.windows_source.start()

    def stop(self) -> None:
        self.windows_source.stop()

    def select_status(self) -> SpotifyState:
        local = self.windows_source.select_status()
        if local.status is not None:
            return local

        if self.remote_source is not None:
            remote = self.remote_source.select_status()
            if remote.status is not None:
                return remote
            return SpotifyState(
                enabled=local.enabled or remote.enabled,
                configured=local.configured or remote.configured,
                available=local.available or remote.available,
                detail=remote.detail or local.detail,
            )

        return local
