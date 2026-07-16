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
