import configparser
import os
import pytest
from config import Config, Region, ColumnMap, load_config, save_config, clear_region

def test_load_defaults_when_no_file(tmp_path):
    path = tmp_path / "settings.ini"
    cfg = load_config(str(path))
    assert cfg.interval_seconds == 1.0
    assert cfg.region is None
    assert cfg.column_map is None
    assert cfg.csv_path == "eve_overview_log.csv"

def test_round_trip_region(tmp_path):
    path = str(tmp_path / "settings.ini")
    cfg = load_config(path)
    cfg.region = Region(x=10, y=20, width=300, height=400)
    cfg.column_map = ColumnMap(name_start=5, name_end=115, type_start=120, type_end=210)
    save_config(cfg, path)

    loaded = load_config(path)
    assert loaded.region == Region(x=10, y=20, width=300, height=400)
    assert loaded.column_map == ColumnMap(name_start=5, name_end=115, type_start=120, type_end=210)

def test_clear_region(tmp_path):
    path = str(tmp_path / "settings.ini")
    cfg = load_config(path)
    cfg.region = Region(x=10, y=20, width=300, height=400)
    cfg.column_map = ColumnMap(name_start=5, name_end=115, type_start=120, type_end=210)
    save_config(cfg, path)

    clear_region(path)
    loaded = load_config(path)
    assert loaded.region is None
    assert loaded.column_map is None

def test_interval_seconds_saved(tmp_path):
    path = str(tmp_path / "settings.ini")
    cfg = load_config(path)
    cfg.interval_seconds = 2.5
    save_config(cfg, path)
    loaded = load_config(path)
    assert loaded.interval_seconds == 2.5
