# Desk Deck Status

## Current Milestone

Spotify MVP: show currently playing Spotify track from the Windows companion, scrolling long title/artist rows on the ESP32 LCD.

## What Changed

- Created the initial repository structure.
- Added PlatformIO firmware configuration for an ESP32-C3 Arduino project.
- Added firmware that initializes I2C, scans for devices, initializes the LCD, sets the RGB backlight, and prints the bring-up message.
- Added project documentation for design, hardware, decisions, and testing.
- Updated firmware to call `Wire.setPins(GPIO10, GPIO8)` before `Wire.begin()` so the DFRobot LCD library keeps the Rust-1 I2C pins when it initializes.
- Updated firmware to wait longer after power-up, initialize the LCD before the I2C scan, use a white backlight, and write the bring-up message three times for more reliable LCD startup.
- Split firmware into `config.h`, `i2c_scan.*`, `lcd_display.*`, and a smaller `main.cpp`.
- Updated design, decisions, and test-plan docs for the module layout.
- Added ignored `firmware/src/secrets.h` and committed `firmware/src/secrets.example.h`.
- Added Wi-Fi manager, HTTP status client, display state, and named backlight color mapping.
- Added a minimal FastAPI companion test server at `companion/app/main.py`.
- Updated docs for Wi-Fi MVP setup and testing.
- Added in-memory companion status modes and mode-switching endpoints.
- Documented the future AI-agent red/yellow/green status-light idea.
- Added fake debug inputs and deterministic companion-side priority selection.
- Added debug endpoints for reading inputs, updating inputs, and resetting state.
- Added agent status bridge endpoints for `working`, `waiting`, and `done`.
- Added repo-local PowerShell scripts for setting agent `working`, `waiting`, `done`, and reset states.
- Added root `AGENTS.md` instructions for using the status scripts during Codex work.
- Refactored the companion into models, status engine, and Google Calendar source modules.
- Added optional Google Calendar read-only OAuth support using ignored files under `companion/secrets/`.
- Added privacy-preserving Calendar meeting states: yellow `MEETING` / `SOON` at 10 minutes, red `MEETING` / `SOON` at 5 minutes, and solid red `MEETING` / `NOW` after meeting start.
- Updated Calendar priority so meeting states interrupt agent status, then the previous agent status resumes when Calendar clears.
- Added a default weather screen with ESP32 chip temperature and San Jose outside weather.
- Added `POST /api/sensors/inside` and `GET /api/weather/status` to the companion.
- Added firmware-side chip temperature posting once per minute using `temperatureRead()`.
- Added `AGENT / DONE` 5-second hold before falling back to weather.
- Added optional Spotify currently-playing source in the companion.
- Added `GET /api/spotify/status` for Spotify debugging.
- Added Spotify status priority below Calendar and active agent states, above debug/weather.
- Extended `/api/status` responses with optional `effect`, defaulting to `solid`.
- Added firmware-side flash support so the LCD backlight can blink locally between HTTP polls.
- Updated Spotify status to send the full track title and first artist with `effect: scroll`.
- Added firmware-side scrolling for rows longer than 16 characters at 500 ms per frame with brief pauses.
- Lowered firmware status polling from 5 seconds to 1 second so Spotify song skips update more quickly.
- Added a short Google Calendar event cache/backoff so faster ESP32 polling does not call Calendar on every `/api/status` request.
- Added companion tests for Calendar timing, event filtering, and override priority.
- Updated README and docs for Calendar setup, behavior, and validation.
- Added companion-side Spotify/weather rotation with configurable Spotify, weather, and scroll-end hold durations.
- Added firmware-side `scroll_once` support for long Spotify rows that should stop on the final frame before rotation.
- Changed Spotify display statuses to use green instead of blue and tuned firmware green to RGB `0, 210, 12`.
- Added `scripts/start-companion.ps1` and `companion/local-env.example.ps1` so local Spotify credentials can be stored once in ignored `companion/secrets/local-env.ps1`.
- Added Spotify song-skip interrupts over manual, Calendar, and active agent statuses with inherited backlight color.
- Tested temporary LCD green comparison modes and selected RGB `0, 210, 12` as the canonical firmware green.
- Added a companion-side active agent status TTL so stale `working` and `waiting` states expire automatically.
- Normalized Spotify title and artist text to LCD-safe ASCII and changed long-text Spotify rotation to wait until the final scroll frame, hold for 2 seconds, then rotate to weather.
- Added a one-screen completion buffer to long Spotify scroll timing so the companion keeps serving the song long enough for the ESP-rendered LCD scroll to reach the final characters before weather rotation.
- Added a 4-second time/date screen to the default rotation, so the cycle is Spotify, temps, then time when Spotify is active, or temps then time when Spotify is inactive.

## What Works

