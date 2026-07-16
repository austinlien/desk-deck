# Desk Deck Firmware

This firmware brings up the ESP32-C3 and DFRobot RGB LCD.

## Tooling

- Visual Studio Code
- PlatformIO extension
- Arduino framework for ESP32

## Build

Open the repository in VS Code and use the PlatformIO sidebar:

- Build
- Upload
- Monitor

Serial monitor speed is `115200`.

## Hardware

```text
LCD VCC -> ESP32 3V3
LCD GND -> ESP32 GND
LCD SDA -> GPIO10 / SDA
LCD SCL -> GPIO8 / SCL
```

## Expected Display

```text
DESK DECK
HARDWARE OK
```
