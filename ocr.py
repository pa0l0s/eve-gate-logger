import numpy as np
import pytesseract
from PIL import Image
from config import Ship, ColumnMap

CONF_THRESHOLD = 35
ROW_TOLERANCE = 8
TESSERACT_CONFIG = "--psm 6"
UPSCALE = 2
BRIGHTNESS_THRESHOLD = 140      # primary pass: preserves letter shape (o vs a)
BRIGHTNESS_THRESHOLD_LOW = 120  # supplementary pass: recovers dots and faint chars

_EVE_COLUMN_HEADERS = frozenset({
    "Name", "Type", "Distance", "Velocity", "Corporation",
    "Alliance", "Faction", "Tag", "Icon", "Radial", "Transverse",
    "Militia", "Size", "Status",
})

_EVE_UI_MESSAGE_WORDS = frozenset({"Nothing", "Found"})


def preprocess_image(image: Image.Image) -> Image.Image:
    return _make_thresh(image, BRIGHTNESS_THRESHOLD)


def parse_overview_image(image: Image.Image, column_map: ColumnMap) -> set[Ship]:
    words = _two_pass_words(image)
    rows = _group_words_by_row(words)
    ships = set()
    for row in rows:
        name = _extract_column_text(row, column_map.name_start, column_map.name_end)
        ship_type = _extract_column_text(row, column_map.type_start, column_map.type_end)
        if name and ship_type and not _is_header_row(row):
            ships.add(Ship(name, ship_type))
    return ships


def _make_thresh(image: Image.Image, threshold: int) -> Image.Image:
    w, h = image.size
    scaled = image.resize((w * UPSCALE, h * UPSCALE), Image.LANCZOS)
    arr = np.array(scaled.convert("L"))
    thresh = np.where(arr > threshold, 0, 255).astype(np.uint8)
    return Image.fromarray(thresh)


def _two_pass_words(image: Image.Image) -> list[dict]:
    """Run OCR at two brightness thresholds and merge by confidence per position."""
    all_words: list[dict] = []
    for threshold in (BRIGHTNESS_THRESHOLD, BRIGHTNESS_THRESHOLD_LOW):
        data = pytesseract.image_to_data(
            _make_thresh(image, threshold),
            config=TESSERACT_CONFIG,
            output_type=pytesseract.Output.DICT,
        )
        for i, text in enumerate(data["text"]):
            if text.strip() and int(data["conf"][i]) >= CONF_THRESHOLD:
                all_words.append({
                    "text": text,
                    "x": data["left"][i] // UPSCALE,
                    "y": data["top"][i] // UPSCALE,
                    "conf": int(data["conf"][i]),
                })

    # Greedy merge: highest-confidence candidate wins at each position
    merged: list[dict] = []
    for word in sorted(all_words, key=lambda w: -w["conf"]):
        if not any(
            abs(m["x"] - word["x"]) <= 20 and abs(m["y"] - word["y"]) <= 8
            for m in merged
        ):
            merged.append(word)
    return merged


def _group_words_by_row(words: list[dict]) -> list[list[dict]]:
    if not words:
        return []
    words_sorted = sorted(words, key=lambda w: w["y"])
    rows: list[list[dict]] = []
    current = [words_sorted[0]]
    for word in words_sorted[1:]:
        if abs(word["y"] - current[0]["y"]) <= ROW_TOLERANCE:
            current.append(word)
        else:
            rows.append(sorted(current, key=lambda w: w["x"]))
            current = [word]
    rows.append(sorted(current, key=lambda w: w["x"]))
    return rows


def _extract_column_text(row: list[dict], col_start: int, col_end: int) -> str:
    return " ".join(
        w["text"] for w in row
        if col_start <= w["x"] < col_end and not _is_noise_word(w["text"])
    ).strip()


def _is_noise_word(text: str) -> bool:
    """Filter distance/speed numbers, 'km', and OCR garbage (icons, symbols)."""
    if text.lower() == "km":
        return True
    if text.isdigit():
        return True
    # Numbers with OCR noise appended (e.g. '38¢', '1b4') — starts with a digit
    if text[0].isdigit():
        return True
    # No alphabetic characters at all (e.g. '©.', '=>')
    if not any(c.isalpha() for c in text):
        return True
    # Contains non-ASCII characters (e.g. 'i¢=', 'km_') — EVE text is always ASCII
    if not all(ord(c) < 128 for c in text):
        return True
    return False


def _is_header_row(row: list[dict]) -> bool:
    words = {w["text"] for w in row}
    return len(words & _EVE_COLUMN_HEADERS) >= 2 or _EVE_UI_MESSAGE_WORDS.issubset(words)
