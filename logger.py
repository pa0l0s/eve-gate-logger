import csv
import os
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from config import Ship, Contact
from enrich import enrich
import discord_notifier
import telegram_notifier

FIELDNAMES = ["timestamp", "name", "type", "tags", "event"]
DEDUP_COOLDOWN_SECONDS = 120
DEDUP_SIMILARITY = 0.75


class CSVLogger:
    def __init__(
        self,
        path: str,
        webhooks: list[str] | None = None,
        telegram_bot_token: str = "",
        telegram_chat_ids: list[str] | None = None,
    ) -> None:
        self._path = path
        self._webhooks = webhooks or []
        self._telegram_token = telegram_bot_token
        self._telegram_chat_ids = telegram_chat_ids or []
        self._file_exists = os.path.isfile(path)
        self._warned = False
        self._recent: dict[str, datetime] = {}

    def log(self, ship: Ship) -> None:
        contact = enrich(ship)
        key = _normalize(contact)
        if self._is_duplicate(key):
            return
        now = datetime.now()
        self._recent[key] = now
        iso_ts = now.strftime("%Y-%m-%dT%H:%M:%S")
        row = {
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "name": contact.pilot_name,
            "type": contact.ship_type,
            "tags": " ".join(f"[{t}]" for t in contact.tags),
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
        discord_notifier.notify(self._webhooks, contact, iso_ts)
        telegram_notifier.notify(self._telegram_token, self._telegram_chat_ids, contact, iso_ts)

    def _is_duplicate(self, key: str) -> bool:
        cutoff = datetime.now() - timedelta(seconds=DEDUP_COOLDOWN_SECONDS)
        self._recent = {k: v for k, v in self._recent.items() if v > cutoff}
        return any(
            SequenceMatcher(None, key, seen).ratio() >= DEDUP_SIMILARITY
            for seen in self._recent
        )

    def close(self) -> None:
        pass


def _normalize(contact: Contact) -> str:
    return f"{contact.pilot_name} {contact.ship_type}".lower()
