# Test Plan

## Display Bring-Up Acceptance Criteria

The milestone is complete when:

- Firmware builds in PlatformIO from a fresh clone.
- Firmware still builds after the module split.
- Firmware uploads to the ESP32-C3 over USB.
- Serial Monitor at `115200` baud shows startup logs.
- I2C scan reports `0x2D`, `0x3E`, `0x68`, and `0x70`.
- LCD backlight turns on and changes to the configured color.
- LCD shows:

```text
DESK DECK
HARDWARE OK
```

## Wi-Fi MVP Acceptance Criteria

- Firmware builds in PlatformIO with local `firmware/src/secrets.h` present.
- Companion server runs locally on Windows with FastAPI.
- ESP32 connects to Wi-Fi and logs its IP address.
- ESP32 polls `GET /api/status`.
- LCD shows:

```text
DESK DECK
ONLINE
```

- Stopping the companion server causes the LCD to show `SERVER` / `OFFLINE`.
- Restarting the server recovers on the next poll without reflashing or rebooting.

## Configurable Status Modes Acceptance Criteria

- `GET /api/status` defaults to `DESK DECK` / `ONLINE` / `green`.
- `GET /api/status/modes` lists `online`, `idle`, `meeting_soon`, `meeting`, `music`, `notify`, and `spotify_paused`.
- `POST /api/status/mode/meeting` changes the active status to `IN A MEETING` / `BUSY` / `red`.
- Invalid mode names return HTTP 404.
- ESP32 LCD updates on the next poll without firmware changes.

## Status Engine Skeleton Acceptance Criteria

- `POST /api/debug/reset` returns default `DESK DECK` / `ONLINE` / `green`.
- `active_meeting=true` returns `IN A MEETING` / `BUSY` / `red`.
- `meeting_soon=true` wins over `active_meeting=true`.
- `spotify_playing=true` is ignored while a meeting input is active.
- Manual mode override wins over fake inputs until reset.

## Test Procedure

1. Install the PlatformIO VS Code extension.
2. Open this repository in VS Code.
3. Wire the LCD according to `docs/hardware.md`, using `5V` for LCD VCC.
4. Build the firmware.
5. Upload the firmware.
6. Open Serial Monitor at `115200`.
7. Record discovered I2C addresses in `status.md`.
8. Confirm LCD text and backlight.

## Wi-Fi MVP Procedure

1. Copy `firmware/src/secrets.example.h` to `firmware/src/secrets.h`.
2. Set `WIFI_SSID`, `WIFI_PASSWORD`, and `STATUS_SERVER_URL`.
3. Start the companion server:

```powershell
cd companion
python3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

4. Build and upload firmware.
5. Open Serial Monitor at `115200`.
6. Confirm Wi-Fi connected log and LCD server status.
7. Stop the server and confirm `SERVER` / `OFFLINE`.
8. Restart the server and confirm recovery.

## Configurable Status Modes Procedure

With the companion server running:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/status
Invoke-RestMethod http://127.0.0.1:8000/api/status/modes
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/status/mode/meeting
Invoke-RestMethod http://127.0.0.1:8000/api/status
```

Confirm the ESP32 LCD shows the selected mode on the next poll.

## Status Engine Skeleton Procedure

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/debug/reset

Invoke-RestMethod `
  -Method Post `
  -ContentType "application/json" `
  -Uri http://127.0.0.1:8000/api/debug/inputs `
  -Body '{"active_meeting":true,"spotify_playing":true}'

Invoke-RestMethod http://127.0.0.1:8000/api/status

Invoke-RestMethod `
  -Method Post `
  -ContentType "application/json" `
  -Uri http://127.0.0.1:8000/api/debug/inputs `
  -Body '{"meeting_soon":true,"active_meeting":true}'

Invoke-RestMethod http://127.0.0.1:8000/api/status
```

## Refactor Regression Checks

- `main.cpp` should contain high-level setup flow only.
- Pin, address, text, and timing values should live in `config.h`.
- I2C scanning should live in `i2c_scan.*`.
- LCD-specific initialization and display writes should live in `lcd_display.*`.
- Runtime behavior should match the original working display bring-up.

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
