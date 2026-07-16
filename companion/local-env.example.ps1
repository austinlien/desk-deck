# Copy this file to companion/secrets/local-env.ps1 and fill in local values.
# Files under companion/secrets/ are ignored by Git.

$env:DESK_DECK_SPOTIFY_CLIENT_ID = "your_spotify_client_id"
$env:DESK_DECK_SPOTIFY_CLIENT_SECRET = "your_spotify_client_secret"
$env:DESK_DECK_SPOTIFY_REDIRECT_URI = "http://127.0.0.1:8888/callback"
$env:DESK_DECK_SPOTIFY_TOKEN = "secrets/spotify/token.json"

# Optional display timing.
$env:DESK_DECK_SPOTIFY_HOLD_SECONDS = "4"
$env:DESK_DECK_WEATHER_HOLD_SECONDS = "5"
$env:DESK_DECK_TIME_HOLD_SECONDS = "4"
$env:DESK_DECK_SPOTIFY_SCROLL_END_HOLD_SECONDS = "1"
$env:DESK_DECK_SPOTIFY_SCROLL_DISPLAY_SYNC_SECONDS = "0"
$env:DESK_DECK_SPOTIFY_INTERRUPT_SECONDS = "5"

# Optional Calendar and weather overrides.
$env:DESK_DECK_CALENDAR_ENABLED = "1"
$env:DESK_DECK_GOOGLE_CALENDAR_ID = "primary"
$env:DESK_DECK_GOOGLE_CREDENTIALS = "secrets/credentials.json"
$env:DESK_DECK_GOOGLE_TOKEN = "secrets/token.json"
$env:DESK_DECK_WEATHER_LOCATION = "San Jose, CA"
$env:DESK_DECK_INSIDE_TEMP_OFFSET_F = "0"
