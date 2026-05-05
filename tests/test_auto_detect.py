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
    assert region.y > 50
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
