from datetime import datetime, timedelta, timezone

from app import status_engine
from app.models import DisplayStatus, InsideSensorReading, WeatherState
from app.weather_source import WeatherSource


class FakeWeatherSource:
    def __init__(self) -> None:
        self.status = DisplayStatus(line1="CHIP 68F", line2="OUT 74F 45%", backlight="green")

    def select_status(self, now: datetime | None = None) -> DisplayStatus:
        return self.status

    def get_state(self, now: datetime | None = None) -> WeatherState:
        return WeatherState(
            enabled=True,
            available=True,
            location="San Jose, CA",
            inside_temperature_f=68,
            outside_temperature_f=74,
            outside_humidity_percent=45,
            status=self.status,
        )


class FakeWttrWeatherSource(WeatherSource):
    def __init__(self) -> None:
        super().__init__(location="San Jose, CA")
        self.fetch_count = 0

    def _fetch_outside_weather(self) -> dict:
        self.fetch_count += 1
        return {"current_condition": [{"temp_F": "74", "humidity": "45"}]}


def setup_function() -> None:
    status_engine.reset_state()
    status_engine.set_calendar_source(None)
    status_engine.set_spotify_source(None)
    status_engine.set_weather_source(FakeWeatherSource())


def test_weather_is_default_status() -> None:
    status = status_engine.select_status(datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc))

    assert status == DisplayStatus(line1="CHIP 68F", line2="OUT 74F 45%", backlight="green")


def test_agent_done_holds_briefly_then_returns_to_weather() -> None:
    now = datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)
    status_engine.set_agent_status_value("done", now=now)

    assert status_engine.select_status(now + timedelta(seconds=4)).line1 == "AGENT"
    assert status_engine.select_status(now + timedelta(seconds=5)).line1 == "CHIP 68F"


def test_working_agent_still_overrides_weather() -> None:
    status_engine.set_agent_status_value("working")

    status = status_engine.select_status()

    assert status == status_engine.AGENT_STATUSES["working"]


def test_working_agent_expires_after_active_ttl() -> None:
    now = datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)
    status_engine.set_agent_status_value("working", now=now)

    status = status_engine.select_status(now + timedelta(seconds=status_engine.AGENT_ACTIVE_TTL_SECONDS))

    assert status == DisplayStatus(line1="CHIP 68F", line2="OUT 74F 45%", backlight="green")


def test_waiting_agent_expires_after_active_ttl() -> None:
    now = datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)
    status_engine.set_agent_status_value("waiting", now=now)

    status = status_engine.select_status(now + timedelta(seconds=status_engine.AGENT_ACTIVE_TTL_SECONDS))

    assert status == DisplayStatus(line1="CHIP 68F", line2="OUT 74F 45%", backlight="green")


def test_agent_status_refresh_extends_active_ttl() -> None:
    now = datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)
    status_engine.set_agent_status_value("working", now=now)
    status_engine.set_agent_status_value("working", now=now + timedelta(seconds=250))

    status = status_engine.select_status(now + timedelta(seconds=500))

    assert status == status_engine.AGENT_STATUSES["working"]


def test_expired_agent_status_endpoint_reports_none() -> None:
    now = datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)
    status_engine.set_agent_status_value("working", now=now)

    state = status_engine.get_agent_status_value(now + timedelta(seconds=status_engine.AGENT_ACTIVE_TTL_SECONDS))

    assert state is None


def test_weather_source_formats_inside_outside_and_humidity() -> None:
    source = FakeWttrWeatherSource()
    source.update_inside(InsideSensorReading(temperature_f=68.2))

    state = source.get_state(datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc))

    assert state.status.line1 == "CHIP 68F"
    assert state.status.line2 == "OUT 74F 45%"
    assert state.available is True


def test_weather_source_applies_inside_temperature_offset() -> None:
    source = WeatherSource(inside_temp_offset_f=-5)
    source.update_inside(InsideSensorReading(temperature_f=73))

    assert source.inside_temperature_f == 68


def test_weather_source_uses_cached_values_when_refresh_fails() -> None:
    class FailingAfterFirstFetch(FakeWttrWeatherSource):
        def _fetch_outside_weather(self) -> dict:
            if self.fetch_count == 0:
                return super()._fetch_outside_weather()
            self.fetch_count += 1
            raise RuntimeError("weather unavailable")

    source = FailingAfterFirstFetch()
    first = datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)
    source.get_state(first)
    state = source.get_state(first + timedelta(minutes=11))

    assert state.outside_temperature_f == 74
    assert state.outside_humidity_percent == 45
    assert state.detail == "weather unavailable"
