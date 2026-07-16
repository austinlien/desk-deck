# Desk Deck Status

## Current Milestone

Display bring-up: show static text on the DFRobot 16x2 RGB LCD from the ESP32-C3.

## What Changed

- Created the initial repository structure.
- Added PlatformIO firmware configuration for an ESP32-C3 Arduino project.
- Added firmware that initializes I2C, scans for devices, initializes the LCD, sets the RGB backlight, and prints the bring-up message.
- Added project documentation for design, hardware, decisions, and testing.
- Updated firmware to call `Wire.setPins(GPIO10, GPIO8)` before `Wire.begin()` so the DFRobot LCD library keeps the Rust-1 I2C pins when it initializes.
- Updated firmware to wait longer after power-up, initialize the LCD before the I2C scan, use a white backlight, and write the bring-up message three times for more reliable LCD startup.

## What Works

- Repo scaffold is ready for the first hardware test.
- Firmware source is written for the display bring-up milestone.
- PlatformIO build and upload succeeded from VS Code.
- Serial Monitor confirmed I2C devices at `0x2D`, `0x3E`, `0x68`, and `0x70` after the latest upload.
- Firmware logs `LCD message written.` after initializing the display.
- LCD text was visible once when powered from `5V`.
- LCD now displays `DESK DECK` and `HARDWARE OK` when powered from `5V`.

## Blocked / Unknown

- PlatformIO is not currently installed on this computer's PATH.
- LCD did not display text reliably at `3V3`.
- Using `5V` for LCD VCC may expose ESP32-C3 I2C pins to 5 V unless the LCD module provides level shifting.

## Validation

- Confirmed expected project files were created.
- Attempted `platformio run` from `firmware/`; command failed because PlatformIO is not installed on PATH.
- User built and uploaded through VS Code PlatformIO successfully.
- Serial Monitor showed LCD text address `0x3E` and RGB address `0x2D`, matching the firmware assumptions.
- Latest attached PlatformIO output confirms a clean build, successful upload to `COM5`, successful reset, and I2C detection of the LCD.
- Local validation with `C:\Users\Austin\.platformio\penv\Scripts\platformio.exe run` completed successfully.

## Next Steps

1. Push the display bring-up milestone to GitHub.
2. Confirm the LCD module's I2C electrical design before long-term 5 V use.
3. Next firmware milestone: split LCD/I2C behavior into small modules before adding Wi-Fi.
