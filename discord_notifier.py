import json
import re
import threading
import urllib.request
from config import Ship
import ship_matcher

_USER_AGENT = "DiscordBot (https://github.com/pa0l0s/eve-gate-logger, 1.0)"
_TAG_RE = re.compile(r'\[([A-Z0-9.\- ]{1,5})\]', re.IGNORECASE)

# ticker -> zKillboard URL (or None if not resolvable), persists for the session
_corp_cache: dict[str, str | None] = {}
_cache_lock = threading.Lock()


def notify(webhooks: list[str], ship: Ship, timestamp: str) -> None:
    if not webhooks:
        return
    t = threading.Thread(target=_send, args=(webhooks, ship, timestamp), daemon=True)
    t.start()


def _send(webhooks: list[str], ship: Ship, timestamp: str) -> None:
    time_str = timestamp[11:16]  # "HH:MM" from "YYYY-MM-DDTHH:MM:SS"
    base = f"{ship.name} {ship.ship_type}".strip()

    # Build annotated line: replace each valid [TAG] with [TAG](zkill_url) if resolvable
    tags = _TAG_RE.findall(f"{ship.name} {ship.ship_type}")
    zkill_parts: list[str] = []
    for tag in tags:
        tag_upper = tag.upper()
        url = _resolve_corp(tag_upper)
        if url:
            zkill_parts.append(f"[{tag_upper}](<{url}>)")
        else:
            zkill_parts.append(f"[{tag_upper}]")

    # Rebuild line replacing [TAG] tokens with annotated versions (case-insensitive match)
    annotated = base
    for i, tag in enumerate(tags):
        annotated = re.sub(re.escape(f"[{tag}]"), zkill_parts[i], annotated, count=1, flags=re.IGNORECASE)

    # Try to match a known ship type and hyperlink it
    sm = ship_matcher.match_ship(ship.name, ship.ship_type)
    if sm:
        ship_link = f"[{sm.canonical_name}](<https://zkillboard.com/ship/{sm.type_id}/>)"
        # Replace the OCR variant in the annotated text (case-insensitive)
        annotated = re.sub(re.escape(sm.ocr_variant), ship_link, annotated, count=1, flags=re.IGNORECASE)

    line = f"`{time_str}` {annotated}"
    payload = json.dumps({"content": line}).encode()

    for url in webhooks:
        try:
            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": _USER_AGENT,
                },
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
        # Step 1: resolve ticker → corp ID via ESI
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

        # Step 2: verify the ticker matches
        req2 = urllib.request.Request(
            f"https://esi.evetech.net/latest/corporations/{corp_id}/?datasource=tranquility",
            headers={"User-Agent": _USER_AGENT},
        )
        with urllib.request.urlopen(req2, timeout=5) as resp:
            corp_data = json.loads(resp.read())
        if corp_data.get("ticker", "").upper() == ticker.upper():
            url = f"https://zkillboard.com/corporation/{corp_id}/"
    except Exception:
        pass

    with _cache_lock:
        _corp_cache[ticker] = url
    return url
