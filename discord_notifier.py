import json
import urllib.request
from config import Ship

EMBED_COLOR = 0xE84855  # red-ish, visible in dark Discord theme


def notify(webhooks: list[str], ship: Ship, timestamp: str) -> None:
    if not webhooks:
        return
    payload = json.dumps({
        "embeds": [{
            "title": "Gate Contact",
            "color": EMBED_COLOR,
            "fields": [
                {"name": "Pilot", "value": ship.name, "inline": True},
                {"name": "Ship",  "value": ship.ship_type, "inline": True},
            ],
            "timestamp": timestamp,
        }]
    }).encode()

    for url in webhooks:
        try:
            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "DiscordBot (https://github.com/pa0l0s/eve-gate-logger, 1.0)",
                },
            )
            urllib.request.urlopen(req, timeout=5)
        except Exception as e:
            print(f"[discord] Failed ({url[:40]}...): {e}")
