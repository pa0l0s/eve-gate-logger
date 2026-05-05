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
