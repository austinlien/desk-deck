# Test Plan

## Display Bring-Up Acceptance Criteria

The milestone is complete when:

- Firmware builds in PlatformIO from a fresh clone.
- Firmware still builds after the module split.
- Firmware uploads to the ESP32-C3 over USB.
- Serial Monitor at `115200` baud shows startup logs.
- I2C scan reports `0x2D`, `0x3E`, `0x68`, and `0x70`.
- LCD backlight turns on and changes to the configured color.
- LCD shows:

```text
DESK DECK
HARDWARE OK
```

## Wi-Fi MVP Acceptance Criteria

- Firmware builds in PlatformIO with local `firmware/src/secrets.h` present.
- Companion server runs locally on Windows with FastAPI.
- ESP32 connects to Wi-Fi and logs its IP address.
- ESP32 polls `GET /api/status`.
- LCD shows:

```text
DESK DECK
ONLINE
```

- Stopping the companion server causes the LCD to show `SERVER` / `OFFLINE`.
- Restarting the server recovers on the next poll without reflashing or rebooting.

## Configurable Status Modes Acceptance Criteria

- `GET /api/status` defaults to `DESK DECK` / `ONLINE` / `green`.
- `GET /api/status/modes` lists `online`, `idle`, `meeting_soon`, `meeting`, `music`, `notify`, and `spotify_paused`.
- `POST /api/status/mode/meeting` changes the active status to `IN A MEETING` / `BUSY` / `red`.
- Invalid mode names return HTTP 404.
- ESP32 LCD updates on the next poll without firmware changes.

## Status Engine Skeleton Acceptance Criteria

- `POST /api/debug/reset` returns default `DESK DECK` / `ONLINE` / `green`.
- `active_meeting=true` returns `IN A MEETING` / `BUSY` / `red`.
- `meeting_soon=true` wins over `active_meeting=true`.
- `spotify_playing=true` is ignored while a meeting input is active.
- Manual mode override wins over fake inputs until reset.

## Agent Status Light Acceptance Criteria

- `POST /api/agent/status/working` returns `AGENT` / `WORKING` / `yellow`.
- `POST /api/agent/status/waiting` returns `AGENT` / `WAITING` / `red`.
- `POST /api/agent/status/done` returns `AGENT` / `DONE` / `green`.
- Agent status overrides manual mode and debug inputs.
- Invalid agent states return HTTP 404.
- `POST /api/agent/reset` restores the normal status engine.

## Google Calendar MVP Acceptance Criteria

- Companion starts without Calendar credentials and still returns default `/api/status`.
- Google OAuth credentials and token files live under ignored `companion/secrets/`.
- `GET /api/calendar/status` reports whether Calendar is configured and available.
- Declined, all-day, and free events are ignored.
- Accepted or owned busy timed events count as meetings.
- A meeting 10 to 5 minutes away returns `MEETING` / `SOON` / `yellow` / `solid`.
- A meeting 5 minutes away returns `MEETING` / `SOON` / `red` / `solid`.
- A started meeting returns `MEETING` / `NOW` / `red` / `solid`.
- Calendar status overrides agent status, then agent status resumes when the meeting state clears.
- Manual modes override Calendar status.
- Firmware builds and treats missing `effect` as solid.

## Default Weather Screen Acceptance Criteria

- `POST /api/sensors/inside` accepts `{"temperature_f": 68}` and updates companion weather state.
- `GET /api/weather/status` returns chip temperature, outside weather, humidity, and composed display status.
- With no manual mode, Calendar state, active `working`/`waiting` agent status, or debug input, `/api/status` returns compact weather text.
- `AGENT` / `DONE` remains visible for 5 seconds, then falls back to weather.
- `AGENT` / `WORKING` and `AGENT` / `WAITING` remain visible until reset or changed.
- Outside weather comes from San Jose, CA by default and uses cached values if refresh fails.
- Firmware posts chip temperature once per minute without blocking status polling.

## Spotify MVP Acceptance Criteria

- `GET /api/spotify/status` reports whether Spotify is configured and available.
- Playing Spotify returns full track title, full first artist, green backlight, and scroll effect.
- Spotify title and artist text with accents or typographic punctuation is normalized to LCD-safe ASCII.
- Firmware scrolls Spotify rows longer than 16 characters every 400 ms with brief start/end pauses.
- Playing Spotify rotates with the compact weather screen when no higher-priority state is active.
- Fitting Spotify text holds for the configured Spotify duration, then weather holds for the configured weather duration.
- Long Spotify text uses `scroll_once`, reaches the final frame, includes a completion buffer, holds for 2-3 seconds plus a display sync buffer, then rotates to weather.
- Spotify song changes briefly interrupt manual, Calendar, and active agent statuses.
- Starting active agent `working` and `waiting` statuses resets the Spotify baseline so stale Spotify state does not immediately interrupt the agent screen.
- Song-change interrupts inherit the interrupted status backlight color, then return to normal priority.
- The first observed Spotify track after startup is only a baseline and does not interrupt higher-priority status.
- Paused, inactive, non-track, or unavailable Spotify falls back to the next status source.
- Manual mode, Calendar, and active agent states override Spotify.
- Spotify/weather rotation overrides debug inputs when Spotify is active.
- Spotify credentials and tokens are kept out of Git under `companion/secrets/spotify/`.

## Test Procedure

1. Install the PlatformIO VS Code extension.
2. Open this repository in VS Code.
3. Wire the LCD according to `docs/hardware.md`, using `5V` for LCD VCC.
4. Build the firmware.
5. Upload the firmware.
6. Open Serial Monitor at `115200`.
7. Record discovered I2C addresses in `status.md`.
8. Confirm LCD text and backlight.

