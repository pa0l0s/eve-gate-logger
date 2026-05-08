# EVE Gate Logger

Monitors your EVE Online overview panel using OCR and logs every new contact to a CSV file and Discord.

## Download

**[⬇ Download eve-gate-logger-v1.2.1-windows.zip](https://github.com/pa0l0s/eve-gate-logger/releases/download/v1.2.1/eve-gate-logger-v1.2.1-windows.zip)**

No Python or Tesseract installation required — everything is bundled.

---

## Requirements

- Windows 10 / 11 x64
- EVE Online running with the overview panel visible
- In-game overview configured to show **ships only**, with at least the following columns in order: **Name**, **Type**, **Corporation**, **Alliance**

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

New to webhooks? See [Intro to Webhooks](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks) on the Discord support site for step-by-step instructions on how to create one.

### Telegram (optional)

```ini
[telegram]
bot_token = 123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
chat_ids =
    -1001234567890
    987654321
```

Multiple chat IDs are supported — add each on its own indented line.

**How to set up a Telegram bot:**

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the prompts — you will receive a **bot token** like `123456789:ABCdef...`
3. Paste the token into `bot_token` in `settings.ini`
4. To find your **chat ID**:
   - For a personal chat: start a conversation with your bot, then open `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` in a browser after sending any message to the bot — look for `"chat":{"id": ...}`
   - For a group or channel: add the bot to the group/channel, send a message, then use the same `getUpdates` URL — the chat ID for groups/channels is a negative number (e.g. `-1001234567890`)
5. Paste the chat ID(s) into `chat_ids` in `settings.ini`

---

## CSV Log

Each new contact is appended to the CSV with the following columns:

| Column | Example |
|--------|---------|
| timestamp | 2026-05-06 00:13:11 |
| name | SumoEnjoyer |
| type | Venture |
| tags | [STI] |
| event | appeared |

Duplicate entries caused by OCR noise are suppressed automatically (fuzzy deduplication with a 120-second cooldown window).

---

## Discord Notifications

When a new contact appears a message is posted to each configured webhook:

```
`00:13` SumoEnjoyer [Venture](<https://zkillboard.com/ship/609/>) [STI](<https://zkillboard.com/corporation/.../>)
```

Message format: `time` · pilot name · ship type · corp/alliance tags

- Ship type is matched against all EVE ship types and linked to zKillboard
- Corp and alliance tags are resolved to zKillboard corporation links via the EVE ESI API
- Tags are 1–5 characters: letters, digits, `.`, `-`, or space (case-insensitive, shown in uppercase)
- Links are suppressed for tags or ship names that cannot be resolved
- The ship type list is refreshed automatically from ESI on each startup; the bundled list is used as fallback if ESI is unreachable

---

## Hotkeys

| Key | Action |
|-----|--------|
| Hold `Ctrl` (default) | Pause scanning while held — lets you browse zKillboard or other windows without triggering notifications |
| `Scroll Lock` (default) | Toggle **mouse-move pause** on/off |

When mouse-move pause is **on**, scanning stops as soon as the mouse moves and resumes 3 seconds after the last movement. This lets you click to a browser window, check zKillboard, and have scanning automatically resume when you stop moving the mouse.

Both keys and all timing are configurable in `settings.ini`:

```ini
[hotkeys]
pause_key = ctrl                ; hold to pause (ctrl, alt, shift, f9, scroll_lock, …)
mouse_pause_on_start = false    ; start with mouse-move pause already enabled
mouse_pause_seconds = 3         ; seconds after last mouse move before resuming
mouse_pause_toggle_key = scroll_lock  ; key to toggle mouse-move pause on/off
mouse_pause_deadzone = 0        ; minimum pixels moved to count as movement (0 = any movement)
```

---

## Command-Line Flags

```
eve-gate-logger.exe [--setup] [--reset] [--nocsv] [--config PATH]

  --setup        Force the region selector overlay open
  --reset        Clear the saved region and run auto-detect again
  --nocsv        Disable CSV logging (Discord/Telegram notifications still sent)
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
