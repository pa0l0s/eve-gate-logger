import argparse
import logging
import os
import sys
import time

import app_logging
app_logging.setup()

import pytesseract

if getattr(sys, "frozen", False):
    pytesseract.pytesseract.tesseract_cmd = os.path.join(sys._MEIPASS, "tesseract.exe")

from config import Config, Region, ColumnMap, load_config, save_config, clear_region, ensure_config_exists, DEFAULT_INI
from capture import capture_region
from ocr import parse_overview_image
from tracker import ShipTracker
from logger import CSVLogger
from auto_detect import detect_overview_region
from region_selector import select_region
from pause_manager import PauseManager

def run_one_cycle(
    region: Region,
    column_map: ColumnMap,
    tracker: ShipTracker,
    logger: CSVLogger,
) -> None:
    image = capture_region(region)
    ships = parse_overview_image(image, column_map)
    for ship in tracker.update(ships):
        logger.log(ship)

def build_components(cfg: Config) -> tuple[Region, ColumnMap, ShipTracker, CSVLogger]:
    region = cfg.region
    column_map = cfg.column_map

    if not region or not column_map:
        print("[eve-gate-logger] No region configured — running auto-detect...")
        detected = detect_overview_region()
        if detected:
            region, column_map = detected
            cfg.region = region
            cfg.column_map = column_map
            save_config(cfg)
            print(f"[eve-gate-logger] Auto-detected region: {region}")
        else:
            print("[eve-gate-logger] Auto-detect failed — please select the overview manually.")
            region = select_region()
            if not region:
                print("[eve-gate-logger] No region selected. Exiting.")
                sys.exit(1)
            column_map = ColumnMap(
                name_start=0,
                name_end=region.width // 2,
                type_start=region.width // 2,
                type_end=region.width,
            )
            cfg.region = region
            cfg.column_map = column_map
            save_config(cfg)

    return region, column_map, ShipTracker(), CSVLogger(
        cfg.csv_path, cfg.webhooks,
        cfg.telegram_bot_token, cfg.telegram_chat_ids,
    )

def main() -> None:
    parser = argparse.ArgumentParser(description="Eve Gate Logger")
    parser.add_argument("--setup", action="store_true", help="Force region selector open")
    parser.add_argument("--reset", action="store_true", help="Clear saved region and re-detect")
    parser.add_argument("--config", default=DEFAULT_INI, help="Path to settings.ini")
    parser.add_argument("--nocsv", action="store_true", help="Disable CSV logging (notifications still sent)")
    args = parser.parse_args()

    ensure_config_exists(args.config)
    cfg = load_config(args.config)

    if args.reset:
        clear_region(args.config)
        cfg = load_config(args.config)
        print("[eve-gate-logger] Region cleared.")

    if args.setup:
        cfg.region = None
        cfg.column_map = None

    if args.nocsv:
        cfg.csv_path = ""

    region, column_map, tracker, logger = build_components(cfg)
    pauser = PauseManager(
        pause_key=cfg.pause_key,
        mouse_pause_on_start=cfg.mouse_pause_on_start,
        mouse_pause_seconds=cfg.mouse_pause_seconds,
        mouse_pause_toggle_key=cfg.mouse_pause_toggle_key,
        mouse_pause_deadzone=cfg.mouse_pause_deadzone,
    )

    dest = cfg.csv_path if cfg.csv_path else "notifications only (--nocsv)"
    print(f"[eve-gate-logger] Scanning every {cfg.interval_seconds}s -> {dest}")
    print(f"[eve-gate-logger] Hold [{cfg.pause_key}] to pause | [{cfg.mouse_pause_toggle_key}] toggles mouse-move pause")
    try:
        while True:
            try:
                if not pauser.is_paused():
                    run_one_cycle(region, column_map, tracker, logger)
            except Exception as e:
                logging.error("[eve-gate-logger] Scan error (will retry): %s", e, exc_info=True)
            time.sleep(cfg.interval_seconds)
    except KeyboardInterrupt:
        print("\n[eve-gate-logger] Stopped.")
        logger.close()

if __name__ == "__main__":
    main()
