# Desk Deck

Desk Deck is a compact ambient-status display built with an ESP32-C3, a 16x2 RGB LCD, and a local Windows companion service. It turns live desktop context—music, meetings, coding-agent activity, weather, and time—into a glanceable physical interface.

```text
MR BRIGHTSIDE
THE KILLERS
```

## What It Demonstrates

- **End-to-end embedded development:** C++ firmware connects over Wi-Fi, polls the companion API, reports sensor data, and handles reconnect/offline states.
- **Responsive Spotify integration:** Windows media-session events provide local track changes without API polling; updates reach the LCD on its next one-second poll. Spotify's Web API is an optional fallback for playback on other devices.
- **A deterministic context engine:** The FastAPI companion prioritizes meetings, agent/work sessions, song changes, and default content while preserving interrupted state.
- **Purpose-built display behavior:** The firmware renders RGB status colors, flashing alerts, and synchronized one-pass scrolling for text longer than 16 characters.
- **Privacy-conscious integrations:** Calendar events become simple `MEETING / SOON` or `MEETING / NOW` states; event titles never reach the display.

## Architecture

```text
Windows media sessions ─┐
Google Calendar         ├─> FastAPI companion ──HTTP/JSON──> ESP32-C3 ──I2C──> RGB LCD
Weather + chip temp     │        status engine
Codex/work hooks        ┘
```

The companion owns external integrations and display priority. The ESP32 stays focused on connectivity, sensor reporting, and reliable rendering.

## Current State

The hardware and companion are working together over the local network. Confirmed behaviors include:

- Live local Spotify title and artist display, including track-skip interrupts and long-text scrolling
- Spotify, temperature, and time/date rotation
- Calendar meeting warnings and flashing active-meeting state
- Global Codex `WORKING` / `DONE` status hooks and a personal work stopwatch
- Successful firmware build/upload and live ESP32-to-companion communication
- 58 passing companion tests covering source selection, timing, filtering, priority, and overrides

## Tech Stack

- **Firmware:** C++, Arduino, PlatformIO, ESP32-C3, I2C
- **Companion:** Python 3.11, FastAPI, Pydantic, WinRT, pytest
- **Integrations:** Windows Global System Media Transport Controls, Google Calendar API, Spotify Web API, wttr.in
- **Automation:** PowerShell scripts and Codex lifecycle hooks

## Run It

1. Create the companion environment and install dependencies:

   ```powershell
   cd companion
   python3.11 -m venv .venv311
   .\.venv311\Scripts\Activate.ps1
   pip install -r requirements.txt
   cd ..
   ```

2. Start the companion from the repository root:

   ```powershell
   .\scripts\start-companion.ps1
   ```

3. Copy `firmware/src/secrets.example.h` to `firmware/src/secrets.h`, add Wi-Fi details and the companion's LAN URL, then build and upload with PlatformIO.

Local Windows Spotify playback works without Spotify credentials. Calendar OAuth and remote-device Spotify fallback are optional; see [companion/README.md](companion/README.md) for setup details and [firmware/README.md](firmware/README.md) for hardware wiring.

## Repository Guide

```text
firmware/          ESP32-C3 firmware and PlatformIO configuration
companion/         FastAPI service, integrations, and automated tests
scripts/           Startup, demo, work-session, and agent-status helpers
docs/              Architecture, hardware, decisions, and test plan
```

For a quick walkthrough, run `scripts/demo-cycle.ps1` while the companion and display are active. It cycles through the main notification, meeting, agent, music, weather, and time states.
