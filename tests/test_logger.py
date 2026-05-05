import csv
import os
from unittest.mock import patch
from config import Ship
from logger import CSVLogger

def test_creates_csv_with_header(tmp_path):
    path = str(tmp_path / "log.csv")
    log = CSVLogger(path)
    log.log(Ship("Angry Pirate", "Rifter"))
    log.close()

    with open(path) as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == ["timestamp", "name", "type", "event"]
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["name"] == "Angry Pirate"
        assert rows[0]["type"] == "Rifter"
        assert rows[0]["event"] == "appeared"

def test_appends_rows_without_duplicate_header(tmp_path):
    path = str(tmp_path / "log.csv")
    log = CSVLogger(path)
    log.log(Ship("Alpha", "Rifter"))
    log.close()

    log2 = CSVLogger(path)
    log2.log(Ship("Beta", "Drake"))
    log2.close()

    with open(path) as f:
        lines = f.readlines()
    data_lines = [l for l in lines if l.strip() and not l.startswith("timestamp")]
    assert len(data_lines) == 2

def test_permission_error_prints_warning_does_not_crash(tmp_path, capsys):
    path = str(tmp_path / "log.csv")
    log = CSVLogger(path)

    with patch("builtins.open", side_effect=PermissionError("locked")):
        log.log(Ship("Alpha", "Rifter"))

    captured = capsys.readouterr()
    assert "locked" in captured.out.lower() or "permission" in captured.out.lower()
