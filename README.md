# EVE Gate Logger

Monitors your EVE Online overview panel using OCR and logs every new contact to a CSV file and Discord.

## Download

**[⬇ Download eve-gate-logger-v1.0.0-windows.zip](https://github.com/pa0l0s/eve-gate-logger/releases/download/v1.0.0/eve-gate-logger-v1.0.0-windows.zip)**

No Python or Tesseract installation required — everything is bundled.

---

## Requirements

- Windows 10 / 11 x64
- EVE Online running with the overview panel visible

---

## Installation

1. Download and extract the zip
2. Place `eve-gate-logger.exe` and `settings.ini` in the same folder
3. Run `eve-gate-logger.exe`

---

## First Run

On the first run the program tries to **auto-detect** the EVE overview region by scanning for the column headers (`Name`, `Type`) in the EVE window.

- If EVE is open with the overview visible → region is detected automatically and saved to `settings.ini`
- If EVE is not open → a **fullscreen overlay** appears; click and drag to select the overview area manually

The saved region is reused on every subsequent run. Use `--reset` to redo detection.

---

## Configuration — settings.ini

```ini
[scanner]
interval_seconds = 1.0        ; how often to scan (seconds)

[region]
; filled automatically after first run — do not edit manually

[output]
csv_path = eve_overview_log.csv   ; path to the output CSV log

[discord]
webhooks =
    https://discord.com/api/webhooks/YOUR_WEBHOOK_URL
    https://discord.com/api/webhooks/SECOND_WEBHOOK_URL
```

Multiple Discord webhooks are supported — add each on its own indented line.

---

## CSV Log

Each new contact is appended to the CSV with the following columns:

| Column | Example |
|--------|---------|
| timestamp | 2026-05-05 23:12:05 |
| name | Koechka Atron |
| type | [.NLC.] [BUSHI] |
| event | appeared |

Duplicate entries caused by OCR noise are suppressed automatically (fuzzy deduplication with a 120-second cooldown window).

---

## Discord Notifications

When a new contact appears a message is posted to each configured webhook:

```
`23:12` Koechka Atron [.NLC.](<https://zkillboard.com/corporation/.../>)[BUSHI](<https://zkillboard.com/corporation/.../>)
```

- Corp and alliance tags are resolved to zKillboard links via the EVE ESI API
- Tags must be 1–5 characters of capital letters, digits, `.`, `-`, or space
- Links are suppressed for tags that cannot be resolved

---

## Command-Line Flags

```
eve-gate-logger.exe [--setup] [--reset] [--config PATH]

  --setup        Force the region selector overlay open
  --reset        Clear the saved region and run auto-detect again
  --config PATH  Use a custom settings.ini (default: settings.ini next to the exe)
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Ships not detected | Run with `--reset` while EVE is open and the overview is visible |
| Wrong column split (ship type in name field) | Run with `--reset` to auto-detect column boundaries |
| Discord 403 error | Check the webhook URL in settings.ini is correct |
| Duplicate entries in CSV | Increase `DEDUP_COOLDOWN_SECONDS` in `logger.py` if needed |

---

## Building from Source

```bash
pip install -r requirements.txt
pyinstaller build.spec --clean
# output: dist/eve-gate-logger.exe
```

Requires Tesseract-OCR installed at `C:\Program Files\Tesseract-OCR\` (edit `TESSERACT_DIR` in `build.spec` if different).
