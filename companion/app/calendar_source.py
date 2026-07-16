from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .models import CalendarState
from .status_engine import calendar_status_from_event_window

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
DEFAULT_CREDENTIALS_PATH = Path("secrets/credentials.json")
DEFAULT_TOKEN_PATH = Path("secrets/token.json")
DEFAULT_CACHE_SECONDS = 30


class GoogleCalendarSource:
    def __init__(
        self,
        credentials_path: Path = DEFAULT_CREDENTIALS_PATH,
        token_path: Path = DEFAULT_TOKEN_PATH,
        calendar_id: str = "primary",
        cache_seconds: int = DEFAULT_CACHE_SECONDS,
    ) -> None:
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.calendar_id = calendar_id
        self.cache_ttl = timedelta(seconds=cache_seconds)
        self.cached_events: list[dict[str, Any]] | None = None
        self.last_fetch_at: datetime | None = None
        self.last_error: str | None = None
        self._service: Any | None = None

    @classmethod
    def from_environment(cls) -> "GoogleCalendarSource | None":
        enabled = os.getenv("DESK_DECK_CALENDAR_ENABLED", "1").lower() not in {"0", "false", "no"}
        if not enabled:
            return None

        credentials_path = Path(os.getenv("DESK_DECK_GOOGLE_CREDENTIALS", DEFAULT_CREDENTIALS_PATH))
        token_path = Path(os.getenv("DESK_DECK_GOOGLE_TOKEN", DEFAULT_TOKEN_PATH))
        calendar_id = os.getenv("DESK_DECK_GOOGLE_CALENDAR_ID", "primary")
        cache_seconds = int(os.getenv("DESK_DECK_CALENDAR_CACHE_SECONDS", str(DEFAULT_CACHE_SECONDS)))
        if not credentials_path.exists() and not token_path.exists():
            return None
        return cls(
            credentials_path=credentials_path,
            token_path=token_path,
            calendar_id=calendar_id,
            cache_seconds=cache_seconds,
        )

    def select_status(self, now: datetime | None = None) -> CalendarState:
        now = now or datetime.now().astimezone()
        try:
            for event in self._candidate_events(now):
                window = _event_window(event)
                if window is None:
                    continue

                event_start, event_end = window
                if not _counts_as_meeting(event):
                    continue

                status = calendar_status_from_event_window(now, event_start, event_end)
                if status is not None:
                    return CalendarState(enabled=True, available=True, status=status)
        except Exception as exc:
            return CalendarState(enabled=True, available=False, detail=str(exc))

        return CalendarState(enabled=True, available=True)

    def _candidate_events(self, now: datetime) -> list[dict[str, Any]]:
        if self.cached_events is not None and self.last_fetch_at is not None:
            if now - self.last_fetch_at < self.cache_ttl:
                return self.cached_events
        if self.last_error is not None and self.last_fetch_at is not None:
            if now - self.last_fetch_at < self.cache_ttl:
                raise RuntimeError(self.last_error)

        try:
            self.cached_events = self._fetch_candidate_events(now)
            self.last_error = None
            return self.cached_events
        except Exception as exc:
            self.last_error = str(exc)
            raise
        finally:
            self.last_fetch_at = now

    def _fetch_candidate_events(self, now: datetime) -> list[dict[str, Any]]:
        service = self._get_service()
        time_min = (now - timedelta(hours=12)).isoformat()
        time_max = (now + timedelta(minutes=10)).isoformat()
        response = (
            service.events()
            .list(
                calendarId=self.calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        return response.get("items", [])

    def _get_service(self) -> Any:
        if self._service is not None:
            return self._service

        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise RuntimeError(
                "Google Calendar dependencies are not installed. Run pip install -r requirements.txt."
            ) from exc

        credentials = None
        if self.token_path.exists():
            credentials = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)

        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                if not self.credentials_path.exists():
                    raise RuntimeError(f"Missing Google OAuth credentials: {self.credentials_path}")
                flow = InstalledAppFlow.from_client_secrets_file(str(self.credentials_path), SCOPES)
                credentials = flow.run_local_server(port=0)

            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            self.token_path.write_text(credentials.to_json(), encoding="utf-8")

        self._service = build("calendar", "v3", credentials=credentials)
        return self._service


def _event_window(event: dict[str, Any]) -> tuple[datetime, datetime] | None:
    start = event.get("start", {})
    end = event.get("end", {})
    if "date" in start or "date" in end:
        return None

    start_value = start.get("dateTime")
    end_value = end.get("dateTime")
    if not start_value or not end_value:
        return None

    return _parse_google_datetime(start_value), _parse_google_datetime(end_value)


def _parse_google_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _counts_as_meeting(event: dict[str, Any]) -> bool:
    if event.get("status") == "cancelled":
        return False
    if event.get("transparency") == "transparent":
        return False

    for attendee in event.get("attendees", []):
        if attendee.get("self"):
            return attendee.get("responseStatus") == "accepted"

    organizer = event.get("organizer", {})
    creator = event.get("creator", {})
    return bool(organizer.get("self") or creator.get("self") or not event.get("attendees"))
