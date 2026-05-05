import unittest
from unittest.mock import patch
from config import Ship
from enrich import enrich
from ship_matcher import ShipMatch


def _match(name, type_id, ocr_variant=None):
    return ShipMatch(name, type_id, ocr_variant or name)


class TestEnrich(unittest.TestCase):

    # ------------------------------------------------------------------
    # Pilot name
    # ------------------------------------------------------------------

    def test_pilot_name_unchanged_when_no_bleed(self):
        with patch("enrich.ship_matcher.match_ship", return_value=_match("Magnate", 596)):
            c = enrich(Ship("k Panzer-Kunst", "Magnate [SWA]"))
        self.assertEqual(c.pilot_name, "k Panzer-Kunst")

    def test_ship_type_stripped_from_pilot_name_when_bleeding(self):
        """OCR sometimes puts ship type at end of name column — strip it."""
        with patch("enrich.ship_matcher.match_ship", return_value=_match("Venture", 608, "Venture")):
            c = enrich(Ship("SumoEnjoyer Venture", "Venture [STI]"))
        self.assertEqual(c.pilot_name, "SumoEnjoyer")

    # ------------------------------------------------------------------
    # Ship type
    # ------------------------------------------------------------------

    def test_canonical_ship_name_used_when_matched(self):
        with patch("enrich.ship_matcher.match_ship", return_value=_match("Magnate", 596)):
            c = enrich(Ship("k Panzer-Kunst", "Magnate [SWA]"))
        self.assertEqual(c.ship_type, "Magnate")
        self.assertEqual(c.ship_type_id, 596)

    def test_raw_type_used_when_no_match(self):
        with patch("enrich.ship_matcher.match_ship", return_value=None):
            c = enrich(Ship("SomePilot", "Unknown Ship"))
        self.assertEqual(c.ship_type, "Unknown Ship")
        self.assertIsNone(c.ship_type_id)

    def test_tags_stripped_from_type_when_no_match(self):
        with patch("enrich.ship_matcher.match_ship", return_value=None):
            c = enrich(Ship("SomePilot", "SomeShip [ABC]"))
        self.assertEqual(c.ship_type, "SomeShip")

    # ------------------------------------------------------------------
    # Tags
    # ------------------------------------------------------------------

    def test_tags_uppercased(self):
        with patch("enrich.ship_matcher.match_ship", return_value=_match("Worm", 49711)):
            c = enrich(Ship("Imamizer", "Worm [swa]"))
        self.assertEqual(c.tags, ["SWA"])

    def test_multiple_tags(self):
        with patch("enrich.ship_matcher.match_ship", return_value=_match("Atron", 608)):
            c = enrich(Ship("Koechka", "Atron [.NLC.] [BUSHI]"))
        self.assertEqual(c.tags, [".NLC.", "BUSHI"])

    def test_no_tags(self):
        with patch("enrich.ship_matcher.match_ship", return_value=_match("Rifter", 587)):
            c = enrich(Ship("SomePilot", "Rifter"))
        self.assertEqual(c.tags, [])

    def test_tag_with_digits(self):
        with patch("enrich.ship_matcher.match_ship", return_value=_match("Venture", 608)):
            c = enrich(Ship("SomePilot", "Venture [4TH]"))
        self.assertEqual(c.tags, ["4TH"])

    # ------------------------------------------------------------------
    # CSV format (name, type, tags columns)
    # ------------------------------------------------------------------

    def test_csv_columns_no_duplication(self):
        """CSV name must not contain ship type; type must not contain tags."""
        with patch("enrich.ship_matcher.match_ship", return_value=_match("Venture", 608, "Venture")):
            c = enrich(Ship("SumoEnjoyer Venture", "Venture [STI]"))
        csv_tags = " ".join(f"[{t}]" for t in c.tags)
        self.assertEqual(c.pilot_name, "SumoEnjoyer")   # no ship type in name
        self.assertEqual(c.ship_type, "Venture")         # no tags in type
        self.assertEqual(csv_tags, "[STI]")

    def test_csv_tags_format(self):
        """Tags column: space-separated bracket tokens."""
        with patch("enrich.ship_matcher.match_ship", return_value=_match("Atron", 608)):
            c = enrich(Ship("Koechka", "Atron [.NLC.] [BUSHI]"))
        csv_tags = " ".join(f"[{t}]" for t in c.tags)
        self.assertEqual(csv_tags, "[.NLC.] [BUSHI]")

    # ------------------------------------------------------------------
    # Discord message format: time pilot ship tags
    # ------------------------------------------------------------------

    def test_discord_message_order(self):
        """Message must be: `HH:MM` pilot ship [TAG] — ship before tags."""
        from unittest.mock import patch as p
        import discord_notifier

        captured = []

        def fake_urlopen(req, timeout=None):
            import json
            body = json.loads(req.data)
            captured.append(body["content"])
            return __import__("io").BytesIO(b"{}")

        with patch("enrich.ship_matcher.match_ship", return_value=_match("Magnate", 596)):
            contact = enrich(Ship("k Panzer-Kunst", "Magnate [SWA]"))

        with patch("discord_notifier._resolve_corp", return_value=None), \
             patch("urllib.request.urlopen", side_effect=fake_urlopen):
            discord_notifier._send(["http://fake-webhook"], contact, "2026-05-06T00:05:00")

        self.assertEqual(len(captured), 1)
        msg = captured[0]
        # Format: `00:05` k Panzer-Kunst [Magnate](<url>) [SWA]
        self.assertIn("`00:05`", msg)
        pilot_pos = msg.index("k Panzer-Kunst")
        ship_pos = msg.index("Magnate")
        tag_pos = msg.index("[SWA]")
        self.assertLess(pilot_pos, ship_pos, "pilot name must come before ship type")
        self.assertLess(ship_pos, tag_pos, "ship type must come before tags")

    def test_discord_message_no_duplicate_ship_name(self):
        """Ship name must appear exactly once in the message."""
        import discord_notifier

        captured = []

        def fake_urlopen(req, timeout=None):
            import json
            body = json.loads(req.data)
            captured.append(body["content"])
            return __import__("io").BytesIO(b"{}")

        with patch("enrich.ship_matcher.match_ship", return_value=_match("Venture", 608, "Venture")):
            contact = enrich(Ship("SumoEnjoyer Venture", "Venture [STI]"))

        with patch("discord_notifier._resolve_corp", return_value=None), \
             patch("urllib.request.urlopen", side_effect=fake_urlopen):
            discord_notifier._send(["http://fake-webhook"], contact, "2026-05-06T00:13:00")

        msg = captured[0]
        self.assertEqual(msg.count("Venture"), 1, f"Venture appears more than once: {msg}")


if __name__ == "__main__":
    unittest.main()
