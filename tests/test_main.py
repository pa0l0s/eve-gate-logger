from unittest.mock import MagicMock, patch
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
