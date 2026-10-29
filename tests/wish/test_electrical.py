"""ADR 0095: a schema 10 Design Contract states a powered toy's circuit."""

import copy
import unittest

from workshop.errors import ContractError
from workshop.wish.catalogues import load_catalogues, parse_catalogues
from workshop.wish.design_contract import parse_design_contract
from tests.wish.test_assembly_tree import _schema_8_kit, _tree_block
from tests.wish.test_design_contract import _PROSE, _contract_text, _prose_block


def _electrical():
    """The Macintosh fidget's locked circuit: 2 x AAA, a lever microswitch
    on the + lead, 75 ohm and an amber LED (toys-spec NOTES, 2026-10-29)."""

    return {
        "parts": [
            {"id": "cells", "bought": "cell-aaa", "count": 2, "role": "source"},
            {"id": "plate", "bought": "contact-aaa-plate", "role": "connector"},
            {"id": "spring", "bought": "contact-aaa-spring", "role": "connector"},
            {"id": "bridge", "bought": "contact-aaa-bridge", "role": "connector"},
            {"id": "switch", "bought": "microswitch-mini-lever", "role": "switch"},
            {"id": "resistor", "bought": "resistor-75r", "role": "controller"},
            {"id": "led", "bought": "led-5mm-amber-diffused", "role": "load"},
            {"id": "wire", "bought": "wire-28awg", "role": "wire"},
        ],
        "paths": [{"id": "screen-light", "load": "led", "current_ma": 12.7,
                   "sequence": ["cells", "plate", "switch", "resistor", "led", "spring", "bridge", "cells"]}],
        "supply_v": {"min": 2.4, "nominal": 3.0, "max": 3.2},
        "standby_ma": 0,
        "runtime_h": 60,
        "switch_logic": "The floppy fully in presses the NO microswitch: lit. Out: dark.",
        "assembled_by": "maker",
        "joins": "solder",
        "batteries_included": False,
    }


def _schema10(electrical=None):
    block = _prose_block(schema_version=10)
    for geometry in block["geometries"]:
        del geometry["wall_min_mm"]
    block["electrical"] = _electrical() if electrical is None else electrical
    return block


