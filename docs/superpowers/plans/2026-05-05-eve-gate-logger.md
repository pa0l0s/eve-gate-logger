# Eve Gate Logger Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Windows app that captures the Eve Online overview panel every second, extracts ship Name and Type via Tesseract OCR, and appends new/reappeared ships to a CSV log file.

**Architecture:** Python modules with single responsibilities, wired together in `main.py`. All Windows-specific calls (`pywin32`, `mss`) are isolated in `auto_detect.py` and `capture.py` so the rest of the codebase is testable on Linux/WSL2. Packaged to a single `.exe` via PyInstaller.

**Tech Stack:** Python 3.11+, mss, pytesseract, Pillow, pywin32, tkinter (stdlib), configparser (stdlib), PyInstaller

---

## File Map

| File | Responsibility |
|---|---|
| `config.py` | Shared types (`Ship`, `Region`, `ColumnMap`, `Config`) + `settings.ini` read/write |
| `tracker.py` | In-memory ship deduplication state |
| `logger.py` | CSV file writer |
| `capture.py` | Screen region screenshot via `mss` |
| `ocr.py` | Tesseract OCR + column-aware row parser |
| `auto_detect.py` | Locate Eve window + detect overview header position |
| `region_selector.py` | Tkinter fullscreen drag-to-select overlay |
| `main.py` | CLI args, scan loop, wires all modules together |
| `settings.ini` | Default user config (ships next to `.exe`) |
| `requirements.txt` | Pinned dependencies |
| `build.spec` | PyInstaller bundle spec |
| `build.bat` | One-click Windows build script |
| `tests/test_config.py` | Tests for config.py |
| `tests/test_tracker.py` | Tests for tracker.py |
| `tests/test_logger.py` | Tests for logger.py |
| `tests/test_capture.py` | Tests for capture.py |
| `tests/test_ocr.py` | Tests for ocr.py |
| `tests/test_auto_detect.py` | Tests for auto_detect.py |
| `tests/test_main.py` | Integration tests for main.py scan loop |

---

## Task 1: Project scaffold

**Files:**
- Create: `requirements.txt`
- Create: `settings.ini`
- Create: `tests/__init__.py`
- Create: `.gitignore`

- [ ] **Step 1: Create `requirements.txt`**

```
mss==9.0.2
pytesseract==0.3.13
Pillow==10.3.0
pywin32==306
pyinstaller==6.6.0
pytest==8.2.0
```

- [ ] **Step 2: Create default `settings.ini`**

```ini
[scanner]
interval_seconds = 1

[region]
x =
y =
width =
height =
name_col_start =
name_col_end =
type_col_start =
type_col_end =

[output]
csv_path = eve_overview_log.csv
```

- [ ] **Step 3: Create `tests/__init__.py`** (empty file)

- [ ] **Step 4: Create `.gitignore`**

```
__pycache__/
*.pyc
*.pyo
dist/
build/
*.egg-info/
.pytest_cache/
eve_overview_log.csv
```

- [ ] **Step 5: Install dependencies (on Windows Python, not WSL2)**

```
pip install mss pytesseract Pillow pywin32 pytest
```

Note: `pywin32` only installs on Windows. On WSL2/Linux for dev, install without it:
```bash
pip install mss pytesseract Pillow pytest
```

- [ ] **Step 6: Commit**

```bash
git add requirements.txt settings.ini tests/__init__.py .gitignore
git commit -m "feat: project scaffold"
```

---

## Task 2: config.py — shared types and settings.ini read/write

**Files:**
- Create: `config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_config.py`:

```python
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
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_config.py -v
```

Expected: `ModuleNotFoundError: No module named 'config'`

- [ ] **Step 3: Implement `config.py`**

```python
import configparser
from dataclasses import dataclass
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

def load_config(path: str = DEFAULT_INI) -> Config:
    parser = configparser.ConfigParser()
    parser.read(path)

    cfg = Config()
    cfg.interval_seconds = parser.getfloat("scanner", "interval_seconds", fallback=1.0)
    cfg.csv_path = parser.get("output", "csv_path", fallback="eve_overview_log.csv")

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

    parser["scanner"]["interval_seconds"] = str(cfg.interval_seconds)
    parser["output"]["csv_path"] = cfg.csv_path

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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_config.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add config.py tests/test_config.py
git commit -m "feat: config module with Region, ColumnMap, Ship types and settings.ini read/write"
```

---

## Task 3: tracker.py — ship deduplication

