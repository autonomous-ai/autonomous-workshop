"""ADR 0092: the owner's filament and Bought Part catalogues."""

import copy
import json
import tempfile
import unittest
from pathlib import Path

from workshop.errors import ContractError
from workshop.wish.catalogues import (
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


if __name__ == "__main__":
    unittest.main()
