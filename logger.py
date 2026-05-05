import csv
import os
from datetime import datetime
from config import Ship

FIELDNAMES = ["timestamp", "name", "type", "event"]

class CSVLogger:
    def __init__(self, path: str) -> None:
        self._path = path
        self._file_exists = os.path.isfile(path)
        self._warned = False

    def log(self, ship: Ship) -> None:
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

    def close(self) -> None:
        pass
