"""ADR 0092: a schema 7 Design Contract declares its Assembly Tree."""

import copy
import json
import unittest

from workshop.errors import ContractError
from workshop.wish.catalogues import parse_catalogues
from workshop.wish.design_contract import parse_design_contract
from tests.wish.test_design_contract import _contract_text


def _catalogues():
    """A deterministic stand-in for the owner's catalogues."""

    filaments = {"schema_version": 1, "filaments": [
        {"id": name, "name": name.title(), "hex": "#112233", "kind": "opaque", "confirmed": True}
        for name in ("navy", "oak", "dark-oak", "dark-blue")
    ]}
    def part(identifier, category, confirmed=True):
        return {"id": identifier, "name": identifier, "category": category, "sizes": [],
                "pack": 10 if confirmed else None, "source": "a shop" if confirmed else None,
                "confirmed": confirmed}
    bought = {"schema_version": 1, "parts": [
        part("steel-pin-1.5x29.5", "fastener"),
        part("clear-jar-6x7", "container"),
        part("led-3v-cool-white", "lamp"),
        part("battery-box-2aa-switch", "power", confirmed=False),
        part("tweezers", "tool"),
        part("foam-tape", "consumable"),
    ]}
    return parse_catalogues(filaments, bought)


def _tree_block():
    """A small book nook kit: a case with a lamp and battery box, a cabinet
    of five Parts with a spine strip and a pin hinge, and two desks."""

    return {
        "schema_version": 7,
        "title": "Kit Nook",
        "inventor": "rowan-vale",
        "envelope_mm": [140, 166, 230],
        "references": [
            {"file": "ref-01-nook.png", "shows": "assembly", "camera": [-60, 20]},
            {"file": "ref-02-case.png", "shows": "geometry:case", "camera": [-90, 0]},
            {"file": "ref-03-cabinet.png", "shows": "geometry:cabinet", "camera": [-90, 15]},
            {"file": "ref-04-desk.png", "shows": "geometry:desk", "camera": [-90, 30]},
        ],
        "geometries": [
            {"id": "case", "name": "Case", "count": 1, "extents_mm": [132, 166, 230], "wall_min_mm": 0.8},
            {"id": "cabinet", "name": "Cabinet", "count": 1, "extents_mm": [31, 21, 30], "wall_min_mm": 1.2},
            {"id": "desk", "name": "Student desk", "count": 2, "extents_mm": [38, 15, 20], "wall_min_mm": 0.8},
        ],
        "requirements": [
            {"id": "R01", "scope": "assembly", "text": "A navy stone box holds a cabinet and two desks."},
            {"id": "R02", "scope": "geometry:cabinet", "text": "The cabinet's door opens on a pin."},
        ],
        "interfaces": [
            {"id": "cabinet-seat", "kind": "static", "components": ["case", "cabinet"],
             "text": "The cabinet's two pegs sit in the case floor's sockets."},
            {"id": "desk-seat", "kind": "static", "components": ["case", "desk"],
             "text": "Each desk's legs sit in the case floor's sockets."},
        ],
        "print": {
            "stocks": {"paper": {"name": "matte couche 120 gsm", "caliper_mm": 0.10}},
            "art": [
                {"file": "print-01-spines.png", "shows": "A row of green book spines."},
                {"file": "print-02-book.png", "shows": "An open spell book."},
            ],
            "pieces": [
                {"id": "M01-spine-strip", "art": "print-01-spines.png", "stock": "paper", "way": "flat",
                 "on": "B01-cabinet-carcass", "where": "The lower shelf's back recess.", "size_mm": [20, 9]},
                {"id": "M02-desk-book", "art": "print-02-book.png", "stock": "paper", "way": "flat",
                 "on": "C01-desk-body", "where": "The desk top's recess.", "size_mm": [10, 7], "count": 2},
            ],
        },
        "assembly_tree": {
            "parts": [
                {"id": "A01-case-shell", "name": "Case shell", "filament": "navy", "form": "panel"},
                {"id": "B01-cabinet-carcass", "name": "Cabinet carcass", "filament": "dark-oak", "form": "panel"},
                {"id": "B02-cabinet-door", "name": "Cabinet door", "filament": "dark-oak", "form": "panel"},
                {"id": "C01-desk-body", "name": "Student desk", "filament": "oak", "form": "panel"},
                {"id": "D01-inkwell", "name": "Inkwell", "filament": "dark-blue", "form": "solid"},
                {"id": "P01-hinge-pin", "bought": "steel-pin-1.5x29.5"},
                {"id": "P02-jar", "bought": "clear-jar-6x7"},
                {"id": "P03-ball-led", "bought": "led-3v-cool-white"},
                {"id": "P04-battery-box", "bought": "battery-box-2aa-switch"},
            ],
            "steps": [
                {"id": "S01-cabinet-shelf", "output": "Cabinet with jar and inkwell", "count": 1,
                 "joint": "peg-socket", "text": "Press the jar and the inkwell onto the upper shelf.",
                 "inputs": [{"id": "B01-cabinet-carcass"},
                            {"id": "P02-jar", "direction": [0, 1, 0]},
                            {"id": "D01-inkwell", "direction": [0, 1, 0]}]},
                {"id": "S02-cabinet-spines", "output": "Cabinet with book spines", "count": 1,
                 "joint": "paper", "text": "Lay the spine strip in the lower shelf's recess.",
                 "inputs": [{"id": "S01-cabinet-shelf"}, {"id": "M01-spine-strip", "direction": [0, 1, 0]}]},
                {"id": "S03-hang-door", "output": "Cabinet", "count": 1, "joint": "pin-hinge",
                 "error_prone": True, "text": "Set the door between the lugs and push the pin down.",
                 "inputs": [{"id": "S02-cabinet-spines"},
                            {"id": "B02-cabinet-door", "direction": [1, 0, 0]},
                            {"id": "P01-hinge-pin", "direction": [0, 0, -1]}]},
                {"id": "S04-dress-desk", "output": "Desk with book", "count": 2, "joint": "paper",
                 "text": "Lay the book in the desk top's recess.",
                 "inputs": [{"id": "C01-desk-body"}, {"id": "M02-desk-book", "direction": [0, 0, -1]}]},
                {"id": "S05-case-lamp", "output": "Case with lamp", "count": 1, "joint": "tab-slot",
                 "text": "Push the LED up its bore from below.",
                 "inputs": [{"id": "A01-case-shell"}, {"id": "P03-ball-led", "direction": [0, 0, 1]}],
                 "leads": [{"lamp": "P03-ball-led", "route_mm": [[-5, 58, 37], [-5, 58, 3]],
                            "exit": "Out of the hole under the dais."}]},
                {"id": "S06-case-battery", "output": "Case", "count": 1, "joint": "foam-tape",
                 "text": "Stick the battery box in its cradle.",
                 "inputs": [{"id": "S05-case-lamp"}, {"id": "P04-battery-box", "direction": [0, 0, 1]}]},
                {"id": "S07-furniture", "output": "Furnished room", "count": 1, "joint": "peg-socket",
                 "text": "Set the cabinet and both desks on their sockets.",
                 "inputs": [{"id": "S06-case-battery"},
                            {"id": "S03-hang-door", "direction": [0, 0, -1]},
                            {"id": "S04-dress-desk", "direction": [0, 0, -1], "count": 2}]},
                {"id": "S08-wiring", "output": "Night Nook", "count": 1, "joint": "leads",
                 "lamps": ["P03-ball-led"], "text": "Join the LED's leads to the battery box.",
                 "inputs": [{"id": "S07-furniture"}]},
            ],
            "components": [
                {"geometry": "case", "parts": ["A01-case-shell", "P03-ball-led", "P04-battery-box"]},
                {"geometry": "cabinet", "parts": ["B01-cabinet-carcass", "B02-cabinet-door",
                                                  "D01-inkwell", "P01-hinge-pin", "P02-jar"]},
                {"geometry": "desk", "parts": ["C01-desk-body"]},
            ],
            "checks": [
                {"id": "light-test", "parts": ["P03-ball-led", "P04-battery-box"],
                 "text": "Join the LED to the battery box, switch on, then take them apart."},
            ],
            "materials": ["tweezers", "foam-tape"],
        },
    }


