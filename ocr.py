import numpy as np
import pytesseract
from PIL import Image
from config import Ship, ColumnMap

CONF_THRESHOLD = 35
ROW_TOLERANCE = 8
TESSERACT_CONFIG = "--psm 6"
UPSCALE = 2
BRIGHTNESS_THRESHOLD = 130  # pixels brighter than this are EVE text (white on dark bg)

_EVE_COLUMN_HEADERS = frozenset({
    "Name", "Type", "Distance", "Velocity", "Corporation",
    "Alliance", "Faction", "Tag", "Icon", "Radial", "Transverse",
    "Militia", "Size", "Status",
})

_EVE_UI_MESSAGE_WORDS = frozenset({"Nothing", "Found"})


def preprocess_image(image: Image.Image) -> Image.Image:
    w, h = image.size
    image = image.resize((w * UPSCALE, h * UPSCALE), Image.LANCZOS)
    arr = np.array(image.convert("L"))
    # EVE uses white text on dark background; invert so Tesseract sees black on white
    thresh = np.where(arr > BRIGHTNESS_THRESHOLD, 0, 255).astype(np.uint8)
    return Image.fromarray(thresh)


def parse_overview_image(image: Image.Image, column_map: ColumnMap) -> set[Ship]:
    processed = preprocess_image(image)
    data = pytesseract.image_to_data(processed, config=TESSERACT_CONFIG, output_type=pytesseract.Output.DICT)
    rows = _group_words_by_row(data)
    ships = set()
    for row in rows:
        name = _extract_column_text(row, column_map.name_start, column_map.name_end)
        ship_type = _extract_column_text(row, column_map.type_start, column_map.type_end)
        if name and ship_type and not _is_header_row(row):
            ships.add(Ship(name, ship_type))
    return ships


def _group_words_by_row(data: dict) -> list[list[dict]]:
    words = [
        # Divide coords by UPSCALE so they match the original column_map positions
        {"text": t, "x": data["left"][i] // UPSCALE, "y": data["top"][i] // UPSCALE}
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
    # No alphabetic characters at all (e.g. '©.', 'i¢=', '=>')
    if not any(c.isalpha() for c in text):
        return True
    return False


def _is_header_row(row: list[dict]) -> bool:
    words = {w["text"] for w in row}
    return len(words & _EVE_COLUMN_HEADERS) >= 2 or _EVE_UI_MESSAGE_WORDS.issubset(words)
