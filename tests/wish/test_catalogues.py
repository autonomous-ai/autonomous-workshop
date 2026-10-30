"""ADR 0092: the owner's filament and Bought Part catalogues."""

import copy
import json
import tempfile
import unittest
from pathlib import Path

from workshop.errors import ContractError
from workshop.wish.catalogues import (
    BOUGHT_PART_HEX,
    BOUGHT_PARTS_FILE,
    CATALOGUE_DIRECTORY,
    FILAMENTS_FILE,
    load_catalogues,
    parse_catalogues,
)


def _filaments():
    return {"schema_version": 1, "filaments": [
        {"id": "navy", "name": "Navy", "hex": "#1f2a44", "kind": "opaque", "confirmed": True},
        {"id": "glow", "name": "Glow", "hex": "#d8f0c8", "kind": "glow", "confirmed": False},
    ]}


def _bought():
    return {"schema_version": 1, "parts": [
        {"id": "steel-pin-1.5x29.5", "name": "Steel pin", "category": "fastener",
         "sizes": [{"what": "diameter", "mm": [1.5]}, {"what": "length", "mm": [29.5]}],
         "pack": 50, "source": "A named shop", "confirmed": True},
        {"id": "led-3v-warm-white", "name": "Micro LED", "category": "lamp",
         "sizes": [{"what": "bead diameter", "max_mm": [2.2]}],
         "pack": None, "source": None, "confirmed": False},
        {"id": "tweezers", "name": "Tweezers", "category": "tool", "sizes": [],
         "pack": None, "source": None, "confirmed": False},
    ]}


