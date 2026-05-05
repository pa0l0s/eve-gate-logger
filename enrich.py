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
        # Strip the matched OCR variant from the end of pilot_name if it bled
        # from the type column into the name column due to a column boundary offset
        pilot_name = re.sub(
            r'\s+' + re.escape(sm.ocr_variant) + r'$', '',
            ship.name, flags=re.IGNORECASE
        ).strip()
    else:
        ship_type = _TAGS_RE.sub("", ship.ship_type).strip()
        ship_type_id = None
        pilot_name = ship.name

    return Contact(pilot_name, ship_type, ship_type_id, tags)
