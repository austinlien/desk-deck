# Decisions

## 2026-07-15: Use PlatformIO With Arduino Framework

Use PlatformIO in VS Code with the Arduino framework for the firmware.

Reasoning:

- Keeps build settings in the repository.
- Easier for another person to clone and build.
- Simpler than ESP-IDF for the first display milestone.
- Allows use of the maintained DFRobot Arduino LCD library.

## 2026-07-15: Use ESP32-C3-DevKitM-1 PlatformIO Target

Use `esp32-c3-devkitm-1` as the PlatformIO board target.

Reasoning:

- PlatformIO has this ESP32-C3 devkit target available.
- The project can override pins in source code for the ESP32-C3-DevKit-RUST-1 hardware.

## 2026-07-15: Use Rust-1 I2C Pins

Use:

```text
SDA = GPIO10
SCL = GPIO8
```

Reasoning:

- This matches the ESP32-C3-DevKit-RUST-1 board documentation.
- Pin assignments are centralized in firmware constants.

## 2026-07-15: Use DFRobot Arduino LCD Library First

Use `dfrobot/DFRobot_RGBLCD1602` for display bring-up.

Reasoning:

- Rewriting the driver for ESP-IDF was useful for a class assignment, but is unnecessary for this project milestone.
- The maintained Arduino library reduces risk and keeps attention on project behavior.

## 2026-07-15: Modularize Firmware Before Wi-Fi

Split the working display bring-up sketch into small firmware modules before adding networking.

Reasoning:

- Keeps `main.cpp` focused on the boot sequence.
- Centralizes pins, addresses, and timing constants before more features depend on them.
- Makes the next Wi-Fi milestone easier to add without mixing network, display, and hardware scan logic.

## 2026-07-15: Use Ignored Firmware Secrets Header

Use `firmware/src/secrets.h` for local Wi-Fi credentials and server URL, with `firmware/src/secrets.example.h` committed as the template.

Reasoning:

- Keeps private Wi-Fi credentials out of GitHub.
- Keeps first embedded-network setup simple in PlatformIO.
- Avoids adding a runtime provisioning workflow before the network path is proven.

## 2026-07-15: Add FastAPI Test Server Before Real Integrations

Add a minimal local FastAPI server that returns fixed display JSON.

Reasoning:

- Proves the intended ESP32-to-PC architecture before Calendar or Spotify complexity.
- Gives the firmware a stable local API to poll.
- Keeps the ESP32 display logic simple: it renders the server's chosen state.

## 2026-07-16: Use Local OAuth For Google Calendar MVP

Use Google Calendar read-only OAuth in the Windows companion app, with ignored local OAuth files under `companion/secrets/`.

Reasoning:

- Keeps Calendar access local to the user's machine.
- Avoids committing secrets or adding hosted auth infrastructure.
- Preserves the existing ESP32 polling contract.

## 2026-07-16: Keep Calendar Display Private

Show `MEETING` / `SOON` for Calendar-derived statuses instead of event titles.

Reasoning:

- The LCD is visible on a desk.
- The first real integration only needs availability signal, not event detail.
- The companion can still make richer decisions later without firmware changes.

## 2026-07-16: Add Optional Firmware Display Effects

Extend `/api/status` responses with an optional `effect` field, starting with `solid` and `flash`.

Reasoning:

- The ESP32 polls the companion every 5 seconds, which is too slow for a visible flash.
- Firmware-side flashing keeps the display effect smooth while preserving the existing text/color API.
- Older companion responses remain valid because missing `effect` defaults to solid.

## 2026-07-16: Keep Weather Composition In The Companion

Use the ESP32 to post its internal chip temperature reading, while the companion fetches outside weather from wttr.in and composes the default LCD text.

Reasoning:

- Keeps display priority and text formatting in one place.
- Avoids adding internet weather parsing to firmware.
- Matches the existing architecture where the ESP32 renders `/api/status`.

## 2026-07-16: Use Compact ASCII Weather Text

Use `CHIP 68F` and `OUT 74F 45%` for the default weather screen.

Reasoning:

- Fits reliably on the 16x2 LCD.
- Avoids LCD character-set issues with degree symbols.
- Labels the ESP32 reading as chip temperature instead of room temperature.
- Shows outside humidity only because current hardware has no indoor humidity sensor.

## 2026-07-16: Keep Spotify In The Companion

Use the Spotify Web API from the Windows companion and continue serving selected text through `/api/status`.

Reasoning:

- Avoids adding OAuth and internet API parsing to firmware.
- Reuses the existing status priority engine.
- Lets paused or unavailable Spotify fail open to weather/default behavior.
