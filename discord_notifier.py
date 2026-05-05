import json
import re
import threading
import urllib.request
from config import Contact

_USER_AGENT = "DiscordBot (https://github.com/pa0l0s/eve-gate-logger, 1.0)"

# ticker -> zKillboard corp URL (or None), persists for the session
_corp_cache: dict[str, str | None] = {}
_cache_lock = threading.Lock()


def notify(webhooks: list[str], contact: Contact, timestamp: str) -> None:
    if not webhooks:
        return
    t = threading.Thread(target=_send, args=(webhooks, contact, timestamp), daemon=True)
    t.start()


def _send(webhooks: list[str], contact: Contact, timestamp: str) -> None:
    time_str = timestamp[11:16]  # "HH:MM"

    # Resolve each tag to a zKillboard corp link
    tag_parts: list[str] = []
    for tag in contact.tags:
        url = _resolve_corp(tag)
        tag_parts.append(f"[{tag}](<{url}>)" if url else f"[{tag}]")

    # Build ship type part with optional zKillboard ship link
    if contact.ship_type_id:
        ship_part = f"[{contact.ship_type}](<https://zkillboard.com/ship/{contact.ship_type_id}/>)"
    else:
        ship_part = contact.ship_type

    parts = [contact.pilot_name]
    if ship_part:
        parts.append(ship_part)
    parts.extend(tag_parts)
    line = f"`{time_str}` {' '.join(parts)}"
    payload = json.dumps({"content": line}).encode()

    for url in webhooks:
        try:
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json", "User-Agent": _USER_AGENT},
            )
            urllib.request.urlopen(req, timeout=5)
        except Exception as e:
            print(f"[discord] Failed ({url[:40]}...): {e}")


def _resolve_corp(ticker: str) -> str | None:
    with _cache_lock:
        if ticker in _corp_cache:
            return _corp_cache[ticker]

    url = None
    try:
        body = json.dumps([ticker]).encode()
        req = urllib.request.Request(
            "https://esi.evetech.net/latest/universe/ids/?datasource=tranquility&language=en",
            data=body,
            headers={"Content-Type": "application/json", "User-Agent": _USER_AGENT},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        corps = data.get("corporations", [])
        if not corps:
            raise ValueError("no corp")
        corp_id = corps[0]["id"]

        req2 = urllib.request.Request(
            f"https://esi.evetech.net/latest/corporations/{corp_id}/?datasource=tranquility",
            headers={"User-Agent": _USER_AGENT},
        )
        with urllib.request.urlopen(req2, timeout=5) as resp:
            corp_data = json.loads(resp.read())
        if corp_data.get("ticker", "").upper() == ticker:
            url = f"https://zkillboard.com/corporation/{corp_id}/"
    except Exception:
        pass

    with _cache_lock:
        _corp_cache[ticker] = url
    return url
