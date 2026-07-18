from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from . import status_engine
from .calendar_source import GoogleCalendarSource
from .models import (
    CalendarState,
    DebugState,
    DisplayStatus,
    InsideSensorReading,
    SpotifyState,
    StatusInputs,
    WeatherState,
)
from .hybrid_spotify_source import HybridSpotifySource
from .weather_source import WeatherSource

spotify_source = HybridSpotifySource.from_environment()


@asynccontextmanager
async def lifespan(_: FastAPI):
    spotify_source.start()
    try:
        yield
    finally:
        spotify_source.stop()


app = FastAPI(title="Desk Deck Companion Server", lifespan=lifespan)
status_engine.set_calendar_source(GoogleCalendarSource.from_environment())
status_engine.set_spotify_source(spotify_source)
weather_source = WeatherSource.from_environment()
status_engine.set_weather_source(weather_source)


@app.get("/api/status", response_model=DisplayStatus)
def get_status() -> DisplayStatus:
    return status_engine.select_status()


@app.get("/api/status/modes")
def get_status_modes() -> dict[str, DisplayStatus]:
    return status_engine.STATUS_MODES


@app.get("/api/agent/status")
def get_agent_status() -> dict[str, str | None]:
    return {"state": status_engine.get_agent_status_value()}


@app.post("/api/agent/status/{state}", response_model=DisplayStatus)
def set_agent_status(state: str) -> DisplayStatus:
    if state not in status_engine.AGENT_STATUSES:
        raise HTTPException(status_code=404, detail=f"Unknown agent status: {state}")

    status_engine.set_agent_status_value(state)
    return status_engine.select_status()


@app.post("/api/agent/reset", response_model=DisplayStatus)
def reset_agent_status() -> DisplayStatus:
    status_engine.set_agent_status_value(None)
    return status_engine.select_status()


@app.post("/api/status/mode/{mode_name}", response_model=DisplayStatus)
def set_status_mode(mode_name: str) -> DisplayStatus:
    if mode_name not in status_engine.STATUS_MODES:
        raise HTTPException(status_code=404, detail=f"Unknown status mode: {mode_name}")

    status_engine.set_active_mode(mode_name)
    return status_engine.select_status()


@app.get("/api/calendar/status", response_model=CalendarState)
def get_calendar_status() -> CalendarState:
    return status_engine.select_calendar_status()


@app.get("/api/spotify/status", response_model=SpotifyState)
def get_spotify_status() -> SpotifyState:
    return status_engine.select_spotify_status()


@app.get("/api/weather/status", response_model=WeatherState)
def get_weather_status() -> WeatherState:
    state = status_engine.get_weather_state()
    if state is None:
        raise HTTPException(status_code=404, detail="Weather source is not configured")
    return state


@app.post("/api/sensors/inside", response_model=WeatherState)
def set_inside_sensor(reading: InsideSensorReading) -> WeatherState:
    return weather_source.update_inside(reading)


@app.get("/api/debug/inputs", response_model=DebugState)
def get_debug_inputs() -> DebugState:
    return DebugState(
        manual_override=status_engine.active_mode,
        agent_override=status_engine.agent_status,
        inputs=status_engine.status_inputs,
    )


@app.post("/api/debug/inputs", response_model=DebugState)
def set_debug_inputs(inputs: StatusInputs) -> DebugState:
    status_engine.set_status_inputs(inputs)
    return DebugState(
        manual_override=status_engine.active_mode,
        agent_override=status_engine.agent_status,
        inputs=status_engine.status_inputs,
    )


@app.post("/api/debug/reset", response_model=DisplayStatus)
def reset_debug_state() -> DisplayStatus:
    status_engine.reset_state()
    return status_engine.select_status()
