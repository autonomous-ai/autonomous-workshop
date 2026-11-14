"""ADR 0104: a kit's Bought Parts block agrees with its Assembly Tree, so
Release bills the pins, glue and nippers the box ships."""

import json
import unittest

from workshop.errors import ContractError
from workshop.release.bought_extras import factory_extra_materials, sealed_bought_lines
from workshop.wish.assembly_tree import bought_totals
from workshop.wish.catalogues import parse_catalogues
from workshop.wish.design_contract import parse_design_contract
from tests.wish.test_assembly_tree import _schema_8_kit, _tree_block
from tests.wish.test_design_contract import _contract_text
from tests.wish.test_electrical import _kit10, _kit_catalogues

PRICES = {"steel-pin-1.5x29.5": 6, "clear-jar-6x7": 20, "led-3v-cool-white": 14,
          "battery-box-2aa-switch": 35, "tweezers": 78, "foam-tape": 59, "glue": 32, "nipper-mini": 150,
          "manual-printed": 120, "kit-packing": 50}


def _catalogues():
    filaments = {"schema_version": 1, "filaments": [
        {"id": name, "name": name.title(), "hex": "#112233", "kind": "opaque", "confirmed": True}
        for name in ("navy", "oak", "dark-oak", "dark-blue")
    ]}
    categories = {"steel-pin-1.5x29.5": "fastener", "clear-jar-6x7": "container", "led-3v-cool-white": "lamp",
                  "battery-box-2aa-switch": "power", "tweezers": "tool", "foam-tape": "consumable",
                  "glue": "consumable", "nipper-mini": "tool",
                  "manual-printed": "packaging", "kit-packing": "packaging"}
    parts = [{"id": key, "name": key, "category": category, "sizes": [], "pack": 1, "source": "a shop",
              "confirmed": True, "unit_price_cents": PRICES[key]} for key, category in categories.items()]
    return parse_catalogues(filaments, {"schema_version": 1, "parts": parts})


def _kit(materials=("tweezers", "foam-tape", "nipper-mini")):
    """The test book nook as a schema 10 kit with no circuit section."""

    block, prose = _schema_8_kit(_tree_block())
    block["schema_version"] = 10
    for geometry in block["geometries"]:
        del geometry["wall_min_mm"]
    block["assembly_tree"]["materials"] = list(materials)
    return block, prose


def _text(block, prose, parts):
    return _contract_text(block, prose=prose) + "\n```bought-parts\n%s\n```\n" % json.dumps({"parts": parts})


FULL = [{"bought": "steel-pin-1.5x29.5", "count": 2}, {"bought": "clear-jar-6x7", "count": 1},
        {"bought": "led-3v-cool-white", "count": 1}, {"bought": "battery-box-2aa-switch", "count": 1},
        {"bought": "nipper-mini", "count": 1}]


