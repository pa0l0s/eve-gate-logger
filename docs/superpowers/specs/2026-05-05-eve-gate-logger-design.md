# Eve Gate Logger — Design Spec

**Date:** 2026-05-05  
**Status:** Approved

---

## Overview

A Windows desktop app that monitors the Eve Online in-game overview panel and logs ships as they appear. Captures only the **Name** and **Type** columns. Ships are logged on first appearance and again only if they leave and reappear. Output is a plain CSV file.

---

## Architecture

Single Python project, packaged to a standalone `.exe` via PyInstaller.

```
eve-gate-logger/
├── main.py              # entry point, scan loop
├── capture.py           # screen region capture (mss)
├── ocr.py               # Tesseract OCR + column parser
├── auto_detect.py       # finds Eve window + overview region automatically
├── region_selector.py   # tkinter drag-to-select overlay (manual override)
├── tracker.py           # in-memory dict of currently visible ships
├── logger.py            # CSV writer
├── config.py            # reads/writes settings.ini
├── settings.ini         # user config (lives next to .exe, not inside bundle)
└── build.spec           # PyInstaller spec
```

Each module has one responsibility. Only `tracker.py` holds mutable state.

---

## Data Flow

```
App start
  └─ Load settings.ini
  └─ If no region saved → auto_detect()
       └─ If auto-detect fails → launch region_selector (drag overlay)
  └─ Open/create CSV file

Every N seconds (default: 1, configurable):
  └─ capture.py      → screenshot of saved region only (small, fast)
  └─ ocr.py          → Tesseract reads image → parse Name + Type columns
  └─ tracker.py      → diff result against current tracked set:
       • In result, NOT in tracked  → log "appeared" + add to set
       • In tracked, NOT in result  → remove from set (ship left overview)
       • In result AND in tracked   → skip (already logged this visit)
  └─ logger.py       → append row to CSV
```

Tracker key: `(name, type)` tuple — handles pilots with similar names on different ship types.

---

## CSV Output Format

```
timestamp,name,type,event
2026-05-05 14:32:01,Angry Pirate,Rifter,appeared
2026-05-05 14:32:04,Space Trucker,Badger,appeared
2026-05-05 14:33:10,Angry Pirate,Rifter,appeared
```

`event` is always `appeared` (both first appearance and reappearance after absence).

---

## Auto-detect

1. Use `pywin32` to locate the Eve Online window by title (`"EVE"`)
2. Capture the full Eve window once at startup
3. Scan horizontal 20px strips top-to-bottom with Tesseract, looking for the overview header row containing `"Name"` and `"Type"` in the same strip
4. Set scan region to the area below the header row within the panel
5. Save region to `settings.ini` — auto-detect only runs once per session

**Failure handling:** if auto-detect fails (overview not open, non-standard layout), block startup and launch the region selector.

---

## Region Selector

A semi-transparent tkinter fullscreen overlay. The user clicks and drags a rectangle over the overview panel. On confirm, the region is saved to `settings.ini`.

Triggered by:
- Auto-detect failure at startup
- `--setup` command-line flag (manual re-calibration)
- `--reset` flag (clears saved region, re-runs auto-detect)

---

## Configuration (`settings.ini`)

Lives next to `eve-gate-logger.exe`, editable with any text editor.

```ini
[scanner]
interval_seconds = 1

[region]
x =
y =
width =
height =

[output]
csv_path = eve_overview_log.csv
```

Empty `x/y/width/height` triggers auto-detect on next launch.

---

## CLI Interface

```
eve-gate-logger.exe           # normal run
eve-gate-logger.exe --setup   # force region selector open
eve-gate-logger.exe --reset   # clear saved region, re-run auto-detect
```

---

## Error Handling

| Situation | Behavior |
|---|---|
| Eve window not found | Print warning, retry next interval |
| Tesseract returns empty/garbled text | Skip cycle silently |
| CSV file locked (e.g. Excel has it open) | Warn once, retry each cycle |
| No region + auto-detect fails | Block and open region selector |

---

## Packaging

- **PyInstaller `--onefile`** — single `.exe`, no install required on gaming PC
- Tesseract binary + `eng.traineddata` bundled inside the `.exe`
- `settings.ini` placed **next to** the `.exe` (not bundled — must survive restarts)
- Build via `build.bat` run once on Windows, or cross-invoked from WSL2 via a Windows Python install

---

## Dependencies

| Package | Purpose |
|---|---|
| `mss` | Fast screen region capture (Win32 GDI) |
| `pytesseract` | Python wrapper for Tesseract OCR |
| `Pillow` | Image manipulation (crop, convert for OCR) |
| `pywin32` | Find Eve window by title |
| `tkinter` | Region selector overlay (stdlib) |
| `configparser` | settings.ini read/write (stdlib) |

---

## Out of Scope

- Ollama / LLM-based vision (Tesseract is sufficient for Eve's clean grid UI)
- System tray icon / GUI (can be added later)
- SQLite or remote logging
- Reading Eve process memory (against ToS)
