# Desk Deck Status

## Current Milestone

Agent status light bridge: expose local companion endpoints for agent working, waiting, and done states.

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

## Blocked / Unknown

- PlatformIO is not currently installed on this computer's PATH.
- LCD did not display text reliably at `3V3`.
- Using `5V` for LCD VCC may expose ESP32-C3 I2C pins to 5 V unless the LCD module provides level shifting.
- Use `python3.11` for the companion FastAPI venv; the default `python` points to a Python 3.14 build that cannot install `pydantic-core` cleanly on this machine.

## Validation

- Confirmed expected project files were created.
- Attempted `platformio run` from `firmware/`; command failed because PlatformIO is not installed on PATH.
- User built and uploaded through VS Code PlatformIO successfully.
- Serial Monitor showed LCD text address `0x3E` and RGB address `0x2D`, matching the firmware assumptions.
- Latest attached PlatformIO output confirms a clean build, successful upload to `COM5`, successful reset, and I2C detection of the LCD.
- Local validation with `C:\Users\Austin\.platformio\penv\Scripts\platformio.exe run` completed successfully.
- Refactor validation with `C:\Users\Austin\.platformio\penv\Scripts\platformio.exe run` completed successfully.
- Refactor upload attempt found `COM5` but failed because the port was busy or locked by another task.
- Refactored firmware uploaded successfully after closing PlatformIO/serial tasks.
- Monitor command was attempted after upload but did not capture startup output before the command timeout.
- User confirmed the LCD still displays `DESK DECK` and `HARDWARE OK` after the refactor upload.
- Firmware Wi-Fi MVP build completed successfully with PlatformIO.
- Companion dependencies installed successfully in a CPython 3.11 venv.
- Companion status function returned `{'line1': 'DESK DECK', 'line2': 'ONLINE', 'backlight': 'green'}`.
- Companion FastAPI server responded locally at `http://127.0.0.1:8000/api/status` with `{"line1":"DESK DECK","line2":"ONLINE","backlight":"green"}`.
- Wi-Fi MVP firmware uploaded successfully to the ESP32 after stopping lingering PlatformIO processes.
- Serial monitor command was attempted after upload but did not capture output before timeout.
- User confirmed the LCD reached `DESK DECK` / `ONLINE`.
- Updated Wi-Fi connected LCD screen to avoid displaying the ESP32 IP address; IP remains in Serial logs.
- No-IP display tweak uploaded successfully to the ESP32.
- Companion endpoint was rechecked locally and returned `DESK DECK` / `ONLINE`.
- Companion status mode validation passed with FastAPI `TestClient`.
- Live companion server was restarted with the mode endpoints.
- `GET /api/status/modes` lists all configured modes.
- Invalid mode requests return HTTP 404.
- Live server switched to `meeting` and back to `online`.
- Firmware build still passes; no firmware changes were required for this milestone.
- Status engine validation passed with FastAPI `TestClient`.
- Live companion server was restarted with debug input endpoints.
- Live debug inputs selected `IN A MEETING` / `BUSY` while Spotify was also active, confirming meeting priority.
- Live debug state was reset to default `DESK DECK` / `ONLINE`.
- Agent status bridge validation passed with FastAPI `TestClient`.
- Firmware build still passes; no firmware changes were required for the agent bridge.
- Live companion server was restarted with agent endpoints.
- Live agent endpoints returned `AGENT` / `WORKING`, `AGENT` / `WAITING`, and `AGENT` / `DONE`.
- Invalid agent status requests return HTTP 404.
- Live agent status was reset to default `DESK DECK` / `ONLINE`.

## Next Steps

1. Confirm ESP32 LCD visually updates for working, waiting, and done.
2. Commit and push agent status light bridge.
3. Confirm the LCD module's I2C electrical design before long-term 5 V use.
4. Next milestone: decide whether to wire agent status into a script/hook or move to Google Calendar MVP.
