from __future__ import annotations

import asyncio
import os
import threading
from typing import Any

from .models import DisplayStatus, SpotifyState, SpotifyTrack
from .spotify_source import _normalize_line


class WindowsMediaSpotifySource:
    """Maintains the currently playing local Spotify track from Windows media sessions."""

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._refresh_event: asyncio.Event | None = None
        self._manager: Any | None = None
        self._session: Any | None = None
        self._session_handlers: list[tuple[Any, int]] = []
        self._state = SpotifyState(
            enabled=enabled,
            configured=enabled,
            available=False,
            detail="Windows media listener has not started.",
        )

    @classmethod
    def from_environment(cls) -> "WindowsMediaSpotifySource":
        enabled = os.getenv("DESK_DECK_WINDOWS_MEDIA_ENABLED", "1").lower() not in {
            "0",
            "false",
            "no",
        }
        return cls(enabled=enabled)

    def start(self) -> None:
        if not self.enabled or self._thread is not None:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="desk-deck-windows-media",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        loop = self._loop
        event = self._refresh_event
        if loop is not None and event is not None:
            loop.call_soon_threadsafe(event.set)
        thread = self._thread
        if thread is not None:
            thread.join(timeout=3)
        self._thread = None

    def select_status(self) -> SpotifyState:
        with self._lock:
            return self._state.model_copy(deep=True)

    def _run(self) -> None:
        try:
            asyncio.run(self._watch())
        except Exception as exc:
            self._set_unavailable(f"Windows media listener unavailable: {exc}")

    async def _watch(self) -> None:
        try:
            from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager
        except ImportError:
            self._set_unavailable("Windows media support is not installed.")
            return

        manager = await GlobalSystemMediaTransportControlsSessionManager.request_async()
        self._manager = manager
        self._loop = asyncio.get_running_loop()
        self._refresh_event = asyncio.Event()
        manager.add_sessions_changed(self._schedule_refresh)
        manager.add_current_session_changed(self._schedule_refresh)
        await self._refresh()

        while not self._stop_event.is_set():
            try:
                await asyncio.wait_for(self._refresh_event.wait(), timeout=0.5)
            except asyncio.TimeoutError:
                continue
            self._refresh_event.clear()
            await self._refresh()

        self._remove_session_handlers()
        self._manager = None
        self._loop = None
        self._refresh_event = None

    def _schedule_refresh(self, *_: Any) -> None:
        loop = self._loop
        event = self._refresh_event
        if loop is not None and event is not None:
            loop.call_soon_threadsafe(event.set)

    async def _refresh(self) -> None:
        manager = self._manager
        if manager is None:
            return
        try:
            session = self._playing_spotify_session(manager.get_sessions())
            self._subscribe_to_session(session)
            if session is None:
                with self._lock:
                    self._state = SpotifyState(enabled=True, configured=True, available=True)
                return

            properties = await session.try_get_media_properties_async()
            title = _normalize_line(properties.title or "Spotify")
            artist = _normalize_line(properties.artist or "Unknown Artist")
            track = SpotifyTrack(title=title, artist=artist, is_playing=True)
            with self._lock:
                self._state = SpotifyState(
                    enabled=True,
                    configured=True,
                    available=True,
                    source="windows",
                    track=track,
                    status=DisplayStatus(
                        line1=title,
                        line2=artist,
                        backlight="green",
                        effect="scroll",
                    ),
                )
        except Exception as exc:
            self._set_unavailable(f"Windows media read failed: {exc}")

    @staticmethod
    def _playing_spotify_session(sessions: Any) -> Any | None:
        for session in sessions:
            app_id = str(getattr(session, "source_app_user_model_id", "")).lower()
            if "spotify" not in app_id:
                continue
            playback = getattr(session.get_playback_info(), "playback_status", None)
            playback_name = str(getattr(playback, "name", playback)).lower()
            if playback_name.endswith("playing"):
                return session
        return None

    def _subscribe_to_session(self, session: Any | None) -> None:
        if session is self._session:
            return
        self._remove_session_handlers()
        self._session = session
        if session is None:
            return
        self._session_handlers = [
            (session.remove_media_properties_changed, session.add_media_properties_changed(self._schedule_refresh)),
            (session.remove_playback_info_changed, session.add_playback_info_changed(self._schedule_refresh)),
        ]

    def _remove_session_handlers(self) -> None:
        for remove_handler, token in self._session_handlers:
            try:
                remove_handler(token)
            except Exception:
                pass
        self._session_handlers = []
        self._session = None

    def _set_unavailable(self, detail: str) -> None:
        with self._lock:
            self._state = SpotifyState(
                enabled=self.enabled,
                configured=self.enabled,
                available=False,
                detail=detail,
            )
