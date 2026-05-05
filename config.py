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
    ship_type: str

@dataclass
class Config:
    interval_seconds: float = 1.0
    region: Optional[Region] = None
    column_map: Optional[ColumnMap] = None
    csv_path: str = "eve_overview_log.csv"
    webhooks: list[str] = field(default_factory=list)

def load_config(path: str = DEFAULT_INI) -> Config:
    parser = configparser.ConfigParser()
    parser.read(path)

    cfg = Config()
    cfg.interval_seconds = parser.getfloat("scanner", "interval_seconds", fallback=1.0)
    cfg.csv_path = parser.get("output", "csv_path", fallback="eve_overview_log.csv")

    raw_webhooks = parser.get("discord", "webhooks", fallback="")
    cfg.webhooks = [
        u.strip() for u in raw_webhooks.replace(",", "\n").splitlines()
        if u.strip().startswith("https://discord.com/api/webhooks/")
    ]

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
