# Desk Deck Companion Test Server

This is the first local test server for Desk Deck. It returns display JSON so the ESP32 can prove Wi-Fi and HTTP polling before Calendar or Spotify are added.

## Setup

```powershell
cd companion
python3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Find the Windows computer's LAN IP with:

```powershell
ipconfig
```

Then set `STATUS_SERVER_URL` in `firmware/src/secrets.h`, for example:

```cpp
constexpr const char* STATUS_SERVER_URL = "http://192.168.1.100:8000/api/status";
```

## Status Modes

The active mode is stored in memory and resets to `online` when the server restarts.

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/status
Invoke-RestMethod http://127.0.0.1:8000/api/status/modes
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/status/mode/meeting
```

Available modes:

```text
online        DESK DECK / ONLINE / green
idle          IDLE / READY / green
meeting_soon  MEETING / IN 5 / yellow
meeting       IN A MEETING / BUSY / red
music         NOW PLAYING / TEST TRACK / blue
notify        SERVER TEST / NOTICE / purple
```

Future note: AI-agent status can later map `working` to yellow, `done` to green, and `blocked` or `error` to red.
