import csv
import os
import re
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from config import Ship

FIELDNAMES = ["timestamp", "name", "type", "event"]
DEDUP_COOLDOWN_SECONDS = 120
DEDUP_SIMILARITY = 0.75


class CSVLogger:
    def __init__(self, path: str) -> None:
        self._path = path
        self._file_exists = os.path.isfile(path)
        self._warned = False
        self._recent: dict[str, datetime] = {}

    def log(self, ship: Ship) -> None:
        key = _normalize(ship)
        if self._is_duplicate(key):
            return
        self._recent[key] = datetime.now()
        row = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "name": ship.name,
            "type": ship.ship_type,
            "event": "appeared",
        }
        try:
            with open(self._path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
                if not self._file_exists:
                    writer.writeheader()
                    self._file_exists = True
                writer.writerow(row)
        except PermissionError as e:
            if not self._warned:
                print(f"[warning] Cannot write to {self._path}: {e} — will retry each cycle")
                self._warned = True

    def _is_duplicate(self, key: str) -> bool:
        cutoff = datetime.now() - timedelta(seconds=DEDUP_COOLDOWN_SECONDS)
        self._recent = {k: v for k, v in self._recent.items() if v > cutoff}
        return any(
            SequenceMatcher(None, key, seen).ratio() >= DEDUP_SIMILARITY
            for seen in self._recent
        )

    def close(self) -> None:
        pass


def _normalize(ship: Ship) -> str:
    combined = f"{ship.name} {ship.ship_type}"
    # Strip all bracket content (alliance tags, complete or partial)
    combined = re.sub(r'\s*\[.*', '', combined).strip()
    return combined.lower()
