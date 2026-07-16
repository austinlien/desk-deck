# Design

## Current Architecture

The current project stage is a Wi-Fi MVP with a local companion server and Google Calendar MVP.

```text
ESP32-C3 firmware
  -> config constants
  -> LCD initialization and message display
  -> I2C scan over Serial
  -> Wi-Fi connection management
  -> HTTP polling from local companion server
  -> high-level boot flow

Windows companion test server
  -> FastAPI
  -> GET /api/status
  -> optional Google Calendar read-only OAuth source
  -> optional Spotify currently-playing OAuth source
  -> default weather screen with ESP32 chip temperature and wttr.in outside weather
  -> agent status override
  -> configurable in-memory status modes
  -> deterministic priority over fake debug inputs
```

There is no persistent config UI or local LLM integration in this milestone.

## Firmware Responsibilities

- Configure the ESP32-C3 I2C pins.
- Detect I2C devices for hardware validation.
- Initialize the LCD.
- Set the RGB backlight.
- Display `DESK DECK` and `HARDWARE OK`.
- Connect to Wi-Fi using local ignored credentials.
- Poll the companion test server for display text.
- Post its internal chip temperature reading to the companion.
- Show clear Wi-Fi/server failure screens.
- Log bring-up information over Serial.

## Firmware Modules

```text
config.h          Pins, LCD constants, startup timing, and bring-up text
display_state.*   Display text and named backlight color mapping
i2c_scan.*        Reusable I2C bus scan and Serial logging
lcd_display.*     LCD initialization and two-line message display
status_client.*   HTTP GET /api/status and JSON parsing
wifi_manager.*    Wi-Fi connect/retry helpers
main.cpp          Boot sequence and high-level orchestration
```

## Future Architecture Direction

Later milestones should keep the ESP32 firmware simple:

- Wi-Fi connection management
- Polling a local Windows companion app
- Displaying server-provided status text
- Clock and offline fallback
- Reconnection behavior

The Windows companion app should eventually own:

- Google Calendar OAuth and polling
- Privacy-preserving calendar status text
- Default weather screen
- Spotify OAuth and polling
- Status prioritization
- Display effects and text animation
- Optional local LLM integration
- REST API for the ESP32

## Current Companion Priority

The companion server selects status in this order:

```text
manual mode override
Google Calendar status
agent override
Spotify currently playing
fake debug inputs
weather default
```

Manual status modes override debug inputs until `/api/debug/reset` is called.
Agent status overrides debug inputs until `/api/agent/reset` or `/api/debug/reset` is called.
Calendar status interrupts agent status, and the stored agent status resumes when no meeting state is active. Calendar status shows only private text. Accepted or owned busy timed events count as meetings; declined, all-day, and free events are ignored. The Calendar states are yellow at 10 minutes, red at 5 minutes, and `MEETING` / `NOW` with solid red after the meeting starts.
Spotify currently playing rotates with compact weather and a clock screen when no higher-priority state is active. Fitting Spotify text shows briefly, then weather shows briefly, then time shows briefly; long Spotify text uses a one-pass scroll effect before weather. Song changes briefly interrupt manual, Calendar, and active agent statuses using the interrupted status backlight color, then normal priority resumes. Paused or inactive Spotify falls back to the next lower-priority source.
When no higher-priority state or active Spotify playback is active, the companion rotates compact weather (`CHIP 68F` and `OUT 74F 45%`) with a time/date screen. Outside weather is fetched by the companion for San Jose, CA; the ESP32 only posts its internal chip temperature and renders `/api/status`.

## Non-Goals For This Milestone

- Persistent configuration
- Buttons, sensors, or input controls
- Enclosure work

## Future Feature Notes

- Automatic Codex lifecycle detection is deferred until there is a reliable signal source. Current agent status is controlled through explicit local API calls.
- `AGENTS.md` and `scripts/agent-*.ps1` provide an instruction-driven workflow for Codex to update the local status light during repository work.
