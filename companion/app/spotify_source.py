from __future__ import annotations

import base64
import json
import os
import secrets
import time
import unicodedata
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

import httpx

from .models import DisplayStatus, SpotifyState, SpotifyTrack

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
CURRENTLY_PLAYING_URL = "https://api.spotify.com/v1/me/player/currently-playing"
SCOPE = "user-read-currently-playing"
DEFAULT_REDIRECT_URI = "http://127.0.0.1:8888/callback"
DEFAULT_TOKEN_PATH = Path("secrets/spotify/token.json")


class SpotifySource:
    def __init__(
        self,
        client_id: str | None,
        client_secret: str | None,
        redirect_uri: str = DEFAULT_REDIRECT_URI,
        token_path: Path = DEFAULT_TOKEN_PATH,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.token_path = token_path

    @classmethod
    def from_environment(cls) -> "SpotifySource | None":
        enabled = os.getenv("DESK_DECK_SPOTIFY_ENABLED", "1").lower() not in {"0", "false", "no"}
        if not enabled:
            return None

        client_id = os.getenv("DESK_DECK_SPOTIFY_CLIENT_ID")
        client_secret = os.getenv("DESK_DECK_SPOTIFY_CLIENT_SECRET")
        redirect_uri = os.getenv("DESK_DECK_SPOTIFY_REDIRECT_URI", DEFAULT_REDIRECT_URI)
        token_path = Path(os.getenv("DESK_DECK_SPOTIFY_TOKEN", DEFAULT_TOKEN_PATH))
        if not client_id and not token_path.exists():
            return None
        return cls(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            token_path=token_path,
        )

    def select_status(self) -> SpotifyState:
        if not self.client_id and not self.token_path.exists():
            return SpotifyState(
                enabled=True,
                configured=False,
                available=False,
                detail="Spotify client ID or token is not configured.",
            )

        try:
            token = self._access_token()
            payload = self._fetch_payload(token)
            if payload is None:
                return SpotifyState(enabled=True, configured=True, available=True)

            if not payload.get("is_playing"):
                return SpotifyState(enabled=True, configured=True, available=True)
            if payload.get("currently_playing_type") != "track":
                return SpotifyState(enabled=True, configured=True, available=True)

            item = payload.get("item") or {}
            artists = item.get("artists") or []
            title = item.get("name") or "Spotify"
            artist = artists[0].get("name") if artists else "Unknown Artist"
            track = SpotifyTrack(title=title, artist=artist, is_playing=True)
            status = DisplayStatus(
                line1=_normalize_line(title),
                line2=_normalize_line(artist),
                backlight="green",
                effect="scroll",
            )
            return SpotifyState(
                enabled=True,
                configured=True,
                available=True,
                track=track,
                status=status,
            )
        except Exception as exc:
            return SpotifyState(
                enabled=True,
                configured=bool(self.client_id or self.token_path.exists()),
                available=False,
                detail=str(exc),
            )

    def _fetch_payload(self, token: str) -> dict[str, Any] | None:
        response = httpx.get(
            CURRENTLY_PLAYING_URL,
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        if response.status_code == 204:
            return None
        response.raise_for_status()
        return response.json()

    def _access_token(self) -> str:
        token = self._load_token()
        if token and token.get("access_token") and token.get("expires_at", 0) > time.time() + 60:
            return str(token["access_token"])

        if token and token.get("refresh_token"):
            refreshed = self._refresh_token(str(token["refresh_token"]))
            self._save_token(refreshed)
            return str(refreshed["access_token"])

        authorized = self._authorize()
        self._save_token(authorized)
        return str(authorized["access_token"])

    def _authorize(self) -> dict[str, Any]:
        if not self.client_id or not self.client_secret:
            raise RuntimeError("Spotify client ID and client secret are required for first login.")

        state = secrets.token_urlsafe(16)
        auth_params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": SCOPE,
            "state": state,
        }
        auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(auth_params)}"
        webbrowser.open(auth_url)

        code = _wait_for_spotify_code(self.redirect_uri, state)
        response = httpx.post(
            TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.redirect_uri,
            },
            headers=self._auth_headers(),
            timeout=10,
        )
        response.raise_for_status()
        return _with_expiry(response.json())

    def _refresh_token(self, refresh_token: str) -> dict[str, Any]:
        if not self.client_id or not self.client_secret:
            raise RuntimeError("Spotify client ID and client secret are required to refresh token.")

        response = httpx.post(
            TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            headers=self._auth_headers(),
            timeout=10,
        )
        response.raise_for_status()
        refreshed = response.json()
        if "refresh_token" not in refreshed:
            refreshed["refresh_token"] = refresh_token
        return _with_expiry(refreshed)

    def _auth_headers(self) -> dict[str, str]:
        raw = f"{self.client_id}:{self.client_secret}".encode("utf-8")
        encoded = base64.b64encode(raw).decode("ascii")
        return {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

    def _load_token(self) -> dict[str, Any] | None:
        if not self.token_path.exists():
            return None
        return json.loads(self.token_path.read_text(encoding="utf-8"))

    def _save_token(self, token: dict[str, Any]) -> None:
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        self.token_path.write_text(json.dumps(token, indent=2), encoding="utf-8")


def _normalize_line(value: str) -> str:
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2026": "...",
        "\u00d7": "x",
        "\u00f8": "o",
        "\u00d8": "O",
        "\u00df": "ss",
        "\u00e6": "ae",
        "\u00c6": "AE",
        "\u0153": "oe",
        "\u0152": "OE",
    }
    normalized = value
    for source, replacement in replacements.items():
        normalized = normalized.replace(source, replacement)

    normalized = unicodedata.normalize("NFKD", normalized)
    ascii_line = normalized.encode("ascii", "ignore").decode("ascii")
    return " ".join(ascii_line.split()).strip()


def _with_expiry(token: dict[str, Any]) -> dict[str, Any]:
    token["expires_at"] = time.time() + int(token.get("expires_in", 3600))
    return token


def _wait_for_spotify_code(redirect_uri: str, expected_state: str) -> str:
    parsed = urllib.parse.urlparse(redirect_uri)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 80
    callback_path = parsed.path or "/"
    result: dict[str, str] = {}

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            request = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(request.query)
            if request.path != callback_path:
                self.send_response(404)
                self.end_headers()
                return

            if params.get("state", [""])[0] != expected_state:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Spotify authorization state mismatch.")
                return

            if "error" in params:
                result["error"] = params["error"][0]
            if "code" in params:
                result["code"] = params["code"][0]

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Spotify authorization complete. You can close this window.")

        def log_message(self, format: str, *args: Any) -> None:
            return

    server = HTTPServer((host, port), CallbackHandler)
    server.timeout = 180
    server.handle_request()
    server.server_close()

    if "error" in result:
        raise RuntimeError(f"Spotify authorization failed: {result['error']}")
    if "code" not in result:
        raise RuntimeError("Spotify authorization timed out.")
    return result["code"]