def _step(block, identifier):
    return next(item for item in block["assembly_tree"]["steps"] if item["id"] == identifier)


def _component(block, geometry):
    return next(item for item in block["assembly_tree"]["components"] if item["geometry"] == geometry)


class AssemblyTreeTest(unittest.TestCase):
    def _parse(self, block):
        return parse_design_contract(_contract_text(block), catalogues=_catalogues())

    def _refused(self, block):
        with self.assertRaises(ContractError) as caught:
            self._parse(block)
        return str(caught.exception)

    def test_a_schema_7_contract_seals_its_tree_verbatim(self):
        block = _tree_block()
        contract = self._parse(block)
        self.assertEqual(contract.schema_version, 7)
        self.assertEqual(contract.to_dict()["assembly_tree"], block["assembly_tree"])
        self.assertEqual(contract.to_dict()["print"], block["print"])
        self.assertEqual(contract.assembly_tree.root, "S08-wiring")
        self.assertEqual(contract.assembly_tree.component_of["P01-hinge-pin"], "cabinet")
        self.assertEqual(contract.assembly_tree.component_of["C01-desk-body"], "desk")
        # The unconfirmed seed the tree uses is named for the owner.
        self.assertEqual(contract.assembly_tree.unconfirmed, ("bought-parts.json:battery-box-2aa-switch",))
        # Schema 7 keeps the cameras and the Interface text.
        self.assertEqual(contract.references[0].camera, (-60.0, 20.0))
        self.assertTrue(all(item.text for item in contract.interfaces))

    def test_the_catalogue_snapshot_holds_every_entry_the_tree_uses(self):
        contract = self._parse(_tree_block())
        snapshot = contract.kit_catalogue()
        self.assertEqual(sorted(snapshot["filaments"]), ["dark-blue", "dark-oak", "navy", "oak"])
        self.assertEqual(snapshot["filaments"]["navy"]["hex"], "#112233")
        # Bought Parts and the material list, never an unused entry.
        self.assertEqual(sorted(snapshot["bought_parts"]), [
            "battery-box-2aa-switch", "clear-jar-6x7", "foam-tape", "led-3v-cool-white",
            "steel-pin-1.5x29.5", "tweezers"])
        self.assertEqual(snapshot["bought_parts"]["led-3v-cool-white"]["category"], "lamp")
        self.assertFalse(snapshot["bought_parts"]["battery-box-2aa-switch"]["confirmed"])
        # A copy: changing it changes nothing the contract holds.
        snapshot["filaments"].clear()
        self.assertTrue(contract.kit_catalogue()["filaments"])
        # Older schemas seal none.
        block = _tree_block()
        block["schema_version"] = 6
        del block["assembly_tree"]
        for piece in block["print"]["pieces"]:
            piece["on"] = "cabinet"
            piece["id"] = piece["id"].split("-", 1)[1]
        self.assertIsNone(parse_design_contract(_contract_text(block)).kit_catalogue())

    def test_print_sheets_and_guides_are_optional_at_schema_7(self):
        block = _tree_block()
        del block["print"]
        tree = block["assembly_tree"]
        # Without paper the desks are single Parts and the cabinet skips its strip.
        _step(block, "S03-hang-door")["inputs"][0]["id"] = "S01-cabinet-shelf"
        tree["steps"] = [item for item in tree["steps"] if item["id"] not in ("S02-cabinet-spines", "S04-dress-desk")]
        _step(block, "S07-furniture")["inputs"][2] = {"id": "C01-desk-body", "direction": [0, 0, -1], "count": 2}
        contract = self._parse(block)
        self.assertIsNone(contract.print_sheets)
        self.assertIsNone(contract.guides)

    def test_schema_7_needs_its_tree(self):
        block = _tree_block()
        del block["assembly_tree"]
        self.assertIn("assembly_tree must be an object", self._refused(block))

    def test_older_schemas_refuse_a_tree_and_never_read_the_catalogues(self):
        block = _tree_block()
        block["schema_version"] = 6
        message = self._refused(block)
        self.assertIn("assembly_tree needs schema_version 7", message)
        del block["assembly_tree"]
        # Schema 6 never reads a catalogue, however broken.
        with self.assertRaises(ContractError) as caught:
            parse_design_contract(_contract_text(block), catalogues=None)
        self.assertNotIn("catalogue", str(caught.exception))
        # ... and its Print Pieces still land on Unique Geometries.
        self.assertIn("on must name a Unique Geometry", str(caught.exception))

    def test_a_part_in_two_components_is_refused(self):
        block = _tree_block()
        _component(block, "desk")["parts"].append("D01-inkwell")
        self.assertIn("D01-inkwell is in two Components: cabinet and desk", self._refused(block))

    def test_a_non_contiguous_component_is_refused(self):
        block = _tree_block()
        _component(block, "cabinet")["parts"].remove("D01-inkwell")
        _component(block, "case")["parts"].append("D01-inkwell")
        message = self._refused(block)
        self.assertIn("Component cabinet is not one contiguous subtree", message)
        self.assertIn("also holds D01-inkwell", message)
        self.assertIn("Component case is not one contiguous subtree", message)

    def test_a_part_in_no_component_is_refused(self):
        block = _tree_block()
        _component(block, "cabinet")["parts"].remove("P02-jar")
        message = self._refused(block)
        self.assertIn("P02-jar belongs to no Component", message)

    def test_every_geometry_has_one_component_of_its_count(self):
        block = _tree_block()
        block["geometries"][2]["count"] = 3
        self.assertIn("made 2 time(s) per toy, but the geometry's count is 3", self._refused(block))
        block = _tree_block()
        block["assembly_tree"]["components"].pop()
        message = self._refused(block)
        self.assertIn("Unique Geometry desk has no Component", message)
        self.assertIn("C01-desk-body belongs to no Component", message)

    def test_a_duplicate_id_or_mnemonic_is_refused(self):
        block = _tree_block()
        block["assembly_tree"]["parts"][2]["id"] = "B01-cabinet-leaf"
        self.assertIn("repeats the id B01 (B01-cabinet-carcass)", self._refused(block))
        block = _tree_block()
        block["assembly_tree"]["parts"].append({"id": "C02-inkwell", "name": "Inkwell", "filament": "oak", "form": "solid"})
        self.assertIn("repeats the mnemonic 'inkwell' (D01-inkwell)", self._refused(block))
        # A step's mnemonic counts too.
        block = _tree_block()
        _step(block, "S08-wiring")["id"] = "S08-cabinet-door"
        self.assertIn("repeats the mnemonic 'cabinet-door'", self._refused(block))

    def test_a_colour_outside_the_catalogue_is_refused(self):
        block = _tree_block()
        block["assembly_tree"]["parts"][0]["filament"] = "sparkle-purple"
        message = self._refused(block)
        self.assertIn("filament 'sparkle-purple' is not in the filament catalogue", message)
        self.assertIn("owner's approval", message)

    def test_one_letter_is_one_filament(self):
        block = _tree_block()
        block["assembly_tree"]["parts"][2]["filament"] = "oak"
        self.assertIn("letter B is dark-oak", self._refused(block))

    def test_printed_letters_are_every_letter_but_m_n_p_and_s(self):
        # Owner decision 2026-10-23 (Q27): not only A-K, one letter per filament.
        renames = {"D01-inkwell": "Z01-inkwell", "C01-desk-body": "L01-desk-body"}
        text = json.dumps(_tree_block())
        for old, new in renames.items():
            text = text.replace(old, new)
        contract = self._parse(json.loads(text))
        self.assertEqual(contract.assembly_tree.component_of["Z01-inkwell"], "cabinet")
        for letter in "MNS":
            block = json.loads(json.dumps(_tree_block()).replace("D01-inkwell", "%s07-inkwell" % letter))
            self.assertIn("any letter but M, N, P and S", self._refused(block))

    def test_one_filament_is_one_letter(self):
        block = _tree_block()
        block["assembly_tree"]["parts"][4]["filament"] = "oak"  # D01-inkwell, beside C01's oak
        self.assertIn("oak already has letter C (C01-desk-body), so D01-inkwell cannot use D",
                      self._refused(block))

    def test_every_printed_part_is_a_panel_or_a_solid(self):
        # Owner decision Q33, 2026-10-26: flat panels joined by tab and slot,
        # small round or 3D props printed whole.
        contract = self._parse(_tree_block())
        self.assertEqual(contract.assembly_tree.panel_mm, 2.0)
        block = _tree_block()
        del block["assembly_tree"]["parts"][0]["form"]
        self.assertIn("parts[0]: a printed Part is {id, name, filament, form}", self._refused(block))
        block = _tree_block()
        block["assembly_tree"]["parts"][0]["form"] = "box"
        self.assertIn("parts[0].form must be panel", self._refused(block))
        # A Bought Part takes no form: it is not printed.
        block = _tree_block()
        block["assembly_tree"]["parts"][5]["form"] = "solid"
        self.assertIn("parts[5]: a Bought Part is exactly {id, bought}", self._refused(block))

    def test_a_panel_is_the_toys_panel_thickness_unless_it_says_why(self):
        # Owner decision Q34, 2026-10-26: one standard thickness, default 2.0 mm.
        block = _tree_block()
        block["assembly_tree"]["panel_mm"] = 1.6
        self.assertEqual(self._parse(block).assembly_tree.panel_mm, 1.6)
        door = block["assembly_tree"]["parts"][2]
        door["thickness_mm"] = 1.6
        self._parse(block)
        door["thickness_mm"] = 3.0
        self.assertIn("B02-cabinet-door", self._refused(block))
        self.assertIn("is a 3 mm panel, but the toy's panels are 1.6 mm (panel_mm): a panel of "
                      "another thickness states its thickness_reason", self._refused(block))
        door["thickness_reason"] = "The door carries a 1 mm arch moulding in relief."
        contract = self._parse(block)
        self.assertEqual(contract.to_dict()["assembly_tree"]["parts"][2]["thickness_mm"], 3.0)
        # A reason needs a thickness it explains.
        door["thickness_mm"] = 1.6
        self.assertIn("thickness_reason explains nothing", self._refused(block))
        del door["thickness_mm"]
        self.assertIn("thickness_reason explains a thickness_mm it does not state", self._refused(block))

    def test_a_solid_takes_no_panel_thickness_and_panel_mm_is_bounded(self):
        block = _tree_block()
        block["assembly_tree"]["parts"][4]["thickness_mm"] = 2.0  # D01-inkwell is a solid
        self.assertIn("parts[4] is a solid: thickness_mm and thickness_reason belong to a panel",
                      self._refused(block))
        for bad in (0.4, 12, True, "2.0"):
            block = _tree_block()
            block["assembly_tree"]["panel_mm"] = bad
            self.assertIn("assembly_tree.panel_mm must be the toy's one panel thickness",
                          self._refused(block))
        block = _tree_block()
        block["assembly_tree"]["parts"][2]["thickness_mm"] = 0.5
        block["assembly_tree"]["parts"][2]["thickness_reason"] = "Thin."
        self.assertIn("parts[2].thickness_mm must be 0.8 to 10 mm", self._refused(block))

    def test_a_lamp_is_tested_in_a_check_step_first(self):
        block = _tree_block()
        del block["assembly_tree"]["checks"]
        self.assertIn("P03-ball-led is a lamp in no Check Step", self._refused(block))
        block = _tree_block()
        check = block["assembly_tree"]["checks"][0]
        check["parts"] = ["P03-ball-led"]
        self.assertIn("names at least one of each", self._refused(block))
        check["parts"] = ["P03-ball-led", "P04-battery-box", "P02-jar"]
        self.assertIn("P02-jar', which is no lamp or power Bought Part", self._refused(block))
        check["parts"] = ["P03-ball-led", "P04-battery-box"]
        check["id"] = "case-shell"
        self.assertIn("repeats the mnemonic 'case-shell'", self._refused(block))
        check["id"] = "light-test"
        check["text"] = ""
        self.assertIn("checks[0].text must be one short English instruction", self._refused(block))
        del check["text"]
        self.assertIn("checks[0] must be exactly {id, text, parts}", self._refused(block))

    def test_a_bought_part_outside_the_catalogue_is_refused(self):
        block = _tree_block()
        block["assembly_tree"]["parts"][5]["bought"] = "brass-hinge"
        message = self._refused(block)
        self.assertIn("bought 'brass-hinge' is not in the Bought Part catalogue", message)

    def test_tools_and_consumables_stay_in_the_material_list(self):
        block = _tree_block()
        block["assembly_tree"]["parts"][5]["bought"] = "tweezers"
        self.assertIn("tools and consumables go in assembly_tree.materials", self._refused(block))
        block = _tree_block()
        block["assembly_tree"]["materials"] = ["clear-jar-6x7", "glitter"]
        message = self._refused(block)
        self.assertIn("'clear-jar-6x7', a container", message)
        self.assertIn("'glitter', which is not in the Bought Part catalogue", message)

    def test_a_print_piece_on_naming_nothing_is_refused(self):
        block = _tree_block()
        block["print"]["pieces"][0]["on"] = "cabinet"
        self.assertIn("M01-spine-strip.on 'cabinet' names nothing that exists", self._refused(block))
        block["print"]["pieces"][0]["on"] = "B09-shelf"
        self.assertIn("'B09-shelf' names nothing that exists", self._refused(block))

    def test_a_print_piece_may_land_on_a_bought_part_or_a_sub_assembly(self):
        block = _tree_block()
        block["print"]["pieces"][0]["on"] = "P02-jar"
        self.assertIsNotNone(self._parse(block).assembly_tree)
        block["print"]["pieces"][0]["on"] = "S01-cabinet-shelf"
        self.assertIsNotNone(self._parse(block).assembly_tree)

    def test_a_print_piece_applied_before_its_host_is_refused(self):
        block = _tree_block()
        block["print"]["pieces"][0]["on"] = "B02-cabinet-door"
        self.assertIn("applied in S02-cabinet-spines, before its host B02-cabinet-door", self._refused(block))
        block["print"]["pieces"][0]["on"] = "S02-cabinet-spines"
        self.assertIn("before its host S02-cabinet-spines", self._refused(block))

    def test_a_print_piece_is_applied_in_a_paper_step_as_often_as_printed(self):
        block = _tree_block()
        _step(block, "S02-cabinet-spines")["joint"] = "tab-slot"
        self.assertIn("whose joint is tab-slot, not paper", self._refused(block))
        block = _tree_block()
        block["print"]["pieces"][1]["count"] = 1
        self.assertIn("M02-desk-book prints 1 copy, but the tree applies it 2 times", self._refused(block))

    def test_schema_7_print_piece_ids_take_the_part_form(self):
        block = _tree_block()
        block["print"]["pieces"][0]["id"] = "spine-strip"
        self.assertIn("must look like M01-<kebab-case mnemonic>", self._refused(block))

    def test_counts_agree_down_the_tree(self):
        block = _tree_block()
        _step(block, "S04-dress-desk")["count"] = 1
        self.assertIn("S04-dress-desk.count is 1, but S07-furniture takes 2 of it", self._refused(block))
        block = _tree_block()
        _step(block, "S08-wiring")["count"] = 2
        self.assertIn("S08-wiring is the finished toy, so it is made once", self._refused(block))

    def test_every_part_and_step_is_used_exactly_once(self):
        block = _tree_block()
        _step(block, "S07-furniture")["inputs"].pop(1)
        self.assertIn("S03-hang-door's Sub-assembly is used by no later step", self._refused(block))
        block = _tree_block()
        block["assembly_tree"]["parts"].append({"id": "D02-quill", "name": "Quill", "filament": "dark-blue", "form": "solid"})
        self.assertIn("D02-quill is in no Assembly Step", self._refused(block))
        block = _tree_block()
        _step(block, "S08-wiring")["inputs"].append({"id": "D01-inkwell"})
        self.assertIn("'D01-inkwell' is already an input of S01-cabinet-shelf", self._refused(block))
        block = _tree_block()
        _step(block, "S01-cabinet-shelf")["inputs"].append({"id": "S03-hang-door", "direction": [0, 0, 1]})
        self.assertIn("is no Part, Print Piece or earlier step", self._refused(block))

    def test_steps_follow_manual_order(self):
        block = _tree_block()
        _step(block, "S01-cabinet-shelf")["id"] = "S09-cabinet-shelf"
        _step(block, "S02-cabinet-spines")["inputs"][0]["id"] = "S09-cabinet-shelf"
        message = self._refused(block)
        self.assertIn("steps[1]: step numbers rise in Manual order, and S02-cabinet-spines follows S09", message)

    def test_each_moving_input_has_one_straight_direction(self):
        block = _tree_block()
        del _step(block, "S03-hang-door")["inputs"][2]["direction"]
        self.assertIn("inputs[2].direction must be its one straight insertion direction", self._refused(block))
        block = _tree_block()
        _step(block, "S03-hang-door")["inputs"][1]["direction"] = [0, 0, 0]
        self.assertIn("inputs[1].direction must be", self._refused(block))
        block = _tree_block()
        _step(block, "S03-hang-door")["inputs"][0]["direction"] = [0, 0, 1]
        self.assertIn("inputs[0] takes no direction", self._refused(block))

    def test_joint_kinds_and_their_fields(self):
        block = _tree_block()
        _step(block, "S06-case-battery")["joint"] = "snap"
        self.assertIn("joint must be one of peg-socket, tab-slot, pin-hinge, foam-tape, glue", self._refused(block))
        block = _tree_block()
        _step(block, "S06-case-battery")["joint"] = "glue"
        self.assertIn("glue is a last resort and needs its glue_reason", self._refused(block))
        _step(block, "S06-case-battery")["glue_reason"] = "The box must not come loose in transit."
        self.assertIsNotNone(self._parse(block).assembly_tree)
        block = _tree_block()
        _step(block, "S05-case-lamp")["glue_reason"] = "x"
        self.assertIn("glue_reason belongs to a glue joint only", self._refused(block))
        block = _tree_block()
        _step(block, "S08-wiring")["joint"] = "fold"
        _step(block, "S08-wiring")["inputs"].append({"id": "S07-furniture"})
        message = self._refused(block)
        self.assertIn("a fold step has exactly one input", message)
        self.assertIn("lamps belongs to a leads step only", message)

    def test_a_short_instruction_and_a_boolean_error_mark(self):
        block = _tree_block()
        _step(block, "S01-cabinet-shelf")["text"] = "x" * 201
        self.assertIn("one short English instruction of at most 200", self._refused(block))
        block = _tree_block()
        _step(block, "S03-hang-door")["error_prone"] = "yes"
        self.assertIn("error_prone must be true or false", self._refused(block))

    def test_a_leads_step_sits_above_every_lamp_it_joins(self):
        block = _tree_block()
        _step(block, "S08-wiring")["lamps"] = ["P02-jar"]
        self.assertIn("names 'P02-jar', which is no lamp Bought Part", self._refused(block))
        # A second lamp on each desk, and the leads joined in the case alone,
        # before the desks are placed.
        block = _tree_block()
        block["assembly_tree"]["parts"].append({"id": "P05-desk-lamp", "bought": "led-3v-cool-white"})
        _step(block, "S04-dress-desk")["inputs"].append({"id": "P05-desk-lamp", "direction": [0, 0, -1]})
        _component(block, "desk")["parts"].append("P05-desk-lamp")
        block["assembly_tree"]["checks"][0]["parts"].append("P05-desk-lamp")
        _step(block, "S05-case-lamp")["inputs"].append(
            _step(block, "S06-case-battery")["inputs"][1])
        _step(block, "S06-case-battery").update({
            "joint": "leads", "lamps": ["P03-ball-led", "P05-desk-lamp"],
            "inputs": [{"id": "S05-case-lamp"}]})
        _step(block, "S08-wiring")["lamps"] = ["P03-ball-led", "P05-desk-lamp"]
        message = self._refused(block)
        self.assertIn(
            "S06-case-battery joins the leads of P05-desk-lamp, which is not yet in its "
            "Sub-assembly", message)
        self.assertNotIn("S08-wiring joins", message)
        self.assertNotIn("P03-ball-led, which is not yet", message)
        # Joined at the root, above both lamps, the same tree passes.
        _step(block, "S06-case-battery").update({"joint": "foam-tape"})
        del _step(block, "S06-case-battery")["lamps"]
        _step(block, "S06-case-battery")["inputs"] = [
            {"id": "S05-case-lamp"}, _step(block, "S05-case-lamp")["inputs"].pop()]
        self.assertIsNotNone(self._parse(block).assembly_tree)

    def test_an_enclosed_lead_declares_its_route(self):
        block = _tree_block()
        _step(block, "S05-case-lamp")["leads"][0]["route_mm"] = [[0, 0, 0]]
        self.assertIn("route_mm must be two or more [x, y, z] points", self._refused(block))
        block = _tree_block()
        del _step(block, "S05-case-lamp")["leads"][0]["exit"]
        self.assertIn("must be exactly {lamp, route_mm, exit}", self._refused(block))
        block = _tree_block()
        _step(block, "S01-cabinet-shelf")["leads"] = [
            {"lamp": "P03-ball-led", "route_mm": [[0, 0, 0], [0, 0, 1]], "exit": "Out the back."}]
        self.assertIn("lamp P03-ball-led is not in this step's Sub-assembly", self._refused(block))

    def test_every_failure_is_named_at_once(self):
        block = _tree_block()
        block["assembly_tree"]["parts"][0]["filament"] = "sparkle-purple"
        block["assembly_tree"]["parts"][5]["bought"] = "brass-hinge"
        block["requirements"][0]["id"] = "bad"
        message = self._refused(block)
        for needle in ("sparkle-purple", "brass-hinge", "requirements[0].id"):
            self.assertIn(needle, message)

    def test_a_run_may_seal_schema_7_now_its_manual_exists(self):
        # Every schema 7 gate is wired: the tree gates (#136) and the Manual (#137).
        self._parse(_tree_block()).check_sealable()
        block = _tree_block()
        block["schema_version"] = 6
        del block["assembly_tree"]
        for piece in block["print"]["pieces"]:
            piece["on"] = "cabinet"
            piece["id"] = piece["id"].split("-", 1)[1]
        parse_design_contract(_contract_text(block)).check_sealable()

    def test_the_packaged_catalogues_hold_every_seed_unconfirmed(self):
        from workshop.wish.catalogues import load_catalogues

        catalogues = load_catalogues()
        self.assertTrue(catalogues.filaments)
        self.assertTrue(catalogues.parts)
        # Seeds are the owner's to confirm: none claims a supplier fact.
        for entry in list(catalogues.filaments.values()) + list(catalogues.parts.values()):
            self.assertFalse(entry.confirmed, entry.id)
        for entry in catalogues.parts.values():
            self.assertIsNone(entry.pack, entry.id)
            self.assertIsNone(entry.source, entry.id)
        # The packaged catalogues validate the example as well as the fake.
        contract = parse_design_contract(_contract_text(_tree_block()))
        self.assertIn("filaments.json:navy", contract.assembly_tree.unconfirmed)
        # Every lamp seed gives the lead diameter Make's lead-route gate sweeps.
        for entry in catalogues.parts.values():
            if entry.category == "lamp":
                self.assertIn("lead diameter", [size["what"] for size in entry.sizes], entry.id)


