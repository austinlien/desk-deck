# Desk Deck

Desk Deck is a personal embedded desk-status display built around an ESP32-C3 and a 16x2 RGB I2C LCD.

The current milestone is intentionally small: bring up the LCD hardware and display a fixed two-line message.

```text
DESK DECK
HARDWARE OK
```

Future milestones will add Wi-Fi, a local Windows companion app, Google Calendar status, Spotify status, and offline behavior.

## Current Scope

- ESP32-C3-DevKit-RUST-1 firmware
- DFRobot Gravity I2C 16x2 RGB LCD
- PlatformIO + Arduino framework
- I2C scan over Serial
- Static LCD text and RGB backlight

## Repository Layout

```text
firmware/          ESP32-C3 PlatformIO firmware
docs/              Design, hardware, decisions, and testing notes
status.md          Current project status and next steps
```

## Quick Start

1. Install Visual Studio Code.
2. Install the PlatformIO extension.
3. Open this repository folder in VS Code.
4. Wire the LCD as documented in [docs/hardware.md](docs/hardware.md).
5. Build and upload the firmware from the PlatformIO sidebar.
6. Open the Serial Monitor at `115200` baud.

## Documentation

- [status.md](status.md): current milestone, progress, blockers, and next steps
- [docs/design.md](docs/design.md): architecture direction
- [docs/hardware.md](docs/hardware.md): board, LCD, wiring, and I2C notes
- [docs/decisions.md](docs/decisions.md): project decisions
- [docs/test-plan.md](docs/test-plan.md): acceptance tests