class ElectricalSectionTest(unittest.TestCase):
    def _parse(self, block):
        return parse_design_contract(_contract_text(block, prose=_PROSE))

    def _refused(self, block):
        with self.assertRaises(ContractError) as caught:
            self._parse(block)
        return str(caught.exception)

    def test_the_mac_fidget_circuit_seals_verbatim_with_its_catalogue(self):
        block = _schema10()
        contract = self._parse(block)
        contract.check_sealable()
        self.assertEqual(contract.schema_version, 10)
        self.assertEqual(contract.to_dict()["electrical"], block["electrical"])
        self.assertIsNone(contract.assembly_tree)
        # A powered toy that is no kit still seals its Bought Parts.
        snapshot = contract.kit_catalogue()
        self.assertEqual(sorted(snapshot["bought_parts"]), sorted(
            {item["bought"] for item in block["electrical"]["parts"]}))
        self.assertEqual(snapshot["bought_parts"]["microswitch-mini-lever"]["category"], "switch")
        self.assertIn("bought-parts.json:cell-aaa", contract.electrical.unconfirmed)

    def test_a_contract_without_the_section_is_unpowered(self):
        block = _schema10()
        del block["electrical"]
        contract = self._parse(block)
        self.assertIsNone(contract.electrical)
        self.assertIsNone(contract.kit_catalogue())
        self.assertNotIn("electrical", contract.to_dict())

    def test_schema_9_refuses_the_section(self):
        block = _schema10()
        block["schema_version"] = 9
        self.assertIn("electrical needs schema_version 10 or later", self._refused(block))

    def test_every_missing_field_is_named(self):
        block = _schema10()
        for name in ("standby_ma", "runtime_h", "switch_logic", "assembled_by"):
            del block["electrical"][name]
        message = self._refused(block)
        self.assertIn("electrical is missing: assembled_by, runtime_h, standby_ma, switch_logic", message)

    def test_parts_must_come_from_the_catalogue_in_their_role(self):
        block = _schema10()
        block["electrical"]["parts"][4]["bought"] = "reed-switch"
        self.assertIn("'reed-switch', which is not in the Bought Part catalogue", self._refused(block))
        block = _schema10()
        block["electrical"]["parts"][4]["role"] = "load"
        self.assertIn("a switch Bought Part plays switch, not load", self._refused(block))
        block = _schema10()
        block["electrical"]["parts"][0]["role"] = "battery"
        self.assertIn("role must be one of check_power's roles", self._refused(block))
        block = _schema10()
        block["electrical"]["parts"].append({"id": "iron", "bought": "soldering-iron", "role": "load"})
        self.assertIn("a tool, which is no circuit part", self._refused(block))

    def test_a_path_runs_from_its_source_through_one_load_and_back(self):
        block = _schema10()
        block["electrical"]["paths"][0]["sequence"] = ["plate", "switch", "led", "plate"]
        self.assertIn("begins and ends at its source", self._refused(block))
        block = _schema10()
        block["electrical"]["paths"][0]["sequence"].insert(1, "wire")
        self.assertIn("leaves wires out", self._refused(block))
        block = _schema10()
        block["electrical"]["paths"][0]["load"] = "switch"
        self.assertIn("load must name a load or actuator part", self._refused(block))
        block = _schema10()
        block["electrical"]["paths"][0]["sequence"].remove("resistor")
        self.assertIn("electrical part resistor is on no path", self._refused(block))
        block = _schema10()
        block["electrical"]["paths"][0]["sequence"][2] = "fuse"
        self.assertIn("names fuse, which is no electrical part", self._refused(block))
        block = _schema10()
        block["electrical"]["parts"].append({"id": "led-two", "bought": "led-5mm-amber-diffused", "role": "load"})
        block["electrical"]["paths"][0]["sequence"].insert(5, "led-two")
        self.assertIn("carries another source or load inline: led-two", self._refused(block))

    def test_the_numbers_and_choices_the_grill_settles_are_checked(self):
        block = _schema10()
        block["electrical"]["supply_v"] = {"min": 3.2, "nominal": 3.0, "max": 2.4}
        self.assertIn("supply_v must be {min, nominal, max}", self._refused(block))
        block = _schema10()
        block["electrical"]["paths"][0]["current_ma"] = 0
        self.assertIn("current_ma must be the load's current", self._refused(block))
        block = _schema10()
        block["electrical"]["standby_ma"] = -1
        self.assertIn("standby_ma must be the drain", self._refused(block))
        block = _schema10()
        block["electrical"]["assembled_by"] = "factory"
        self.assertIn("assembled_by must be maker or buyer", self._refused(block))
        block = _schema10()
        block["electrical"]["joins"] = "glue"
        self.assertIn("joins must be solder or solderless", self._refused(block))
        block = _schema10()
        block["electrical"]["batteries_included"] = "no"
        self.assertIn("batteries_included must be true or false", self._refused(block))
        block = _schema10()
        block["electrical"]["parts"] = [item for item in block["electrical"]["parts"] if item["id"] != "cells"]
        self.assertIn("has no source", self._refused(block))


def _kit_catalogues():
    """The kit test's catalogue plus the Mac fidget's seeds, all confirmed."""

    packaged = load_catalogues()
    filaments = {"schema_version": 1, "filaments": [
        {"id": name, "name": name.title(), "hex": "#112233", "kind": "opaque", "confirmed": True}
        for name in ("navy", "oak", "dark-oak", "dark-blue")
    ]}
    parts = []
    for entry in packaged.parts.values():
        parts.append({"id": entry.id, "name": entry.name, "category": entry.category,
                      "sizes": copy.deepcopy(list(entry.sizes)), "pack": 1, "source": "a shop",
                      "confirmed": True})
    parts.append({"id": "led-3v-cool-white-test", "name": "x", "category": "lamp", "sizes": [],
                  "pack": 1, "source": "a shop", "confirmed": True})
    return parse_catalogues(filaments, {"schema_version": 1, "parts": parts})


def _kit10():
    """The kit test's book nook as schema 10, its circuit stated."""

    block, prose = _schema_8_kit(_tree_block())
    block["schema_version"] = 10
    for geometry in block["geometries"]:
        del geometry["wall_min_mm"]
    block["electrical"] = {
        "parts": [{"id": "box", "bought": "battery-box-2aa-switch", "role": "source"},
                  {"id": "led", "bought": "led-3v-cool-white", "role": "load"}],
        "paths": [{"id": "nook-light", "load": "led", "current_ma": 10, "sequence": ["box", "led", "box"]}],
        "supply_v": {"min": 2.0, "nominal": 3.0, "max": 3.2},
        "standby_ma": 0, "runtime_h": 20,
        "switch_logic": "The battery box's slide switch.",
        "assembled_by": "buyer", "joins": "solderless", "batteries_included": False,
    }
    return block, prose


