# Desk Deck Companion Test Server

This is the local companion server for Desk Deck. It returns display JSON for the ESP32 and can optionally read Google Calendar to show private meeting status.

## Setup

```powershell
cd companion
python3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Google Calendar MVP

Calendar support uses local Google OAuth and the primary calendar by default. It is disabled automatically when no credentials or token file exists.

1. Create a Google OAuth desktop client with the Calendar API enabled.
2. Download the OAuth client JSON to:

```text
companion/secrets/credentials.json
```

3. Start the companion server from the `companion/` directory. On the first Calendar request, a browser login opens and creates:

```text
companion/secrets/token.json
```

Both files are ignored by Git. Optional environment variables:

```powershell
$env:DESK_DECK_CALENDAR_ENABLED = "1"
$env:DESK_DECK_GOOGLE_CALENDAR_ID = "primary"
$env:DESK_DECK_GOOGLE_CREDENTIALS = "secrets/credentials.json"
$env:DESK_DECK_GOOGLE_TOKEN = "secrets/token.json"
```

Calendar event rules:

- Manual modes override Calendar.
- Calendar overrides agent status, then the stored agent status resumes when no meeting state is active.
- Declined, all-day, and free events are ignored.
- Accepted or owned busy timed events count as meetings.
- 10 to 5 minutes before start: `MEETING` / `SOON` / yellow.
- 5 minutes before start: `MEETING` / `SOON` / red.
- Started meetings: `MEETING` / `NOW` / red.

## Default Weather Screen

When no manual mode, Calendar state, active agent state, or debug input is active, the companion returns a default weather screen:

```text
CHIP 68F
OUT 74F 45%
```

The ESP32 posts its internal chip temperature reading to `POST /api/sensors/inside`; the companion applies an optional Fahrenheit offset and fetches outside weather for San Jose, CA from wttr.in.

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/weather/status

Invoke-RestMethod `
  -Method Post `
  -ContentType "application/json" `
  -Uri http://127.0.0.1:8000/api/sensors/inside `
  -Body '{"temperature_f":68}'
```

Optional environment variables:

```powershell
$env:DESK_DECK_WEATHER_LOCATION = "San Jose, CA"
$env:DESK_DECK_INSIDE_TEMP_OFFSET_F = "0"
$env:DESK_DECK_AGENT_DONE_HOLD_SECONDS = "5"
$env:DESK_DECK_AGENT_ACTIVE_TTL_SECONDS = "300"
```

`AGENT / DONE` remains visible for 5 seconds, then the display falls back to the default weather screen. `AGENT / WORKING` and `AGENT / WAITING` stay active until reset, changed, or the active-state TTL expires.

## Spotify MVP

Spotify support uses the Spotify Web API to show the currently playing track. It is disabled automatically when no Spotify client ID or token is configured.

1. Create a Spotify app at <https://developer.spotify.com/dashboard>.
2. Add this redirect URI to the Spotify app:

```text
http://127.0.0.1:8888/callback
```

3. Copy the local environment template and fill in the Spotify values:

```powershell
Copy-Item .\local-env.example.ps1 .\secrets\local-env.ps1
notepad .\secrets\local-env.ps1
```

The `companion/secrets/local-env.ps1` file is ignored by Git and is loaded by the repo-local startup script.

Equivalent environment variables:

```powershell
$env:DESK_DECK_SPOTIFY_CLIENT_ID = "your_spotify_client_id"
$env:DESK_DECK_SPOTIFY_CLIENT_SECRET = "your_spotify_client_secret"
$env:DESK_DECK_SPOTIFY_REDIRECT_URI = "http://127.0.0.1:8888/callback"
$env:DESK_DECK_SPOTIFY_TOKEN = "secrets/spotify/token.json"
```

4. Start the companion server and call:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/spotify/status
```

On first use, a browser login opens and creates the ignored token file under `companion/secrets/spotify/`.

Spotify display rules:

- Manual modes, Calendar, and active agent states override Spotify.
- Playing Spotify rotates with weather and time above debug inputs.
- Paused or inactive Spotify falls back to weather.
- Row 1 shows the full track title and scrolls on the firmware when needed.
- Row 2 shows the full first artist and scrolls on the firmware when needed.
- Title and artist text is normalized to LCD-safe ASCII before display.
- Backlight is green, using RGB `0, 210, 12` on the firmware.
- Fitting Spotify text shows for 4 seconds, then weather shows for 5 seconds, then time shows for 4 seconds.
- Long Spotify text scrolls once to the final frame at 400 ms per frame, includes a one-screen completion buffer, holds the final frame for 2 seconds by default, includes a 2-second display sync buffer, then rotates to weather.
- Song changes briefly interrupt manual, Calendar, and active agent statuses for 5 seconds.
- Song-change interrupts inherit the interrupted status backlight color, then return to normal priority.
- Starting `AGENT / WORKING` or `AGENT / WAITING` resets the Spotify baseline, so stale Spotify state does not immediately interrupt the agent screen; later track changes still interrupt briefly.

Optional rotation environment variables:

```powershell
$env:DESK_DECK_SPOTIFY_HOLD_SECONDS = "4"
$env:DESK_DECK_WEATHER_HOLD_SECONDS = "5"
$env:DESK_DECK_TIME_HOLD_SECONDS = "4"
$env:DESK_DECK_SPOTIFY_SCROLL_END_HOLD_SECONDS = "2"
$env:DESK_DECK_SPOTIFY_SCROLL_DISPLAY_SYNC_SECONDS = "2"
$env:DESK_DECK_SPOTIFY_INTERRUPT_SECONDS = "5"
```

## Run

```powershell
.\scripts\start-companion.ps1
```

Run this command from the repository root. It loads `companion/secrets/local-env.ps1` when present, then starts Uvicorn from the companion directory.

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
Invoke-RestMethod http://127.0.0.1:8000/api/calendar/status
Invoke-RestMethod http://127.0.0.1:8000/api/spotify/status
Invoke-RestMethod http://127.0.0.1:8000/api/status/modes
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/status/mode/meeting
```

Available modes:

```text
online        DESK DECK / ONLINE / green
idle          IDLE / READY / green
meeting_soon  MEETING / IN 5 / yellow
meeting       IN A MEETING / BUSY / red
music         NOW PLAYING / TEST TRACK / green
notify        SERVER TEST / NOTICE / purple
spotify_paused PAUSED / TEST TRACK / green
```

Manual modes override debug inputs until reset.

## Agent Status Light

Agent status is a high-priority override for local coding-agent state. It wins over manual modes and debug inputs until reset. Active `working` and `waiting` states also expire after `DESK_DECK_AGENT_ACTIVE_TTL_SECONDS`, defaulting to 300 seconds, so the display recovers if an agent run exits without clearing its state.

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

The debug input endpoints simulate notification and Spotify integrations without firmware changes. The fallback debug priority order is:

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
