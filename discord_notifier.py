import json
import urllib.request
from config import Ship


def notify(webhooks: list[str], ship: Ship, timestamp: str) -> None:
    if not webhooks:
        return
    line = f"{ship.name} {ship.ship_type}".strip()
    payload = json.dumps({"content": line}).encode()

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
