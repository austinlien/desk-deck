# Desk Deck Companion Test Server

This is the first local test server for Desk Deck. It returns fixed display JSON so the ESP32 can prove Wi-Fi and HTTP polling before Calendar or Spotify are added.

## Setup

```powershell
cd companion
python3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Find the Windows computer's LAN IP with:

```powershell
ipconfig
```

Then set `STATUS_SERVER_URL` in `firmware/src/secrets.h`, for example:

```cpp
constexpr const char* STATUS_SERVER_URL = "http://192.168.1.100:8000/api/status";
```