**Files:**
- Create: `tracker.py`
- Create: `tests/test_tracker.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_tracker.py`:

```python
from config import Ship
from tracker import ShipTracker

def test_new_ship_is_returned():
    t = ShipTracker()
    new = t.update({Ship("Angry Pirate", "Rifter")})
    assert Ship("Angry Pirate", "Rifter") in new

def test_same_ship_in_next_scan_is_not_returned():
    t = ShipTracker()
    t.update({Ship("Angry Pirate", "Rifter")})
    new = t.update({Ship("Angry Pirate", "Rifter")})
    assert len(new) == 0

def test_ship_that_left_and_reappears_is_returned():
    t = ShipTracker()
    t.update({Ship("Angry Pirate", "Rifter")})
    t.update(set())                              # ship leaves
    new = t.update({Ship("Angry Pirate", "Rifter")})  # reappears
    assert Ship("Angry Pirate", "Rifter") in new

def test_multiple_ships_tracked_independently():
    t = ShipTracker()
    t.update({Ship("Alpha", "Rifter"), Ship("Beta", "Drake")})
    # Alpha leaves, Beta stays, Gamma arrives
    new = t.update({Ship("Beta", "Drake"), Ship("Gamma", "Merlin")})
    assert Ship("Gamma", "Merlin") in new
    assert Ship("Alpha", "Rifter") not in new
    assert Ship("Beta", "Drake") not in new

def test_same_name_different_type_tracked_separately():
    t = ShipTracker()
    new = t.update({Ship("Pilot", "Rifter"), Ship("Pilot", "Drake")})
    assert len(new) == 2
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_tracker.py -v
```

Expected: `ModuleNotFoundError: No module named 'tracker'`

- [ ] **Step 3: Implement `tracker.py`**

```python
from config import Ship

class ShipTracker:
    def __init__(self) -> None:
        self._visible: set[Ship] = set()

    def update(self, current: set[Ship]) -> set[Ship]:
        """Return ships that are new this scan. Update internal state."""
        new_ships = current - self._visible
        self._visible = current
        return new_ships
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_tracker.py -v
```

Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add tracker.py tests/test_tracker.py
git commit -m "feat: ship tracker with deduplication logic"
```

---

## Task 4: logger.py — CSV writer

**Files:**
- Create: `logger.py`
- Create: `tests/test_logger.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_logger.py`:

```python
import csv
import os
from unittest.mock import patch, mock_open
from datetime import datetime
from config import Ship
from logger import CSVLogger

def test_creates_csv_with_header(tmp_path):
    path = str(tmp_path / "log.csv")
    log = CSVLogger(path)
    log.log(Ship("Angry Pirate", "Rifter"))
    log.close()

    with open(path) as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == ["timestamp", "name", "type", "event"]
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["name"] == "Angry Pirate"
        assert rows[0]["type"] == "Rifter"
        assert rows[0]["event"] == "appeared"

def test_appends_rows_without_duplicate_header(tmp_path):
    path = str(tmp_path / "log.csv")
    log = CSVLogger(path)
    log.log(Ship("Alpha", "Rifter"))
    log.close()

    log2 = CSVLogger(path)
    log2.log(Ship("Beta", "Drake"))
    log2.close()

    with open(path) as f:
        lines = f.readlines()
    # header + 2 data rows = 3 lines (plus possible trailing newline)
    data_lines = [l for l in lines if l.strip() and not l.startswith("timestamp")]
    assert len(data_lines) == 2

def test_permission_error_prints_warning_does_not_crash(tmp_path, capsys):
    path = str(tmp_path / "log.csv")
    log = CSVLogger(path)

    with patch("builtins.open", side_effect=PermissionError("locked")):
        log.log(Ship("Alpha", "Rifter"))

    captured = capsys.readouterr()
    assert "locked" in captured.out.lower() or "permission" in captured.out.lower()
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_logger.py -v
```

Expected: `ModuleNotFoundError: No module named 'logger'`

- [ ] **Step 3: Implement `logger.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_logger.py -v
```

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add logger.py tests/test_logger.py
git commit -m "feat: CSV logger with header, append, and PermissionError handling"
```

---

## Task 5: capture.py — screen region capture

**Files:**
- Create: `capture.py`
- Create: `tests/test_capture.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_capture.py`:

