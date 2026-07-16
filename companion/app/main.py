from fastapi import FastAPI

app = FastAPI(title="Desk Deck Companion Test Server")


@app.get("/api/status")
def get_status() -> dict[str, str]:
    return {
        "line1": "DESK DECK",
        "line2": "ONLINE",
        "backlight": "green",
    }
