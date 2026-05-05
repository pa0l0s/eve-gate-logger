from unittest.mock import patch
from PIL import Image
from config import Ship, ColumnMap
from ocr import parse_overview_image, preprocess_image

# Row y≈5:  "Angry"(x=10) "Pirate"(x=55) | "Rifter"(x=130)
# Row y≈25: "Space"(x=10) "Trucker"(x=55) | "Badger"(x=130)
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
        "conf":  [10,               90],
    }
    image = Image.new("RGB", (300, 50))
    with patch("ocr.pytesseract.image_to_data", return_value=low_conf_data):
        ships = parse_overview_image(image, COLUMN_MAP)
    assert ships == set()

def test_preprocess_returns_grayscale_image():
    image = Image.new("RGB", (100, 50), color=(30, 30, 30))
    result = preprocess_image(image)
    assert result.mode == "L"
