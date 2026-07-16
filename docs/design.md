# Design

## Current Architecture

The current project stage is a Wi-Fi MVP with a local test server.

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
  -> fixed display JSON
```

There is no Calendar integration, Spotify integration, OAuth, persistent config, or local LLM integration in this milestone.

## Firmware Responsibilities

- Configure the ESP32-C3 I2C pins.
- Detect I2C devices for hardware validation.
- Initialize the LCD.
- Set the RGB backlight.
- Display `DESK DECK` and `HARDWARE OK`.
- Connect to Wi-Fi using local ignored credentials.
- Poll the companion test server for display text.
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
- Spotify OAuth and polling
- Status prioritization
- Text shortening
- Optional local LLM integration
- REST API for the ESP32

## Non-Goals For This Milestone

- Calendar or Spotify integration
- Persistent configuration
- Buttons, sensors, or input controls
- Enclosure work
