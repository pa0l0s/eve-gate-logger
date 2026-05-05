from __future__ import annotations
import pytesseract
from PIL import Image
from typing import Optional
import mss
import numpy as np
from config import Region, ColumnMap

HEADER_ROW_HEIGHT = 20
OVERVIEW_DEFAULT_HEIGHT = 500
CONF_THRESHOLD = 50

def find_eve_window_rect() -> Optional[tuple[int, int, int, int]]:
    """Returns (left, top, width, height) of the Eve window, or None."""
    try:
        import win32gui
        def _callback(hwnd, results):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if "EVE" in title:
                    rect = win32gui.GetWindowRect(hwnd)
                    left, top, right, bottom = rect
                    results.append((left, top, right - left, bottom - top))
        results: list[tuple[int, int, int, int]] = []
        win32gui.EnumWindows(_callback, results)
        return results[0] if results else None
    except ImportError:
        return None

def capture_full_window(rect: tuple[int, int, int, int]) -> Image.Image:
    left, top, width, height = rect
    monitor = {"left": left, "top": top, "width": width, "height": height}
    with mss.mss() as sct:
        shot = sct.grab(monitor)
        return Image.fromarray(np.array(shot))

def detect_overview_region() -> Optional[tuple[Region, ColumnMap]]:
    """
    Scan the Eve window for the overview header row.
    Returns (Region, ColumnMap) if found, else None.
    """
    rect = find_eve_window_rect()
    if not rect:
        return None

    win_left, win_top, win_width, win_height = rect
    image = capture_full_window(rect)

    data = pytesseract.image_to_data(
        image.convert("L"),
        config="--psm 6",
        output_type=pytesseract.Output.DICT,
    )

    name_x = name_y = type_x = None
    for i, text in enumerate(data["text"]):
        if int(data["conf"][i]) < CONF_THRESHOLD:
            continue
        if text.strip() == "Name":
            name_x = data["left"][i]
            name_y = data["top"][i]
        if text.strip() == "Type" and name_x is not None:
            if abs(data["top"][i] - name_y) <= 10:
                type_x = data["left"][i]
                break

    if name_x is None or type_x is None:
        return None

    header_bottom = name_y + HEADER_ROW_HEIGHT
    region_y = win_top + header_bottom
    region_height = min(OVERVIEW_DEFAULT_HEIGHT, win_height - header_bottom)
    region = Region(x=win_left, y=region_y, width=win_width, height=region_height)

    col_map = ColumnMap(
        name_start=name_x,
        name_end=type_x - 5,
        type_start=type_x,
        type_end=win_width,
    )

    return region, col_map
