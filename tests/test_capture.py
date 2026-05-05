from unittest.mock import patch, MagicMock
import numpy as np
from PIL import Image
from config import Region
from capture import capture_region

FAKE_ARRAY = np.zeros((100, 200, 4), dtype=np.uint8)

def _make_mock_mss():
    mock_sct = MagicMock()
    mock_sct.__enter__ = MagicMock(return_value=mock_sct)
    mock_sct.__exit__ = MagicMock(return_value=False)
    mock_sct.grab = MagicMock(return_value=MagicMock())
    return mock_sct

def test_capture_passes_correct_monitor_dict():
    region = Region(x=10, y=20, width=300, height=150)
    mock_sct = _make_mock_mss()

    with patch("capture.mss.mss", return_value=mock_sct), \
         patch("capture.np.array", return_value=FAKE_ARRAY):
        capture_region(region)

    mock_sct.grab.assert_called_once_with({
        "left": 10, "top": 20, "width": 300, "height": 150
    })

def test_capture_returns_pil_image():
    region = Region(x=0, y=0, width=50, height=50)
    mock_sct = _make_mock_mss()

    with patch("capture.mss.mss", return_value=mock_sct), \
         patch("capture.np.array", return_value=FAKE_ARRAY):
        result = capture_region(region)

    assert isinstance(result, Image.Image)
