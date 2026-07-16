# Test Plan

## Display Bring-Up Acceptance Criteria

The milestone is complete when:

- Firmware builds in PlatformIO from a fresh clone.
- Firmware uploads to the ESP32-C3 over USB.
- Serial Monitor at `115200` baud shows startup logs.
- I2C scan reports `0x2D`, `0x3E`, `0x68`, and `0x70`.
- LCD backlight turns on and changes to the configured color.
- LCD shows:

```text
DESK DECK
HARDWARE OK
```

## Test Procedure

1. Install the PlatformIO VS Code extension.
2. Open this repository in VS Code.
3. Wire the LCD according to `docs/hardware.md`, using `5V` for LCD VCC.
4. Build the firmware.
5. Upload the firmware.
6. Open Serial Monitor at `115200`.
7. Record discovered I2C addresses in `status.md`.
8. Confirm LCD text and backlight.

## Troubleshooting

If no I2C devices are found:

- Check LCD power and ground.
- Check SDA/SCL orientation.
- Confirm the board is the Rust-1 variant.

If onboard I2C devices appear but the LCD does not:

- Check the DFRobot connector pin order.
- Confirm the LCD is powered.
- Try a shorter cable.
- Fully remove USB power for 5 seconds and retry after reconnecting.

If text appears but RGB backlight control fails:

- Confirm the RGB controller address.
- Try RGB address `0x60`, `0x6B`, or `0x2D` based on the LCD hardware version.

If Serial Monitor is blank:

- Confirm baud rate is `115200`.
- Reopen the monitor after upload.
- Test with and without USB CDC build flags if needed.
