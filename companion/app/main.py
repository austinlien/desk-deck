from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Desk Deck Companion Test Server")


class DisplayStatus(BaseModel):
    line1: str
    line2: str
    backlight: str


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
}

active_mode = "online"


@app.get("/api/status", response_model=DisplayStatus)
def get_status() -> DisplayStatus:
    return STATUS_MODES[active_mode]


@app.get("/api/status/modes")
def get_status_modes() -> dict[str, DisplayStatus]:
    return STATUS_MODES


@app.post("/api/status/mode/{mode_name}", response_model=DisplayStatus)
def set_status_mode(mode_name: str) -> DisplayStatus:
    global active_mode

    if mode_name not in STATUS_MODES:
        raise HTTPException(status_code=404, detail=f"Unknown status mode: {mode_name}")

    active_mode = mode_name
    return STATUS_MODES[active_mode]
