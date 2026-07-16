from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Desk Deck Companion Test Server")


class DisplayStatus(BaseModel):
    line1: str
    line2: str
    backlight: str


class StatusInputs(BaseModel):
    meeting_soon: bool = False
    active_meeting: bool = False
    notification: bool = False
    spotify_playing: bool = False
    spotify_paused: bool = False


class DebugState(BaseModel):
    manual_override: str | None
    inputs: StatusInputs


STATUS_MODES: dict[str, DisplayStatus] = {
    "online": DisplayStatus(
        line1="DESK DECK",
        line2="ONLINE",
        backlight="green",
    ),
    "idle": DisplayStatus(
        line1="IDLE",
        line2="READY",
        backlight="green",
    ),
    "meeting_soon": DisplayStatus(
        line1="MEETING",
        line2="IN 5",
        backlight="yellow",
    ),
    "meeting": DisplayStatus(
        line1="IN A MEETING",
        line2="BUSY",
        backlight="red",
    ),
    "music": DisplayStatus(
        line1="NOW PLAYING",
        line2="TEST TRACK",
        backlight="blue",
    ),
    "notify": DisplayStatus(
        line1="SERVER TEST",
        line2="NOTICE",
        backlight="purple",
    ),
    "spotify_paused": DisplayStatus(
        line1="PAUSED",
        line2="TEST TRACK",
        backlight="blue",
    ),
}

active_mode: str | None = None
status_inputs = StatusInputs()


def select_status() -> DisplayStatus:
    if active_mode is not None:
        return STATUS_MODES[active_mode]

    if status_inputs.meeting_soon:
        return STATUS_MODES["meeting_soon"]
    if status_inputs.active_meeting:
        return STATUS_MODES["meeting"]
    if status_inputs.notification:
        return STATUS_MODES["notify"]
    if status_inputs.spotify_playing:
        return STATUS_MODES["music"]
    if status_inputs.spotify_paused:
        return STATUS_MODES["spotify_paused"]
    return STATUS_MODES["online"]


@app.get("/api/status", response_model=DisplayStatus)
def get_status() -> DisplayStatus:
    return select_status()


@app.get("/api/status/modes")
def get_status_modes() -> dict[str, DisplayStatus]:
    return STATUS_MODES


@app.post("/api/status/mode/{mode_name}", response_model=DisplayStatus)
def set_status_mode(mode_name: str) -> DisplayStatus:
    global active_mode

    if mode_name not in STATUS_MODES:
        raise HTTPException(status_code=404, detail=f"Unknown status mode: {mode_name}")

    active_mode = mode_name
    return select_status()


@app.get("/api/debug/inputs", response_model=DebugState)
def get_debug_inputs() -> DebugState:
    return DebugState(manual_override=active_mode, inputs=status_inputs)


@app.post("/api/debug/inputs", response_model=DebugState)
def set_debug_inputs(inputs: StatusInputs) -> DebugState:
    global status_inputs

    status_inputs = inputs
    return DebugState(manual_override=active_mode, inputs=status_inputs)


@app.post("/api/debug/reset", response_model=DisplayStatus)
def reset_debug_state() -> DisplayStatus:
    global active_mode, status_inputs

    active_mode = None
    status_inputs = StatusInputs()
    return select_status()
