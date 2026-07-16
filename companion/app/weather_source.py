from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import quote

import httpx

from .models import DisplayStatus, InsideSensorReading, WeatherState

DEFAULT_LOCATION = "San Jose, CA"
DEFAULT_CACHE_SECONDS = 600


class WeatherSource:
    def __init__(
        self,
        location: str = DEFAULT_LOCATION,
        inside_temp_offset_f: float = 0,
        cache_seconds: int = DEFAULT_CACHE_SECONDS,
    ) -> None:
        self.location = location
        self.inside_temp_offset_f = inside_temp_offset_f
        self.cache_ttl = timedelta(seconds=cache_seconds)
        self.inside_temperature_f: float | None = None
        self.outside_temperature_f: float | None = None
        self.outside_humidity_percent: int | None = None
        self.last_fetch_at: datetime | None = None
        self.last_error: str | None = None

    @classmethod
    def from_environment(cls) -> "WeatherSource":
        return cls(
            location=os.getenv("DESK_DECK_WEATHER_LOCATION", DEFAULT_LOCATION),
            inside_temp_offset_f=float(os.getenv("DESK_DECK_INSIDE_TEMP_OFFSET_F", "0")),
        )

    def update_inside(self, reading: InsideSensorReading) -> WeatherState:
        self.inside_temperature_f = reading.temperature_f + self.inside_temp_offset_f
        return self.get_state()

    def get_state(self, now: datetime | None = None) -> WeatherState:
        now = now or datetime.now().astimezone()
        self._refresh_outside_weather(now)
        return WeatherState(
            enabled=True,
            available=self.outside_temperature_f is not None,
            location=self.location,
            inside_temperature_f=self.inside_temperature_f,
            outside_temperature_f=self.outside_temperature_f,
            outside_humidity_percent=self.outside_humidity_percent,
            status=self.select_status(now),
            detail=self.last_error,
        )

    def select_status(self, now: datetime | None = None) -> DisplayStatus:
        now = now or datetime.now().astimezone()
        self._refresh_outside_weather(now)
        return DisplayStatus(
            line1=f"CHIP {_format_temp(self.inside_temperature_f)}",
            line2=f"OUT {_format_temp(self.outside_temperature_f)} {_format_humidity(self.outside_humidity_percent)}",
            backlight="green",
        )

    def _refresh_outside_weather(self, now: datetime) -> None:
        if self.last_fetch_at is not None and now - self.last_fetch_at < self.cache_ttl:
            return

        try:
            payload = self._fetch_outside_weather()
            current = payload["current_condition"][0]
            self.outside_temperature_f = float(current["temp_F"])
            self.outside_humidity_percent = int(current["humidity"])
            self.last_fetch_at = now
            self.last_error = None
        except Exception as exc:
            self.last_error = str(exc)
            if self.outside_temperature_f is not None:
                self.last_fetch_at = now

    def _fetch_outside_weather(self) -> dict[str, Any]:
        location = quote(self.location)
        response = httpx.get(f"https://wttr.in/{location}", params={"format": "j1"}, timeout=5)
        response.raise_for_status()
        return response.json()


def _format_temp(value: float | None) -> str:
    if value is None:
        return "--F"
    return f"{round(value):.0f}F"


def _format_humidity(value: int | None) -> str:
    if value is None:
        return "--%"
    return f"{value}%"
