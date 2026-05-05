from config import Ship
from tracker import ShipTracker

def test_new_ship_is_returned():
    t = ShipTracker()
    new = t.update({Ship("Angry Pirate", "Rifter")})
    assert Ship("Angry Pirate", "Rifter") in new

def test_same_ship_in_next_scan_is_not_returned():
    t = ShipTracker()
    t.update({Ship("Angry Pirate", "Rifter")})
    new = t.update({Ship("Angry Pirate", "Rifter")})
    assert len(new) == 0

def test_ship_that_left_and_reappears_is_returned():
    t = ShipTracker()
    t.update({Ship("Angry Pirate", "Rifter")})
    t.update(set())
    new = t.update({Ship("Angry Pirate", "Rifter")})
    assert Ship("Angry Pirate", "Rifter") in new

def test_multiple_ships_tracked_independently():
    t = ShipTracker()
    t.update({Ship("Alpha", "Rifter"), Ship("Beta", "Drake")})
    new = t.update({Ship("Beta", "Drake"), Ship("Gamma", "Merlin")})
    assert Ship("Gamma", "Merlin") in new
    assert Ship("Alpha", "Rifter") not in new
    assert Ship("Beta", "Drake") not in new

def test_same_name_different_type_tracked_separately():
    t = ShipTracker()
    new = t.update({Ship("Pilot", "Rifter"), Ship("Pilot", "Drake")})
    assert len(new) == 2
