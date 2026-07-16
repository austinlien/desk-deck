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
spotify_paused PAUSED / TEST TRACK / blue
```

Manual modes override debug inputs until reset.

## Agent Status Light

Agent status is a high-priority override for local coding-agent state. It wins over manual modes and debug inputs until reset.

Preferred repo-local scripts:

```powershell
.\scripts\agent-working.ps1
.\scripts\agent-waiting.ps1
.\scripts\agent-done.ps1
.\scripts\agent-reset.ps1
```

Direct API calls:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/agent/status/working
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/agent/status/waiting
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/agent/status/done
Invoke-RestMethod http://127.0.0.1:8000/api/agent/status
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/agent/reset
```

States:

```text
working  AGENT / WORKING / yellow
waiting  AGENT / WAITING / red
done     AGENT / DONE / green
```

Automatic Codex lifecycle detection is not implemented yet. For now, scripts, hooks, or a Codex instruction can call these local bridge endpoints explicitly.

## Debug Inputs

The debug input endpoints simulate future Calendar, notification, and Spotify integrations without firmware changes. The priority order is:

```text
meeting_soon
active_meeting
notification
spotify_playing
spotify_paused
online
```

Examples:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/debug/inputs

Invoke-RestMethod `
  -Method Post `
  -ContentType "application/json" `
  -Uri http://127.0.0.1:8000/api/debug/inputs `
  -Body '{"active_meeting":true,"spotify_playing":true}'

Invoke-RestMethod http://127.0.0.1:8000/api/status
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/debug/reset
```

Future note: automatic agent status can be revisited when there is a reliable lifecycle signal source.