```python
from unittest.mock import patch, MagicMock
import numpy as np
from PIL import Image
from config import Region
from capture import capture_region

def _make_mock_mss():
    mock_sct = MagicMock()
    # mss returns a screenshot object; .pixels is a numpy-compatible array
    fake_screenshot = MagicMock()
    fake_screenshot.__array__ = lambda self, dtype=None: np.zeros((100, 200, 4), dtype=np.uint8)
    mock_sct.__enter__ = MagicMock(return_value=mock_sct)
    mock_sct.__exit__ = MagicMock(return_value=False)
    mock_sct.grab = MagicMock(return_value=fake_screenshot)
    return mock_sct

def test_capture_passes_correct_monitor_dict():
    region = Region(x=10, y=20, width=300, height=150)
    mock_sct = _make_mock_mss()

    with patch("capture.mss.mss", return_value=mock_sct):
        result = capture_region(region)

    mock_sct.grab.assert_called_once_with({
        "left": 10, "top": 20, "width": 300, "height": 150
    })

def test_capture_returns_pil_image():
    region = Region(x=0, y=0, width=50, height=50)
    mock_sct = _make_mock_mss()

    with patch("capture.mss.mss", return_value=mock_sct):
        result = capture_region(region)

    assert isinstance(result, Image.Image)
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_capture.py -v
```

Expected: `ModuleNotFoundError: No module named 'capture'`

- [ ] **Step 3: Implement `capture.py`**

```python
import mss
import numpy as np
from PIL import Image
from config import Region

def capture_region(region: Region) -> Image.Image:
    monitor = {"left": region.x, "top": region.y, "width": region.width, "height": region.height}
    with mss.mss() as sct:
        screenshot = sct.grab(monitor)
        return Image.fromarray(np.array(screenshot))
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_capture.py -v
```

Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add capture.py tests/test_capture.py
git commit -m "feat: screen region capture via mss"
```

---

## Task 6: ocr.py — Tesseract OCR + column-aware parser

**Files:**
- Create: `ocr.py`
- Create: `tests/test_ocr.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_ocr.py`:

```python
from unittest.mock import patch
from PIL import Image
from config import Ship, ColumnMap
from ocr import parse_overview_image, preprocess_image

# Simulates pytesseract.image_to_data output for:
#   Row y≈5:  "Angry"(x=10) "Pirate"(x=55) | "Rifter"(x=130)
#   Row y≈25: "Space"(x=10) "Trucker"(x=55) | "Badger"(x=130)
MOCK_OCR_DATA = {
    "text":  ["Angry", "Pirate", "Rifter", "Space", "Trucker", "Badger"],
    "left":  [10,      55,       130,      10,      55,        130],
    "top":   [5,       5,        5,        25,      25,        25],
    "width": [40,      50,       50,       45,      60,        50],
    "conf":  [90,      90,       90,       90,      90,        90],
}

COLUMN_MAP = ColumnMap(name_start=0, name_end=120, type_start=120, type_end=250)

def test_parse_returns_correct_ships():
    image = Image.new("RGB", (300, 100), color=(30, 30, 30))
    with patch("ocr.pytesseract.image_to_data", return_value=MOCK_OCR_DATA):
        ships = parse_overview_image(image, COLUMN_MAP)
    assert Ship("Angry Pirate", "Rifter") in ships
    assert Ship("Space Trucker", "Badger") in ships

def test_parse_returns_empty_on_no_data():
    empty_data = {"text": [], "left": [], "top": [], "width": [], "conf": []}
    image = Image.new("RGB", (300, 100))
    with patch("ocr.pytesseract.image_to_data", return_value=empty_data):
        ships = parse_overview_image(image, COLUMN_MAP)
    assert ships == set()

def test_parse_skips_low_confidence_words():
    low_conf_data = {
        "text":  ["GarbageGarbage", "Rifter"],
        "left":  [10,               130],
        "top":   [5,                5],
        "width": [80,               50],
        "conf":  [10,               90],   # first word below threshold
    }
    image = Image.new("RGB", (300, 50))
    with patch("ocr.pytesseract.image_to_data", return_value=low_conf_data):
        ships = parse_overview_image(image, COLUMN_MAP)
    assert ships == set()

def test_preprocess_returns_grayscale_image():
    image = Image.new("RGB", (100, 50), color=(30, 30, 30))
    result = preprocess_image(image)
    assert result.mode == "L"
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_ocr.py -v
```

Expected: `ModuleNotFoundError: No module named 'ocr'`

- [ ] **Step 3: Implement `ocr.py`**

```python
import pytesseract
from PIL import Image, ImageOps
from config import Ship, ColumnMap