class CatalogueTest(unittest.TestCase):
    def _refused(self, filaments, bought):
        with self.assertRaises(ContractError) as caught:
            parse_catalogues(filaments, bought)
        return str(caught.exception)

    def test_both_catalogues_parse(self):
        catalogues = parse_catalogues(_filaments(), _bought())
        self.assertEqual(catalogues.filaments["glow"].kind, "glow")
        self.assertEqual(catalogues.parts["steel-pin-1.5x29.5"].pack, 50)
        self.assertTrue(catalogues.parts["tweezers"].material)
        self.assertFalse(catalogues.parts["led-3v-warm-white"].material)

    def test_a_confirmed_bought_part_needs_its_pack_and_source(self):
        bought = _bought()
        bought["parts"][0]["source"] = None
        self.assertIn("is confirmed, so it needs its pack size and source", self._refused(_filaments(), bought))

    def test_malformed_entries_are_all_named(self):
        filaments, bought = _filaments(), _bought()
        filaments["filaments"][0]["hex"] = "navy"
        filaments["filaments"][1]["kind"] = "sparkle"
        filaments["filaments"].append(copy.deepcopy(filaments["filaments"][0]))
        bought["parts"][0]["category"] = "gadget"
        bought["parts"][1]["sizes"] = [{"what": "bead", "mm": [2], "max_mm": [3]}]
        bought["parts"][2]["pack"] = 0
        message = self._refused(filaments, bought)
        for needle in ("hex must be a lowercase #rrggbb", "kind must be opaque, translucent, glow",
                       "filaments[2].id repeats 'navy'", "category must be one of",
                       "sizes[0] must be {what, mm}", "pack must be how many come in one pack"):
            self.assertIn(needle, message)

    def test_no_filament_may_take_the_reserved_bought_part_colour(self):
        # Owner decision Q29: Bought Parts are magenta in every STEP, a colour
        # no spool may have, nor one the colour gate cannot tell from it.
        self.assertEqual(BOUGHT_PART_HEX, "#ff00ff")
        for hex_code in (BOUGHT_PART_HEX, "#fd01fe"):
            filaments = _filaments()
            filaments["filaments"][0]["hex"] = hex_code
            self.assertIn("filaments[0].hex is %s, the reserved colour of Bought Parts" % hex_code,
                          self._refused(filaments, _bought()))
        filaments = _filaments()
        filaments["filaments"][0]["hex"] = "#fa00ff"
        self.assertIn("navy", parse_catalogues(filaments, _bought()).filaments)

    def test_the_run_local_gate_holds_the_same_reserved_colour(self):
        from tests.make.test_kit_tree import kit_tree

        self.assertEqual(kit_tree.BOUGHT_PART_HEX, BOUGHT_PART_HEX)

    def test_a_catalogue_needs_its_schema_and_entries(self):
        message = self._refused({"filaments": []}, {"schema_version": 1, "parts": []})
        self.assertIn("filaments.json must be an object with schema_version 1", message)
        self.assertIn("bought-parts.json.parts must be a non-empty list", message)

    def test_load_reads_a_directory_and_refuses_a_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / FILAMENTS_FILE).write_text(json.dumps(_filaments()), encoding="utf-8")
            with self.assertRaises(ContractError) as caught:
                load_catalogues(tmp)
            self.assertIn("cannot read %s" % BOUGHT_PARTS_FILE, str(caught.exception))
            (Path(tmp) / BOUGHT_PARTS_FILE).write_text(json.dumps(_bought()), encoding="utf-8")
            self.assertIn("navy", load_catalogues(tmp).filaments)

    def test_the_packaged_seed_covers_night_charms_hall_and_is_unconfirmed(self):
        catalogues = load_catalogues()
        for name in ("navy", "oak", "dark-oak", "black", "brass", "white", "green",
                     "translucent-amber", "glow"):
            self.assertIn(name, catalogues.filaments)
        for name in ("battery-box-2aa-switch", "led-3v-warm-white", "led-3v-cool-white",
                     "steel-pin-1.5x29.5", "screw-m2x8-pan-self-tapping", "clear-jar-6x7",
                     "foam-tape", "foam-dots", "tweezers", "screwdriver"):
            self.assertIn(name, catalogues.parts)
        self.assertTrue((CATALOGUE_DIRECTORY / FILAMENTS_FILE).is_file())
        self.assertFalse(any(entry.confirmed for entry in catalogues.filaments.values()))
        self.assertFalse(any(entry.confirmed for entry in catalogues.parts.values()))

    def test_the_packaged_seed_holds_the_turtle_keycap_colours(self):
        # Owner, 2026-10-29: jade and mint added for the K4 turtle keycap.
        filaments = load_catalogues().filaments
        self.assertEqual((filaments["jade"].hex, filaments["jade"].kind), ("#3f9a85", "opaque"))
        self.assertEqual((filaments["mint"].hex, filaments["mint"].kind), ("#a3d9c3", "opaque"))

    def test_the_packaged_seed_holds_the_toadstool_red(self):
        # Owner, 2026-10-30: scarlet red added for the toadstool headphone stand.
        filaments = load_catalogues().filaments
        self.assertEqual(
            (filaments["scarlet-red"].hex, filaments["scarlet-red"].kind), ("#de4343", "opaque")
        )


    def test_the_packaged_seed_holds_the_mac_fidget_circuit_unconfirmed(self):
        # ADR 0095: cells, contacts and a switch are categories of their own,
        # and a part with leads gives its lead diameter.
        parts = load_catalogues().parts
        categories = {name: parts[name].category for name in (
            "cell-aaa", "contact-aaa-spring", "contact-aaa-plate", "contact-aaa-bridge",
            "microswitch-mini-lever", "led-5mm-amber-diffused", "resistor-75r", "wire-28awg",
            "screw-m2x6-pan", "solder", "soldering-iron")}
        self.assertEqual(categories, {
            "cell-aaa": "cell", "contact-aaa-spring": "contact", "contact-aaa-plate": "contact",
            "contact-aaa-bridge": "contact", "microswitch-mini-lever": "switch",
            "led-5mm-amber-diffused": "lamp", "resistor-75r": "other", "wire-28awg": "wire",
            "screw-m2x6-pan": "fastener", "solder": "consumable", "soldering-iron": "tool"})
        self.assertEqual(parts["microswitch-mini-lever"].lead_diameter_mm, 0.8)
        self.assertIsNone(parts["contact-aaa-bridge"].lead_diameter_mm)
        self.assertFalse(any(parts[name].confirmed for name in categories))

    def test_the_lead_diameter_is_the_largest_one_given(self):
        bought = _bought()
        bought["parts"][1]["sizes"].append({"what": "lead diameter", "max_mm": [0.45, 0.5]})
        parts = parse_catalogues(_filaments(), bought).parts
        self.assertEqual(parts["led-3v-warm-white"].lead_diameter_mm, 0.5)
        self.assertIsNone(parts["steel-pin-1.5x29.5"].lead_diameter_mm)


if __name__ == "__main__":
    unittest.main()