class KitElectricalTest(unittest.TestCase):
    def _parse(self, block, prose):
        return parse_design_contract(_contract_text(block, prose=prose), catalogues=_kit_catalogues())

    def test_a_kit_states_the_circuit_of_its_tree(self):
        block, prose = _kit10()
        contract = self._parse(block, prose)
        snapshot = contract.kit_catalogue()
        self.assertIn("steel-pin-1.5x29.5", snapshot["bought_parts"])
        self.assertIn("battery-box-2aa-switch", snapshot["bought_parts"])
        self.assertIn("navy", snapshot["filaments"])

    def test_a_kit_circuit_names_every_wired_entry_and_no_stranger(self):
        block, prose = _kit10()
        block["electrical"]["parts"].append({"id": "cells", "bought": "cell-aaa", "role": "source"})
        block["electrical"]["paths"].append({"id": "spare", "load": "led", "current_ma": 1,
                                             "sequence": ["cells", "led", "cells"]})
        with self.assertRaises(ContractError) as caught:
            self._parse(block, prose)
        self.assertIn("electrical part cells (cell-aaa) is no Bought Part of the Assembly Tree",
                      str(caught.exception))
        block, prose = _kit10()
        block["electrical"]["parts"] = [block["electrical"]["parts"][0],
                                        {"id": "lamp", "bought": "resistor-75r", "role": "load"}]
        block["electrical"]["paths"][0].update(load="lamp", sequence=["box", "lamp", "box"])
        with self.assertRaises(ContractError) as caught:
            self._parse(block, prose)
        self.assertIn("P03-ball-led (led-3v-cool-white) is a lamp in no electrical part", str(caught.exception))



def _wired_tree():
    """The kit test's book nook lit by two AAA cells through a soldered lever
    switch: a switch is a Wired Part as its catalogue entry has a lead diameter."""

    block = _tree_block()
    tree = block["assembly_tree"]
    tree["parts"][-1] = {"id": "P04-cells", "bought": "cell-aaa"}
    tree["parts"].append({"id": "P05-switch", "bought": "microswitch-mini-lever"})
    battery = next(item for item in tree["steps"] if item["id"] == "S06-case-battery")
    battery["inputs"] = [{"id": "S05-case-lamp"}, {"id": "P04-cells", "direction": [0, 0, 1], "count": 2},
                         {"id": "P05-switch", "direction": [0, 0, 1]}]
    wiring = tree["steps"][-1]
    wiring.update(lamps=["P03-ball-led", "P05-switch"], method="solder",
                  text="Solder the LED's leads through the switch to the cells.")
    tree["components"][0]["parts"] = ["A01-case-shell", "P03-ball-led", "P04-cells", "P05-switch"]
    tree["checks"][0]["parts"] = ["P03-ball-led", "P04-cells", "P05-switch"]
    return block


class WiredPartTreeTest(unittest.TestCase):
    def _parse(self, block):
        return parse_design_contract(_contract_text(block), catalogues=_kit_catalogues())

    def _refused(self, block):
        with self.assertRaises(ContractError) as caught:
            self._parse(block)
        return str(caught.exception)

    def test_a_soldered_switch_and_cells_seal_in_a_kit(self):
        contract = self._parse(_wired_tree())
        wiring = contract.assembly_tree.section["steps"][-1]
        self.assertEqual((wiring["method"], wiring["lamps"]), ("solder", ["P03-ball-led", "P05-switch"]))
        self.assertEqual(contract.kit_catalogue()["bought_parts"]["cell-aaa"]["category"], "cell")

    def test_only_a_leads_step_names_a_method_of_its_three(self):
        block = _wired_tree()
        block["assembly_tree"]["steps"][-1]["method"] = "glue"
        self.assertIn("method must be one of twist, solder, connector", self._refused(block))
        block = _wired_tree()
        block["assembly_tree"]["steps"][0]["method"] = "solder"
        self.assertIn("assembly_tree.steps[0].method belongs to a leads step only", self._refused(block))

    def test_a_part_without_leads_is_no_wired_part(self):
        block = _wired_tree()
        block["assembly_tree"]["parts"][-1]["bought"] = "contact-aaa-bridge"
        self.assertIn("names 'P05-switch', which is no Wired Part", self._refused(block))

    def test_a_check_step_needs_a_lamp_and_its_power(self):
        block = _wired_tree()
        block["assembly_tree"]["checks"][0]["parts"] = ["P03-ball-led", "P05-switch"]
        self.assertIn("names at least one lamp and one power or cell part", self._refused(block))


if __name__ == "__main__":
    unittest.main()