CONF_THRESHOLD = 50
ROW_TOLERANCE = 8
TESSERACT_CONFIG = "--psm 6"

def preprocess_image(image: Image.Image) -> Image.Image:
    gray = image.convert("L")
    return ImageOps.invert(gray)

def parse_overview_image(image: Image.Image, column_map: ColumnMap) -> set[Ship]:
    processed = preprocess_image(image)
    data = pytesseract.image_to_data(processed, config=TESSERACT_CONFIG, output_type=pytesseract.Output.DICT)
    rows = _group_words_by_row(data)
    ships = set()
    for row in rows:
        name = _extract_column_text(row, column_map.name_start, column_map.name_end)
        ship_type = _extract_column_text(row, column_map.type_start, column_map.type_end)
        if name and ship_type:
            ships.add(Ship(name, ship_type))
    return ships

def _group_words_by_row(data: dict) -> list[list[dict]]:
    words = [
        {"text": t, "x": data["left"][i], "y": data["top"][i]}
        for i, t in enumerate(data["text"])
        if t.strip() and int(data["conf"][i]) >= CONF_THRESHOLD
    ]
    if not words:
        return []
    words.sort(key=lambda w: w["y"])
    rows: list[list[dict]] = []
    current = [words[0]]
    for word in words[1:]:
        if abs(word["y"] - current[0]["y"]) <= ROW_TOLERANCE:
            current.append(word)
        else:
            rows.append(sorted(current, key=lambda w: w["x"]))
            current = [word]
    rows.append(sorted(current, key=lambda w: w["x"]))
    return rows

def _extract_column_text(row: list[dict], col_start: int, col_end: int) -> str:
    return " ".join(w["text"] for w in row if col_start <= w["x"] < col_end).strip()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_ocr.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add ocr.py tests/test_ocr.py
git commit -m "feat: Tesseract OCR with column-aware row parser and image preprocessing"
```

---

## Task 7: auto_detect.py — locate Eve window and overview region

**Files:**
- Create: `auto_detect.py`
- Create: `tests/test_auto_detect.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_auto_detect.py`:

```python
from unittest.mock import patch, MagicMock
from PIL import Image
from config import Region, ColumnMap
from auto_detect import detect_overview_region, find_eve_window_rect

# Header row OCR data: "Name" at x=10, "Type" at x=130, y=50
MOCK_HEADER_DATA = {
    "text":  ["Name", "Type"],
    "left":  [10,     130],
    "top":   [50,     50],
    "width": [40,     40],
    "conf":  [90,     90],
}

MOCK_NO_HEADER_DATA = {
    "text":  ["SomeOtherText"],
    "left":  [10],
    "top":   [10],
    "width": [80],
    "conf":  [90],
}

def _fake_window_rect():
    return (0, 0, 1920, 1080)

def test_detect_finds_region_when_header_present():
    image = Image.new("RGB", (1920, 1080))
    with patch("auto_detect.pytesseract.image_to_data", return_value=MOCK_HEADER_DATA), \
         patch("auto_detect.capture_full_window", return_value=image), \
         patch("auto_detect.find_eve_window_rect", return_value=_fake_window_rect()):
        result = detect_overview_region()

    assert result is not None
    region, col_map = result
    assert region.y > 50            # starts below the header row
    assert col_map.name_start == 10
    assert col_map.type_start == 130

def test_detect_returns_none_when_no_header():
    image = Image.new("RGB", (1920, 1080))
    with patch("auto_detect.pytesseract.image_to_data", return_value=MOCK_NO_HEADER_DATA), \
         patch("auto_detect.capture_full_window", return_value=image), \
         patch("auto_detect.find_eve_window_rect", return_value=_fake_window_rect()):
        result = detect_overview_region()

    assert result is None

def test_detect_returns_none_when_eve_not_found():
    with patch("auto_detect.find_eve_window_rect", return_value=None):
        result = detect_overview_region()

    assert result is None
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_auto_detect.py -v
```

Expected: `ModuleNotFoundError: No module named 'auto_detect'`

- [ ] **Step 3: Implement `auto_detect.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_auto_detect.py -v
```

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add auto_detect.py tests/test_auto_detect.py
git commit -m "feat: auto-detect Eve window and overview header region"
```

---

## Task 8: region_selector.py — tkinter drag-to-select overlay

**Files:**
- Create: `region_selector.py`

