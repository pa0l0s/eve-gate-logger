import csv
import difflib
import json
import os
import re
import sys
import threading
import urllib.request
from typing import NamedTuple

_USER_AGENT = "DiscordBot (https://github.com/pa0l0s/eve-gate-logger, 1.0)"
_ESI_BASE = "https://esi.evetech.net/latest"

_ships: dict[str, int] | None = None       # lowercase name -> type_id
_display: dict[str, str] | None = None     # lowercase name -> display name
_names_lower: list[str] | None = None
_load_lock = threading.Lock()
_refresh_done = False


class ShipMatch(NamedTuple):
    canonical_name: str
    type_id: int
    ocr_variant: str


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def _writable_csv() -> str:
    """Path for the user-side (writable) CSV, next to the exe or source dir."""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "esi_ship_types", "ship_types.csv")


def _bundled_csv() -> str:
    """Path to the CSV bundled inside the PyInstaller archive."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "esi_ship_types", "ship_types.csv")


def _best_csv() -> str:
    w = _writable_csv()
    return w if os.path.exists(w) else _bundled_csv()


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------

def _load() -> None:
    global _ships, _display, _names_lower
    with _load_lock:
        if _ships is not None:
            return
        _ships = {}
        _display = {}
        path = _best_csv()
        try:
            with open(path, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    key = row["type_name"].lower()
                    _ships[key] = int(row["type_id"])
                    _display[key] = row["type_name"]
        except Exception as e:
            print(f"[ship_matcher] Could not load {path}: {e}")
        _names_lower = list(_ships.keys())


# ---------------------------------------------------------------------------
# ESI refresh (runs once in background)
# ---------------------------------------------------------------------------

def _esi_get(path: str) -> object:
    url = f"{_ESI_BASE}{path}?datasource=tranquility&language=en"
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def _esi_post(path: str, payload: list) -> object:
    url = f"{_ESI_BASE}{path}?datasource=tranquility&language=en"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json", "User-Agent": _USER_AGENT},
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def _refresh_from_esi() -> None:
    global _refresh_done
    try:
        category = _esi_get("/universe/categories/6/")
        if category.get("name") != "Ship":
            return

        rows: list[dict] = []
        type_ids: list[int] = []
        for group_id in category["groups"]:
            try:
                group = _esi_get(f"/universe/groups/{group_id}/")
            except Exception:
                continue
            if not group.get("published", False):
                continue
            for tid in group.get("types", []):
                rows.append({"type_id": tid, "type_name": "", "group_id": group["group_id"], "group_name": group["name"]})
                type_ids.append(tid)

        names_by_id: dict[int, str] = {}
        for start in range(0, len(type_ids), 1000):
            batch = type_ids[start:start + 1000]
            try:
                for item in _esi_post("/universe/names/", batch):
                    names_by_id[item["id"]] = item["name"]
            except Exception:
                pass

        for row in rows:
            row["type_name"] = names_by_id.get(row["type_id"], "")

        rows = [r for r in rows if r["type_name"]]
        rows.sort(key=lambda r: (r["group_name"].lower(), r["type_name"].lower()))

        out_path = _writable_csv()
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["type_id", "type_name", "group_id", "group_name"])
            writer.writeheader()
            writer.writerows(rows)

        # Reload in-memory tables from the fresh data
        new_ships: dict[str, int] = {}
        new_display: dict[str, str] = {}
        for row in rows:
            key = row["type_name"].lower()
            new_ships[key] = int(row["type_id"])
            new_display[key] = row["type_name"]

        with _load_lock:
            global _ships, _display, _names_lower
            _ships = new_ships
            _display = new_display
            _names_lower = list(new_ships.keys())

        print(f"[ship_matcher] Updated {len(rows)} ship types from ESI")
    except Exception as e:
        print(f"[ship_matcher] ESI refresh failed, using existing list: {e}")
    finally:
        _refresh_done = True


def _ensure_refresh() -> None:
    global _refresh_done
    if not _refresh_done:
        _refresh_done = True  # prevent second thread even if first hasn't finished
        t = threading.Thread(target=_refresh_from_esi, daemon=True)
        t.start()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def match_ship(name: str, ship_type: str) -> ShipMatch | None:
    """Find a known EVE ship type in OCR text. Returns ShipMatch or None."""
    _load()
    _ensure_refresh()

    with _load_lock:
        ships = _ships
        display = _display
        names = _names_lower

    if not ships or not names:
        return None

    combined = re.sub(r"\[.*?\]", "", f"{name} {ship_type}").strip()
    tokens = combined.split()
    if not tokens:
        return None

    for window in range(min(len(tokens), 3), 0, -1):
        for start in range(len(tokens) - window, -1, -1):
            candidate = " ".join(tokens[start: start + window])
            matches = difflib.get_close_matches(candidate.lower(), names, n=1, cutoff=0.82)
            if matches:
                key = matches[0]
                return ShipMatch(display[key], ships[key], candidate)

    return None
