# Desk Deck

Desk Deck is a personal embedded desk-status display built around an ESP32-C3 and a 16x2 RGB I2C LCD.

The current milestone is a Wi-Fi desk status display with a local Windows companion server, Google Calendar meeting status, event-driven local Spotify playback, a remote Spotify fallback, and default weather/time screens.

```text
CHIP 68F
OUT 74F 45%
```

Local Spotify track changes reach the companion through Windows media sessions and appear on the LCD's next poll. The companion uses Spotify's Web API only as a slower fallback for playback on another device.

## Current Scope

- ESP32-C3-DevKit-RUST-1 firmware
- DFRobot Gravity I2C 16x2 RGB LCD
- PlatformIO + Arduino framework
- I2C scan over Serial
- Wi-Fi connection
- HTTP polling from a local companion server
- Optional Google Calendar meeting status
- Local Spotify title/artist with song-skip interrupts
- Optional Spotify Web API fallback for remote-device playback
- Default inside/outside weather display
- Default time/date display
- Demo recording cycle for display states
- Personal elapsed-time work stopwatch with `HH:MM:SS` display
- LCD status text and RGB backlight from server JSON

## Repository Layout

```text
firmware/          ESP32-C3 PlatformIO firmware
companion/         Local FastAPI companion server
docs/              Design, hardware, decisions, and testing notes
status.md          Current project status and next steps
```

## Quick Start

1. Install Visual Studio Code.
2. Install the PlatformIO extension.
3. Open this repository folder in VS Code.
4. Wire the LCD as documented in [docs/hardware.md](docs/hardware.md).
5. Copy `firmware/src/secrets.example.h` to `firmware/src/secrets.h` and fill in Wi-Fi/server settings.
6. Run the companion test server from [companion/README.md](companion/README.md).
7. Build and upload the firmware from the PlatformIO sidebar.
8. Open the Serial Monitor at `115200` baud.

Use `python3.11` for the companion server environment. The default `python` on this machine points to a Python 3.14 build that does not currently install FastAPI dependencies cleanly.

## Documentation

- [status.md](status.md): current milestone, progress, blockers, and next steps
- [docs/design.md](docs/design.md): architecture direction
- [docs/hardware.md](docs/hardware.md): board, LCD, wiring, and I2C notes
- [docs/decisions.md](docs/decisions.md): project decisions
- [docs/test-plan.md](docs/test-plan.md): acceptance tests