Note: tkinter UI cannot be automatically tested. Test manually by running `python region_selector.py` — a semi-transparent red overlay should appear, allow click-drag to select a rectangle, and print the selected region to stdout.

- [ ] **Step 1: Implement `region_selector.py`**

```python
import tkinter as tk
from typing import Optional
from config import Region

def select_region() -> Optional[Region]:
    """
    Opens a fullscreen semi-transparent overlay.
    User clicks and drags to select the overview region.
    Returns the selected Region, or None if cancelled (Escape).
    """
    result: list[Optional[Region]] = [None]

    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.attributes("-alpha", 0.3)
    root.attributes("-topmost", True)
    root.configure(bg="black")
    root.title("Eve Gate Logger — Select Overview Region (Escape to cancel)")

    canvas = tk.Canvas(root, cursor="cross", bg="black", highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)

    start_x = start_y = 0
    rect_id = None

    def on_press(event: tk.Event) -> None:
        nonlocal start_x, start_y, rect_id
        start_x, start_y = event.x, event.y
        if rect_id:
            canvas.delete(rect_id)

    def on_drag(event: tk.Event) -> None:
        nonlocal rect_id
        if rect_id:
            canvas.delete(rect_id)
        rect_id = canvas.create_rectangle(
            start_x, start_y, event.x, event.y,
            outline="red", width=2
        )

    def on_release(event: tk.Event) -> None:
        x1 = min(start_x, event.x)
        y1 = min(start_y, event.y)
        x2 = max(start_x, event.x)
        y2 = max(start_y, event.y)
        if x2 - x1 > 10 and y2 - y1 > 10:
            result[0] = Region(x=x1, y=y1, width=x2 - x1, height=y2 - y1)
        root.destroy()

    def on_escape(event: tk.Event) -> None:
        root.destroy()

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)
    root.bind("<Escape>", on_escape)

    root.mainloop()
    return result[0]

if __name__ == "__main__":
    region = select_region()
    print(f"Selected: {region}")
```

- [ ] **Step 2: Manual test on Windows**

```
python region_selector.py
```

Expected: Black overlay fills screen. Drag a rectangle — it appears in red. Release → prints `Selected: Region(x=..., y=..., width=..., height=...)`. Escape → prints `Selected: None`.

- [ ] **Step 3: Commit**

```bash
git add region_selector.py
git commit -m "feat: tkinter fullscreen drag-to-select region overlay"
```

---

## Task 9: main.py — scan loop and CLI

**Files:**
- Create: `main.py`
- Create: `tests/test_main.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_main.py`:

```python
import time
from unittest.mock import MagicMock, patch, call
from config import Config, Region, ColumnMap, Ship
from main import run_one_cycle, build_components

REGION = Region(x=0, y=0, width=300, height=200)
COL_MAP = ColumnMap(name_start=0, name_end=120, type_start=120, type_end=250)

def test_run_one_cycle_logs_new_ships():
    from tracker import ShipTracker
    from logger import CSVLogger

    tracker = ShipTracker()
    logger = MagicMock(spec=CSVLogger)
    ships = {Ship("Angry Pirate", "Rifter")}

    with patch("main.capture_region", return_value=MagicMock()), \
         patch("main.parse_overview_image", return_value=ships):
        run_one_cycle(REGION, COL_MAP, tracker, logger)

    logger.log.assert_called_once_with(Ship("Angry Pirate", "Rifter"))

def test_run_one_cycle_skips_already_tracked_ships():
    from tracker import ShipTracker
    from logger import CSVLogger

    tracker = ShipTracker()
    logger = MagicMock(spec=CSVLogger)
    ships = {Ship("Angry Pirate", "Rifter")}

    with patch("main.capture_region", return_value=MagicMock()), \
         patch("main.parse_overview_image", return_value=ships):
        run_one_cycle(REGION, COL_MAP, tracker, logger)
        run_one_cycle(REGION, COL_MAP, tracker, logger)

    assert logger.log.call_count == 1

def test_run_one_cycle_handles_ocr_empty_gracefully():
    from tracker import ShipTracker
    from logger import CSVLogger

    tracker = ShipTracker()
    logger = MagicMock(spec=CSVLogger)

    with patch("main.capture_region", return_value=MagicMock()), \
         patch("main.parse_overview_image", return_value=set()):
        run_one_cycle(REGION, COL_MAP, tracker, logger)

    logger.log.assert_not_called()
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_main.py -v
```

Expected: `ModuleNotFoundError: No module named 'main'`