class KitBoughtBlockTest(unittest.TestCase):
    def _parse(self, parts, block=None):
        block, prose = block or _kit()
        return parse_design_contract(_text(block, prose, parts), catalogues=_catalogues())

    def _refused(self, parts, block=None):
        with self.assertRaises(ContractError) as caught:
            self._parse(parts, block)
        return str(caught.exception)

    def test_the_tree_counts_each_bought_entry_per_toy(self):
        block, _prose = _kit()
        self.assertEqual(bought_totals(block["assembly_tree"]), {
            "clear-jar-6x7": 1, "steel-pin-1.5x29.5": 1, "led-3v-cool-white": 1, "battery-box-2aa-switch": 1})
        block["assembly_tree"]["steps"][0]["inputs"][1]["count"] = 3
        block["assembly_tree"]["steps"][0]["count"] = 1
        self.assertEqual(bought_totals(block["assembly_tree"])["clear-jar-6x7"], 3)

    def test_a_kit_seals_its_block_with_spares_and_shipped_tools_priced(self):
        contract = self._parse(FULL)
        self.assertEqual(contract.to_dict()["bought_parts"], {"parts": FULL})
        snapshot = contract.kit_catalogue()
        self.assertEqual(snapshot["unit_prices"]["nipper-mini"], 150)
        self.assertEqual(snapshot["unit_prices"]["steel-pin-1.5x29.5"], 6)
        lines = sealed_bought_lines(contract.to_dict(), snapshot)
        self.assertEqual({line["part"]: (line["count"], line["unit_price_cents"]) for line in lines}, {
            "steel-pin-1.5x29.5": (2, 6), "clear-jar-6x7": (1, 20), "led-3v-cool-white": (1, 14),
            "battery-box-2aa-switch": (1, 35), "nipper-mini": (1, 150)})
        self.assertEqual(len(factory_extra_materials(lines)), 5)

    def test_every_tree_bought_part_is_listed_at_its_count_or_more(self):
        self.assertIn("hold 1 x clear-jar-6x7, which the block does not list",
                      self._refused([item for item in FULL if item["bought"] != "clear-jar-6x7"]))
        block = _kit()
        block[0]["assembly_tree"]["steps"][2]["inputs"][2]["count"] = 3
        self.assertIn("lists 2 x steel-pin-1.5x29.5, but the Assembly Tree holds 3",
                      self._refused(FULL, block))

    def test_a_tool_the_manual_does_not_list_is_refused(self):
        self.assertIn("lists glue, which the Assembly Tree neither holds",
                      self._refused(FULL + [{"bought": "glue", "count": 1}]))
        self.assertIn("lists nipper-mini, which the Assembly Tree neither holds",
                      self._refused(FULL, _kit(materials=("tweezers",))))

    def test_packaging_is_billed_from_the_block_and_never_a_part_or_material(self):
        packed = FULL + [{"bought": "manual-printed", "count": 1}, {"bought": "kit-packing", "count": 1}]
        contract = self._parse(packed)
        lines = {line["part"]: line for line in sealed_bought_lines(contract.to_dict(), contract.kit_catalogue())}
        self.assertEqual((lines["manual-printed"]["count"], lines["manual-printed"]["unit_price_cents"]), (1, 120))
        self.assertEqual((lines["kit-packing"]["count"], lines["kit-packing"]["unit_price_cents"]), (1, 50))
        block = _kit(materials=("tweezers", "nipper-mini", "kit-packing"))
        self.assertIn("names 'kit-packing', a packaging", self._refused(FULL, block))
        block = _kit()
        block[0]["assembly_tree"]["parts"][5]["bought"] = "manual-printed"
        self.assertIn("is packaging: a kit bills it in its bought-parts block", self._refused(FULL, block))

    def test_a_kit_circuit_counts_its_own_parts_and_the_block_the_rest(self):
        block, prose = _kit10()
        rest = [{"bought": "steel-pin-1.5x29.5", "count": 1}, {"bought": "clear-jar-6x7", "count": 1}]
        contract = parse_design_contract(_text(block, prose, rest), catalogues=_kit_catalogues())
        self.assertEqual(contract.to_dict()["bought_parts"], {"parts": rest})
        with self.assertRaises(ContractError) as caught:
            parse_design_contract(_text(block, prose, rest[:1]), catalogues=_kit_catalogues())
        self.assertIn("1 x clear-jar-6x7, which the block does not list", str(caught.exception))

    def test_a_kit_without_a_block_bills_its_tree_unpriced_and_refuses(self):
        block, prose = _kit()
        contract = parse_design_contract(_contract_text(block, prose=prose), catalogues=_catalogues())
        lines = sealed_bought_lines(contract.to_dict(), contract.kit_catalogue())
        self.assertEqual(sorted((line["part"], line["count"]) for line in lines), [
            ("battery-box-2aa-switch", 1), ("clear-jar-6x7", 1), ("led-3v-cool-white", 1),
            ("steel-pin-1.5x29.5", 1)])
        with self.assertRaises(ContractError) as caught:
            factory_extra_materials(lines)
        self.assertIn("steel-pin-1.5x29.5", str(caught.exception))

    def test_a_tree_without_bought_parts_and_no_block_bills_nothing(self):
        block, prose = _kit()
        tree = block["assembly_tree"]
        tree["parts"] = [item for item in tree["parts"] if "bought" not in item]
        self.assertIsNone(sealed_bought_lines({"assembly_tree": {"parts": tree["parts"], "steps": []}}, {}))

    def test_the_packaged_catalogue_carries_the_priced_kit_extras(self):
        from workshop.wish.catalogues import load_catalogues

        parts = load_catalogues().parts
        self.assertTrue(parts["nipper-mini"].material)
        self.assertEqual(parts["nipper-mini"].unit_price_cents, 150)
        for name, cents in (("manual-printed", 120), ("kit-packing", 50)):
            self.assertTrue(parts[name].packaging)
            self.assertFalse(parts[name].material)
            self.assertEqual(parts[name].unit_price_cents, cents)


if __name__ == "__main__":
    unittest.main()
