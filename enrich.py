import re
from config import Ship, Contact
import ship_matcher

_TAGS_RE = re.compile(r'\[([A-Z0-9.\- ]{1,5})\]', re.IGNORECASE)


def enrich(ship: Ship) -> Contact:
    """Convert raw OCR Ship into a Contact with uppercase tags and canonical ship name."""
    tags = [t.upper() for t in _TAGS_RE.findall(ship.ship_type)]

    sm = ship_matcher.match_ship(ship.name, ship.ship_type)
    if sm:
        ship_type = sm.canonical_name
        ship_type_id = sm.type_id
    else:
        ship_type = _TAGS_RE.sub("", ship.ship_type).strip()
        ship_type_id = None

    return Contact(ship.name, ship_type, ship_type_id, tags)