- Repo scaffold is ready for the first hardware test.
- Firmware source is written for the display bring-up milestone.
- PlatformIO build and upload succeeded from VS Code.
- Serial Monitor confirmed I2C devices at `0x2D`, `0x3E`, `0x68`, and `0x70` after the latest upload.
- Firmware logs `LCD message written.` after initializing the display.
- LCD text was visible once when powered from `5V`.
- LCD now displays `DESK DECK` and `HARDWARE OK` when powered from `5V`.
- Refactored firmware builds successfully with PlatformIO.
- Companion test server source is present and returns `/api/status` JSON.
- Companion server can switch local test modes without firmware changes.
- Companion server can select status from fake meeting, notification, and Spotify inputs.
- Companion server can expose explicit agent status lights without firmware changes.
- Agent status scripts can be used by Codex or the user without typing direct API calls.
- Companion server can optionally derive status from Google Calendar without showing event titles.
- Calendar status takes priority over agent status while preserving the agent state for later resume.
- Companion can show `CHIP 68F` / `OUT 74F 45%` as the default status.
- Firmware can post chip temperature readings to the companion without a new local secret.
- Companion can show full Spotify track title and artist with green backlight when playback is active.
- Firmware can render solid, flashing backlight, and scrolling text effects from companion JSON.
- Companion can rotate active Spotify playback with the default weather screen.
- Firmware can render one-pass scrolling text with `effect: scroll_once`.
- Companion can briefly show a newly skipped-to Spotify song over higher-priority statuses, then return to normal priority.
- Firmware uses RGB `0, 210, 12` for the canonical `green` backlight.
- Active agent `working` and `waiting` states self-clear after `DESK_DECK_AGENT_ACTIVE_TTL_SECONDS`, defaulting to 300 seconds.
- Spotify display text avoids unsupported LCD characters and long rows reach the final scroll frame, hold briefly, then rotate to weather.
- Default low-priority display rotates weather with a time/date screen.

## Blocked / Unknown

- PlatformIO is not currently installed on this computer's PATH.
- LCD did not display text reliably at `3V3`.
- Using `5V` for LCD VCC may expose ESP32-C3 I2C pins to 5 V unless the LCD module provides level shifting.
- Use `python3.11` for the companion FastAPI venv; the default `python` points to a Python 3.14 build that cannot install `pydantic-core` cleanly on this machine.
- Google Calendar live validation still requires local OAuth credentials in `companion/secrets/credentials.json`.

## TBD

- Explore a current-time secondary display mode.
  - Consider showing current time alongside another useful context value, such as elapsed time in a game/session.
  - Define the source of the secondary value, priority rules, and LCD layout before implementation.
  - Resolve this TBD after the use case is clarified and either implemented or intentionally deferred.

## Validation

- Companion regression passed with `.\.venv311\Scripts\python.exe -m pytest`: 41 tests passed.
- Firmware build passed with `C:\Users\Austin\.platformio\penv\Scripts\platformio.exe run`.
- Firmware upload to `COM5` succeeded with `C:\Users\Austin\.platformio\penv\Scripts\platformio.exe run -t upload --upload-port COM5`.
- Live companion was restarted with `.\scripts\start-companion.ps1 -RestartExisting`.
- Live API smoke tests confirmed `/api/status`, `/api/spotify/status`, `/api/agent/status`, and `/api/status/modes` respond locally.
- Live `agent-working` baseline stayed on `AGENT` / `WORKING`; a later Spotify skip was manually confirmed to interrupt briefly and then return.
- User confirmed the final Spotify scrolling, skip interrupt, and agent behavior looked good on the LCD.
- Follow-up long-scroll completion buffer companion regression passed with `.\.venv311\Scripts\python.exe -m pytest`: 41 tests passed.
- Follow-up long-scroll completion buffer firmware regression passed with `C:\Users\Austin\.platformio\penv\Scripts\platformio.exe run`; live companion was restarted.
- Reduced Spotify final-frame hold from 3 seconds to 2 seconds; companion regression and firmware regression passed, and the live companion was restarted.
- Default time screen companion regression passed with `.\.venv311\Scripts\python.exe -m pytest`: 42 tests passed.
- Default time screen firmware regression passed with `C:\Users\Austin\.platformio\penv\Scripts\platformio.exe run`; live companion was restarted and sampled rotating temps, time/date, and Spotify.

## Next Steps

1. Create a Spotify app and configure `http://127.0.0.1:8888/callback` as a redirect URI.
2. Copy `companion/local-env.example.ps1` to ignored `companion/secrets/local-env.ps1` and fill in Spotify client ID/secret.
3. Start the companion from the repo root with `.\scripts\start-companion.ps1`.
4. Complete the browser login from `GET /api/spotify/status`.
5. Play a track and confirm the LCD shows title and artist in green.
6. Confirm the LCD module's I2C electrical design before long-term 5 V use.