- [ ] **Step 3: Implement `main.py`**

```python
import argparse
import sys
import time

from config import Config, Region, ColumnMap, load_config, save_config, clear_region, DEFAULT_INI
from capture import capture_region
from ocr import parse_overview_image
from tracker import ShipTracker
from logger import CSVLogger
from auto_detect import detect_overview_region
from region_selector import select_region

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
            # Column map unknown after manual selection — use full-width defaults
            column_map = ColumnMap(
                name_start=0,
                name_end=region.width // 2,
                type_start=region.width // 2,
                type_end=region.width,
            )
            cfg.region = region
            cfg.column_map = column_map
            save_config(cfg)

    return region, column_map, ShipTracker(), CSVLogger(cfg.csv_path)

def main() -> None:
    parser = argparse.ArgumentParser(description="Eve Gate Logger")
    parser.add_argument("--setup", action="store_true", help="Force region selector open")
    parser.add_argument("--reset", action="store_true", help="Clear saved region and re-detect")
    parser.add_argument("--config", default=DEFAULT_INI, help="Path to settings.ini")
    args = parser.parse_args()

    cfg = load_config(args.config)

    if args.reset:
        clear_region(args.config)
        cfg = load_config(args.config)
        print("[eve-gate-logger] Region cleared.")

    if args.setup:
        cfg.region = None
        cfg.column_map = None

    region, column_map, tracker, logger = build_components(cfg)

    print(f"[eve-gate-logger] Scanning every {cfg.interval_seconds}s → {cfg.csv_path}")
    try:
        while True:
            try:
                run_one_cycle(region, column_map, tracker, logger)
            except Exception as e:
                print(f"[eve-gate-logger] Scan error (will retry): {e}")
            time.sleep(cfg.interval_seconds)
    except KeyboardInterrupt:
        print("\n[eve-gate-logger] Stopped.")
        logger.close()

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_main.py -v
```

Expected: 3 passed

- [ ] **Step 5: Run the full test suite**

```bash
pytest -v
```

Expected: All tests pass (24 total across all modules)

- [ ] **Step 6: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: main scan loop with CLI args --setup and --reset"
```

---

## Task 10: Packaging — PyInstaller build

**Files:**
- Create: `build.spec`
- Create: `build.bat`

Note: This task must be run on Windows with Python and PyInstaller installed.
Tesseract for Windows must be installed first: https://github.com/UB-Mannheim/tesseract/wiki

- [ ] **Step 1: Find Tesseract install path on Windows**

```
where tesseract
```

Note the path (typically `C:\Program Files\Tesseract-OCR\tesseract.exe`).

- [ ] **Step 2: Create `build.spec`**

Replace `TESSERACT_PATH` with your actual path from Step 1.

```python
# build.spec
import os

TESSERACT_DIR = r"C:\Program Files\Tesseract-OCR"

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[
        (os.path.join(TESSERACT_DIR, "tesseract.exe"), "."),
    ],
    datas=[
        (os.path.join(TESSERACT_DIR, "tessdata", "eng.traineddata"), "tessdata"),
    ],
    hiddenimports=["win32gui", "win32con", "PIL._tkinter_finder"],
    hookspath=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name="eve-gate-logger",
    console=True,
    onefile=True,
)
```

- [ ] **Step 3: Create `build.bat`**

```bat
@echo off
echo Building eve-gate-logger.exe...
pyinstaller build.spec --clean --noconfirm
echo.
echo Copying default settings.ini next to exe...
copy /Y settings.ini dist\settings.ini
echo.
echo Done. Run dist\eve-gate-logger.exe
pause
```

- [ ] **Step 4: Run the build on Windows**

```
build.bat
```

Expected: `dist\eve-gate-logger.exe` created (~30-50 MB), `dist\settings.ini` copied alongside it.

- [ ] **Step 5: Smoke test the exe on Windows with Eve open**

```
cd dist
eve-gate-logger.exe --setup
```

Expected: Region selector overlay appears. Select the overview panel. App starts scanning and prints log lines. Open `eve_overview_log.csv` in Notepad to verify rows are written.

- [ ] **Step 6: Commit**

```bash
git add build.spec build.bat
git commit -m "feat: PyInstaller build spec and Windows build script"
```

---

## Done

All tasks complete when:
- `pytest -v` passes all 17 tests
- `dist\eve-gate-logger.exe` runs on Windows with Eve open
- Ships appear in `eve_overview_log.csv` as pilots enter the overview