## Wi-Fi MVP Procedure

1. Copy `firmware/src/secrets.example.h` to `firmware/src/secrets.h`.
2. Set `WIFI_SSID`, `WIFI_PASSWORD`, and `STATUS_SERVER_URL`.
3. Start the companion server:

```powershell
cd companion
python3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

4. Build and upload firmware.
5. Open Serial Monitor at `115200`.
6. Confirm Wi-Fi connected log and LCD server status.
7. Stop the server and confirm `SERVER` / `OFFLINE`.
8. Restart the server and confirm recovery.

## Configurable Status Modes Procedure

With the companion server running:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/status
Invoke-RestMethod http://127.0.0.1:8000/api/status/modes
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/status/mode/meeting
Invoke-RestMethod http://127.0.0.1:8000/api/status
```

## Agent Status Light Procedure

```powershell
.\scripts\agent-working.ps1
Invoke-RestMethod http://127.0.0.1:8000/api/status

.\scripts\agent-waiting.ps1
Invoke-RestMethod http://127.0.0.1:8000/api/status

.\scripts\agent-done.ps1
Invoke-RestMethod http://127.0.0.1:8000/api/status

.\scripts\agent-reset.ps1
Invoke-RestMethod http://127.0.0.1:8000/api/status
```

Equivalent direct API calls:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/agent/status/working
Invoke-RestMethod http://127.0.0.1:8000/api/status

Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/agent/status/waiting
Invoke-RestMethod http://127.0.0.1:8000/api/status

Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/agent/status/done
Invoke-RestMethod http://127.0.0.1:8000/api/status

Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/agent/reset
```

Confirm the ESP32 LCD shows the selected mode on the next poll.

## Status Engine Skeleton Procedure

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/debug/reset

Invoke-RestMethod `
  -Method Post `
  -ContentType "application/json" `
  -Uri http://127.0.0.1:8000/api/debug/inputs `
  -Body '{"active_meeting":true,"spotify_playing":true}'

Invoke-RestMethod http://127.0.0.1:8000/api/status

Invoke-RestMethod `
  -Method Post `
  -ContentType "application/json" `
  -Uri http://127.0.0.1:8000/api/debug/inputs `
  -Body '{"meeting_soon":true,"active_meeting":true}'

Invoke-RestMethod http://127.0.0.1:8000/api/status
```

## Google Calendar MVP Procedure

With the Python 3.11 venv active:

```powershell
cd companion
.\.venv311\Scripts\python.exe -m pytest
```

With Google OAuth files present:

```powershell
.\.venv311\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Invoke-RestMethod http://127.0.0.1:8000/api/calendar/status
Invoke-RestMethod http://127.0.0.1:8000/api/status
```

Create a short accepted busy Calendar event and confirm the ESP32 shows `MEETING` / `SOON`, first yellow, then red, then `MEETING` / `NOW` after the start time.

## Default Weather Screen Procedure

With the companion server running:

```powershell
Invoke-RestMethod `
  -Method Post `
  -ContentType "application/json" `
  -Uri http://127.0.0.1:8000/api/sensors/inside `
  -Body '{"temperature_f":68}'

Invoke-RestMethod http://127.0.0.1:8000/api/weather/status
Invoke-RestMethod http://127.0.0.1:8000/api/status
```

Confirm `/api/status` shows:

```text
CHIP 68F
OUT <temp>F <humidity>%
```

Upload firmware and confirm Serial logs show periodic chip temperature POST results.

## Spotify MVP Procedure

Configure a Spotify app with redirect URI:

```text
http://127.0.0.1:8888/callback
```

Start the companion server with:

```powershell
$env:DESK_DECK_SPOTIFY_CLIENT_ID = "your_spotify_client_id"
$env:DESK_DECK_SPOTIFY_CLIENT_SECRET = "your_spotify_client_secret"
$env:DESK_DECK_SPOTIFY_REDIRECT_URI = "http://127.0.0.1:8888/callback"
$env:DESK_DECK_SPOTIFY_TOKEN = "secrets/spotify/token.json"
.\.venv311\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Then:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/spotify/status
Invoke-RestMethod http://127.0.0.1:8000/api/status
```

Play a Spotify track and confirm the LCD shows the track title and artist in green, then rotates to weather. Confirm rows longer than 16 characters scroll once to the final frame, hold briefly, then rotate to weather. While a manual, Calendar, or agent status is active, skip to a new song and confirm the new title appears briefly using the interrupted status color, then returns. Pause playback and confirm the display falls back to weather or the next active higher-priority state.

## Refactor Regression Checks

- `main.cpp` should contain high-level setup flow only.
- Pin, address, text, and timing values should live in `config.h`.
- I2C scanning should live in `i2c_scan.*`.
- LCD-specific initialization and display writes should live in `lcd_display.*`.
- Runtime behavior should match the original working display bring-up.

## Troubleshooting

If no I2C devices are found:

- Check LCD power and ground.
- Check SDA/SCL orientation.
- Confirm the board is the Rust-1 variant.

If onboard I2C devices appear but the LCD does not:

- Check the DFRobot connector pin order.
- Confirm the LCD is powered.
- Try a shorter cable.
- Fully remove USB power for 5 seconds and retry after reconnecting.

If text appears but RGB backlight control fails:

- Confirm the RGB controller address.
- Try RGB address `0x60`, `0x6B`, or `0x2D` based on the LCD hardware version.

If Serial Monitor is blank:

- Confirm baud rate is `115200`.
- Reopen the monitor after upload.
- Test with and without USB CDC build flags if needed.
