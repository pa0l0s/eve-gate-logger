import configparser
from dataclasses import dataclass, field
from typing import Optional, NamedTuple

DEFAULT_INI = "settings.ini"

class Region(NamedTuple):
    x: int
    y: int
    width: int
    height: int

class ColumnMap(NamedTuple):
    name_start: int
    name_end: int
    type_start: int
    type_end: int

class Ship(NamedTuple):
    name: str
    ship_type: str  # raw OCR text from the type column, may include tags


class Contact(NamedTuple):
    pilot_name: str
    ship_type: str           # canonical ship name (or raw type without tags)
    ship_type_id: int | None # type_id for zkillboard ship link, None if unmatched
    tags: list[str]          # uppercase ticker strings e.g. ["SWA", "BUSHI"]

@dataclass
class Config:
    interval_seconds: float = 1.0
    region: Optional[Region] = None
    column_map: Optional[ColumnMap] = None
    csv_path: str = "eve_overview_log.csv"
    webhooks: list[str] = field(default_factory=list)
    telegram_bot_token: str = ""
    telegram_chat_ids: list[str] = field(default_factory=list)
    pause_key: str = "ctrl"
    mouse_pause_on_start: bool = False
    mouse_pause_seconds: float = 3.0
    mouse_pause_toggle_key: str = "scroll_lock"
    mouse_pause_deadzone: int = 4

def ensure_config_exists(path: str = DEFAULT_INI) -> None:
    """Write a default settings.ini with comments if none exists."""
    import os
    if os.path.exists(path):
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write(
            "[scanner]\n"
            "interval_seconds = 1.0\n"
            "\n"
            "[region]\n"
            "; Filled automatically on first run — do not edit manually\n"
            "\n"
            "[output]\n"
            "csv_path = eve_overview_log.csv\n"
            "\n"
            "[discord]\n"
            "; Add one webhook URL per line (indented)\n"
            "webhooks =\n"
            ";    https://discord.com/api/webhooks/YOUR_WEBHOOK_URL\n"
            "\n"
            "[telegram]\n"
            "; Get a bot token from @BotFather, then find your chat_id via getUpdates\n"
            "bot_token =\n"
            "chat_ids =\n"
            ";    123456789\n"
            "\n"
            "[hotkeys]\n"
            "; Hold this key to pause scanning (e.g. ctrl, alt, shift, f9, scroll_lock)\n"
            "pause_key = ctrl\n"
            "; Pause scanning when mouse is moving (true/false)\n"
            "mouse_pause_on_start = false\n"
            "; Seconds after last mouse move before scanning resumes\n"
            "mouse_pause_seconds = 3\n"
            "; Toggle mouse-move-pause on/off with this key\n"
            "mouse_pause_toggle_key = scroll_lock\n"
            "; Minimum mouse movement in pixels to trigger pause (0 = any movement)\n"
            "mouse_pause_deadzone = 4\n"
        )


def load_config(path: str = DEFAULT_INI) -> Config:
    parser = configparser.ConfigParser(inline_comment_prefixes=(";", "#"))
    parser.read(path)

    cfg = Config()
    cfg.interval_seconds = parser.getfloat("scanner", "interval_seconds", fallback=1.0)
    cfg.csv_path = parser.get("output", "csv_path", fallback="eve_overview_log.csv")

    raw_webhooks = parser.get("discord", "webhooks", fallback="")
    cfg.webhooks = [
        u.strip() for u in raw_webhooks.replace(",", "\n").splitlines()
        if u.strip().startswith("https://discord.com/api/webhooks/")
    ]

    cfg.telegram_bot_token = parser.get("telegram", "bot_token", fallback="").strip()
    raw_chat_ids = parser.get("telegram", "chat_ids", fallback="")
    cfg.telegram_chat_ids = [
        c.strip() for c in raw_chat_ids.replace(",", "\n").splitlines()
        if c.strip()
    ]

    cfg.pause_key = parser.get("hotkeys", "pause_key", fallback="ctrl").strip()
    cfg.mouse_pause_on_start = parser.getboolean("hotkeys", "mouse_pause_on_start", fallback=False)
    cfg.mouse_pause_seconds = parser.getfloat("hotkeys", "mouse_pause_seconds", fallback=3.0)
    cfg.mouse_pause_toggle_key = parser.get("hotkeys", "mouse_pause_toggle_key", fallback="scroll_lock").strip()
    cfg.mouse_pause_deadzone = parser.getint("hotkeys", "mouse_pause_deadzone", fallback=0)

    x = parser.get("region", "x", fallback="").strip()
    y = parser.get("region", "y", fallback="").strip()
    w = parser.get("region", "width", fallback="").strip()
    h = parser.get("region", "height", fallback="").strip()

    if x and y and w and h:
        cfg.region = Region(int(x), int(y), int(w), int(h))

    ns = parser.get("region", "name_col_start", fallback="").strip()
    ne = parser.get("region", "name_col_end", fallback="").strip()
    ts = parser.get("region", "type_col_start", fallback="").strip()
    te = parser.get("region", "type_col_end", fallback="").strip()

    if ns and ne and ts and te:
        cfg.column_map = ColumnMap(int(ns), int(ne), int(ts), int(te))

    return cfg

def save_config(cfg: Config, path: str = DEFAULT_INI) -> None:
    parser = configparser.ConfigParser()
    parser.read(path)

    if "scanner" not in parser:
        parser["scanner"] = {}
    if "region" not in parser:
        parser["region"] = {}
    if "output" not in parser:
        parser["output"] = {}
    if "discord" not in parser:
        parser["discord"] = {}

    parser["scanner"]["interval_seconds"] = str(cfg.interval_seconds)
    parser["output"]["csv_path"] = cfg.csv_path
    parser["discord"]["webhooks"] = "\n    ".join(cfg.webhooks)

    if cfg.region:
        parser["region"]["x"] = str(cfg.region.x)
        parser["region"]["y"] = str(cfg.region.y)
        parser["region"]["width"] = str(cfg.region.width)
        parser["region"]["height"] = str(cfg.region.height)
    else:
        for key in ("x", "y", "width", "height"):
            parser["region"][key] = ""

    if cfg.column_map:
        parser["region"]["name_col_start"] = str(cfg.column_map.name_start)
        parser["region"]["name_col_end"] = str(cfg.column_map.name_end)
        parser["region"]["type_col_start"] = str(cfg.column_map.type_start)
        parser["region"]["type_col_end"] = str(cfg.column_map.type_end)
    else:
        for key in ("name_col_start", "name_col_end", "type_col_start", "type_col_end"):
            parser["region"][key] = ""

    with open(path, "w") as f:
        parser.write(f)

def clear_region(path: str = DEFAULT_INI) -> None:
    parser = configparser.ConfigParser()
    parser.read(path)
    if "region" not in parser:
        parser["region"] = {}
    for key in ("x", "y", "width", "height", "name_col_start", "name_col_end", "type_col_start", "type_col_end"):
        parser["region"][key] = ""
    with open(path, "w") as f:
        parser.write(f)