def _schema_8_kit(block):
    """The same kit as schema 8 (ADR 0093): each geometry names its prose
    section and one Guide Image names every geometry."""

    block["schema_version"] = 8
    for geometry in block["geometries"]:
        geometry["prose_sections"] = [geometry["name"]]
    block["guides"] = [{"file": "guide-01-views.png", "shows": "Every Component from two more sides.",
                        "geometries": [item["id"] for item in block["geometries"]]}]
    prose = "# Kit Nook\n\n" + "".join(
        "### %s\n\nThe %s, described.\n\n" % (item["name"], item["name"].lower())
        for item in block["geometries"])
    return block, prose


class SchemaEightKitTest(unittest.TestCase):
    """ADR 0093: schema 8 keeps every schema 7 feature, with the tree optional."""

    def test_a_schema_8_kit_seals_its_tree_and_prose(self):
        block, prose = _schema_8_kit(_tree_block())
        contract = parse_design_contract(_contract_text(block, prose=prose), catalogues=_catalogues())
        contract.check_sealable()
        self.assertEqual(contract.schema_version, 8)
        self.assertEqual(contract.to_dict()["assembly_tree"], block["assembly_tree"])
        self.assertEqual(contract.to_dict()["print"], block["print"])
        self.assertIsNotNone(contract.kit_catalogue())
        self.assertEqual([item.heading for item in contract.prose], ["Case", "Cabinet", "Student desk"])

    def test_a_schema_8_toy_without_a_tree_reads_no_catalogue(self):
        block, prose = _schema_8_kit(_tree_block())
        del block["assembly_tree"]
        for piece in block["print"]["pieces"]:
            piece["on"] = "cabinet"
            piece["id"] = piece["id"].split("-", 1)[1]
        contract = parse_design_contract(_contract_text(block, prose=prose), catalogues=None)
        self.assertIsNone(contract.assembly_tree)
        self.assertIsNone(contract.kit_catalogue())
        # Without a tree a piece id is a schema 6 id, not a Part id.
        block, prose = _schema_8_kit(_tree_block())
        del block["assembly_tree"]
        with self.assertRaises(ContractError):
            parse_design_contract(_contract_text(block, prose=prose), catalogues=None)


if __name__ == "__main__":
    unittest.main()
