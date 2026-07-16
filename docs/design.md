# Design

## Current Architecture

The current project stage is a display-only firmware bring-up.

```text
ESP32-C3 firmware
  -> I2C scan over Serial
  -> DFRobot RGB LCD initialization
  -> static two-line LCD message
```

There is no network code, companion app, calendar integration, Spotify integration, or local LLM integration in this milestone.

## Firmware Responsibilities

- Configure the ESP32-C3 I2C pins.
- Detect I2C devices for hardware validation.
- Initialize the LCD.
- Set the RGB backlight.
- Display `DESK DECK` and `HARDWARE OK`.
- Log bring-up information over Serial.

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
