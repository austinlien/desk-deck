# Design

## Current Architecture

The current project stage is a modular display-only firmware foundation.

```text
ESP32-C3 firmware
  -> config constants
  -> LCD initialization and message display
  -> I2C scan over Serial
  -> high-level boot flow
```

There is no network code, companion app, calendar integration, Spotify integration, or local LLM integration in this milestone.

## Firmware Responsibilities

- Configure the ESP32-C3 I2C pins.
- Detect I2C devices for hardware validation.
- Initialize the LCD.
- Set the RGB backlight.
- Display `DESK DECK` and `HARDWARE OK`.
- Log bring-up information over Serial.

## Firmware Modules

```text
config.h          Pins, LCD constants, startup timing, and bring-up text
i2c_scan.*        Reusable I2C bus scan and Serial logging
lcd_display.*     LCD initialization and two-line message display
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

- Wi-Fi
- REST API calls
- Calendar or Spotify integration
- Persistent configuration
- Buttons, sensors, or input controls
- Enclosure work
