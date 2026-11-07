"""ADR 0095 amendment (2026-11-01): a powered toy's Bought Parts in its model.

The run-local ``make-round/scripts/bought_model.py`` seats one body per
Bought Part in the mount envelopes of Make's power report, writes the
electrical pictures and the Electrical assembly text, and the host checks
the sealed result before Make is accepted without rebuilding any geometry.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import math
import shutil
import tempfile
import types
import unittest
from pathlib import Path

from workshop.artifacts import build_artifact_manifest
from workshop.errors import ContractError
from workshop.make.assembly_package import (
    IDENTITY_TRANSFORM,
    missing_production_parts,
    occurrences_missing_colour_names,
    read_assembly_package,
)
from workshop.make.bought_model import draws_bought_parts, expected_bodies, verify_made_bought
from workshop.runtime.package_data import product_run_domain_skill_roots
from workshop.wish.catalogues import load_catalogues
from workshop.wish.design_contract import parse_design_contract
from tests.make.test_assembly_package import quarterhoot_package
from tests.wish.test_design_contract import _PROSE, _contract_text
from tests.wish.test_electrical import _mac_usb, _schema10

TOOL = product_run_domain_skill_roots()["make-round"] / "scripts" / "bought_model.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("bought_model_under_test", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tool = load_tool()
PRODUCT = "products/toy"
MAGENTA = [1.0, 0.0, 1.0, 1.0]


BOARD = [[-12.0, 0.0, 0.0], [12.0, 1.6, 30.0]]


def small_circuit(pcba=True):
    """A USB night light: the buyer's charger, a receptacle, one lever
    switch, one chip resistor and one 5 mm LED, joined by hookup wire."""

    electrical = {
        "parts": [
            {"id": "usb-supply", "role": "source", "external": True},
            {"id": "usb-c", "bought": "usb-c-receptacle-power", "role": "inlet"},
            {"id": "s-half", "bought": "microswitch-mini-lever", "role": "switch"},
            {"id": "r-screen", "bought": "resistor-150r", "role": "controller"},
            {"id": "screen-led", "bought": "led-5mm-amber-diffused", "role": "load"},
            {"id": "wire", "bought": "wire-28awg", "role": "wire"},
        ],
        "paths": [{"id": "screen-light", "load": "screen-led", "current_ma": 20,
                   "sequence": ["usb-supply", "usb-c", "s-half", "r-screen", "screen-led", "usb-supply"]}],
        "supply_v": {"min": 4.4, "nominal": 5.0, "max": 5.25},
        "standby_ma": 0, "runtime_h": None,
        "switch_logic": "Floppy half in closes s-half: the screen glows.",
        "assembled_by": "maker", "joins": "solder", "batteries_included": False,
    }
    if pcba:
        electrical["pcba"] = {"parts": ["usb-c", "r-screen", "screen-led"], "bounds_mm": BOARD}
    return electrical


def sealed(electrical):
    """``(contract dict, kit_catalogue)`` exactly as a Wish seals them."""

    contract = parse_design_contract(_contract_text(_schema10(electrical), prose=_PROSE),
                                     catalogues=load_catalogues())
    return contract.to_dict(), contract.kit_catalogue()


ENVELOPES = {
    "usb-c": ((-5.0, -10.0, 0.0), (5.0, -2.0, 4.0)),
    "s-half": ((10.0, 0.0, 0.0), (24.0, 7.0, 8.0)),
    "r-screen": ((-3.0, 2.0, 5.0), (3.0, 3.0, 8.0)),
    "screen-led": ((-4.0, 3.0, 10.0), (4.0, 13.0, 18.0)),
}
PLACEMENTS = {
    "kind": "bought-placements", "schema_version": 1,
    "parts": {"usb-c": {"facing": "-y"}, "s-half": {"facing": "+z", "hinge": "+x"},
              "r-screen": {"facing": "+y"}, "screen-led": {"facing": "+y"}},
}


def envelope_path(part):
    return "ref/validation/%s-envelope.step" % part


def bounds():
    return {envelope_path(part): box for part, box in ENVELOPES.items()}


def envelopes():
    return {part: envelope_path(part) for part in ENVELOPES}


class PlanTest(unittest.TestCase):
    """The plan is pure: catalogue sizes, envelope bounds and placements."""

    def setUp(self):
        self.contract, self.catalogue = sealed(small_circuit())
        self.electrical = self.contract["electrical"]
        self.parts = self.catalogue["bought_parts"]

    def plan(self, placements=None, boxes=None):
        return tool.plan(self.electrical, self.parts, envelopes(), boxes or bounds(),
                         copy.deepcopy(PLACEMENTS if placements is None else placements))

    def refused(self, **kwargs):
        with self.assertRaises(tool.Refused) as caught:
            self.plan(**kwargs)
        return "; ".join(caught.exception.reasons)

    def test_every_carried_part_and_the_board_get_one_body_seated_in_its_envelope(self):
        planned = self.plan()
        names = [body["name"] for body in planned["bodies"]]
        self.assertEqual(names, ["bought_usb_c", "bought_s_half", "bought_r_screen", "bought_screen_led",
                                 "bought_pcba"])
        self.assertEqual(names, expected_bodies(self.electrical, self.parts))
        receptacle = planned["bodies"][0]
        # Facing -y: it seats against the envelope's +y face, its mouth out.
        self.assertEqual(receptacle["bounds"][1][1], -2.0)
        self.assertAlmostEqual(receptacle["bounds"][1][1] - receptacle["bounds"][0][1], 7.4)
        self.assertEqual([body["on_board"] for body in planned["bodies"]], [True, False, True, True, False])
        self.assertEqual(planned, self.plan(), "the plan is deterministic")

    def test_a_catalogue_part_larger_than_its_sealed_mount_is_refused(self):
        boxes = bounds()
        boxes[envelope_path("s-half")] = ((10.0, 0.0, 0.0), (20.0, 7.0, 8.0))
        self.assertIn("s-half: the lever-switch body is 12.80 along x, its sealed mount envelope only 10.00",
                      self.refused(boxes=boxes))

    def test_a_directional_part_needs_its_facing_and_a_lever_its_hinge(self):
        placements = copy.deepcopy(PLACEMENTS)
        del placements["parts"]["screen-led"]
        placements["parts"]["s-half"] = {"facing": "+z"}
        message = self.refused(placements=placements)
        self.assertIn("screen-led: no facing", message)
        self.assertIn("s-half: a lever switch needs a hinge across its facing", message)

    def test_a_part_without_a_mount_envelope_is_refused(self):
        boxes = bounds()
        del boxes[envelope_path("r-screen")]
        self.assertIn("r-screen: the power report seats it in no mount envelope", self.refused(boxes=boxes))

    def test_the_board_is_drawn_at_the_contract_s_outline_and_never_placed_by_make(self):
        board = self.plan()["bodies"][-1]
        self.assertEqual((board["name"], board["source"], board["envelope"]), ("bought_pcba", "contract", None))
        self.assertEqual(board["bounds"], BOARD)
        self.electrical = sealed(small_circuit(pcba=False))[0]["electrical"]
        self.assertNotIn("bought_pcba", [body["name"] for body in self.plan()["bodies"]])
        placements = dict(copy.deepcopy(PLACEMENTS), pcba={"envelope": "ref/validation/pcba-envelope.step"})
        self.assertIn("the board's outline is the contract's pcba.bounds_mm", tool.check_placements(placements)[0])

    def test_a_route_must_reach_the_bodies_it_joins(self):
        placements = copy.deepcopy(PLACEMENTS)
        placements["routes"] = [{"wire": "wire", "from": "s-half", "to": "pcba",
                                 "points": [[17.0, 3.5, 8.0], [17.0, 3.5, 20.0], [11.5, 1.0, 20.0]]}]
        route = self.plan(placements=placements)["routes"][0]
        self.assertEqual((route["name"], route["form"], route["diameter_mm"]), ("bought_wire_1", "wire", 0.9))
        placements["routes"][0]["points"][-1] = [30.0, 1.0, 20.0]
        self.assertIn("starts or ends 18.00 from pcba", self.refused(placements=placements))
        placements["routes"][0]["wire"] = "s-half"
        self.assertIn("names 's-half', which is no wire part", self.refused(placements=placements))

    def test_a_malformed_placements_file_is_refused_before_planning(self):
        self.assertTrue(tool.check_placements({"kind": "bought-placements", "schema_version": 1,
                                               "parts": {"usb-c": {"facing": "up"}}}))
        self.assertTrue(tool.check_placements({"kind": "bought-placements", "schema_version": 1,
                                               "parts": {"s-half": {"hinge": "sideways"}}}))
        self.assertEqual(tool.check_placements(PLACEMENTS), [])

    # Issue #225: a Bought Part seated square to a tilted face.

    def test_without_a_pose_the_plan_is_the_one_runs_sealed_before_poses(self):
        placements = copy.deepcopy(PLACEMENTS)
        placements["routes"] = [{"wire": "wire", "from": "s-half", "to": "pcba",
                                 "points": [[17.0, 3.5, 8.0], [17.0, 3.5, 20.0], [11.5, 1.0, 20.0]]}]
        planned = self.plan(placements=placements)
        self.assertFalse(any("pose" in body for body in planned["bodies"]))
        # The canonical plan of this fixture before poses existed: a run
        # sealed without one keeps its body list byte for byte.
        self.assertEqual(hashlib.sha256(tool._canonical(planned)).hexdigest(),
                         "c3b7c49f1e0476e258923d2e7effa387168c4ed4d67fa717dcff4e887da0a817")
        self.assertEqual(tool.posed_requests(envelopes(), bounds(), placements), {})

    def test_a_posed_part_is_planned_in_its_own_frame_and_records_its_pose(self):
        placements = copy.deepcopy(PLACEMENTS)
        pose = {"axis": [1, 0, 0], "angle_deg": 30}
        placements["parts"]["screen-led"]["pose"] = pose
        # The world bounding box of the turned envelope is larger than the
        # envelope; in the part's frame it is the envelope itself.
        boxes = bounds()
        boxes[envelope_path("screen-led")] = ((-4.0, 1.0, 8.0), (4.0, 15.0, 20.0))
        requests = tool.posed_requests(envelopes(), boxes, placements)
        self.assertEqual(requests, {"screen-led": (envelope_path("screen-led"), {
            "axis": [1.0, 0.0, 0.0], "angle_deg": 30.0, "centre": [0.0, 8.0, 14.0]})})
        local = {"screen-led": ((-4.0, 3.0, 10.0), (4.0, 13.0, 18.0))}
        planned = tool.plan(self.electrical, self.parts, envelopes(), boxes, placements, local)
        led = next(body for body in planned["bodies"] if body["part"] == "screen-led")
        unposed = next(body for body in self.plan()["bodies"] if body["part"] == "screen-led")
        self.assertEqual(led["pose"], requests["screen-led"][1])
        self.assertEqual({k: v for k, v in led.items() if k != "pose"}, unposed)
        # The frame turns +y (the LED's facing) by 30 degrees about +x.
        facing = tool.to_world(led["pose"], (0.0, 1.0, 0.0), point=False)
        self.assertAlmostEqual(facing[1], math.cos(math.radians(30)))
        self.assertAlmostEqual(facing[2], math.sin(math.radians(30)))
        corner = (1.0, 2.0, 3.0)
        self.assertTrue(all(abs(a - b) < 1e-9 for a, b in zip(
            tool.to_local(led["pose"], tool.to_world(led["pose"], corner)), corner)))

    def test_a_route_end_reaches_a_posed_body_in_its_frame(self):
        placements = copy.deepcopy(PLACEMENTS)
        placements["parts"]["s-half"]["pose"] = {"axis": [0, 0, 1], "angle_deg": 90}
        local = {"s-half": ENVELOPES["s-half"]}
        lever = next(body for body in self.plan()["bodies"] if body["part"] == "s-half")
        # The body's +x end, in its own frame, turns about the centre
        # (17, 3.5, 4) by 90 degrees about +z: to +y in the world.
        end = (lever["bounds"][1][0], 3.5, 4.0)
        frame = {"axis": [0.0, 0.0, 1.0], "angle_deg": 90.0, "centre": [17.0, 3.5, 4.0]}
        world = [round(v, 6) for v in tool.to_world(frame, end)]
        self.assertAlmostEqual(world[0], 17.0)
        self.assertAlmostEqual(world[1], 3.5 + end[0] - 17.0)
        placements["routes"] = [{"wire": "wire", "from": "s-half", "to": "pcba",
                                 "points": [world, [world[0], world[1], 20.0], [11.5, 1.0, 20.0]]}]
        planned = tool.plan(self.electrical, self.parts, envelopes(), bounds(), placements, local)
        self.assertEqual(planned["routes"][0]["from"], "s-half")
        # The same end unturned is no longer on the body.
        placements["routes"][0]["points"][0] = list(end)
        with self.assertRaises(tool.Refused) as caught:
            tool.plan(self.electrical, self.parts, envelopes(), bounds(), placements, local)
        self.assertIn("from s-half", "; ".join(caught.exception.reasons))

    def test_a_malformed_pose_is_refused_before_planning(self):
        for pose in ({"axis": [1, 0, 0]}, {"angle_deg": 30}, {"axis": [1, 0], "angle_deg": 30},
                     {"axis": [0, 0, 0], "angle_deg": 30}, {"axis": [1, 0, 0], "angle_deg": 0},
                     {"axis": [1, 0, 0], "angle_deg": 181}, {"axis": [1, 0, 0], "angle_deg": True},
                     {"axis": ["x", 0, 0], "angle_deg": 30}, {"axis": [1, 0, float("nan")], "angle_deg": 30},
                     {"axis": [1, 0, 0], "angle_deg": 30, "centre": [0, 0, 0]}, [1, 0, 0, 30], "+x30"):
            placements = copy.deepcopy(PLACEMENTS)
            placements["parts"]["usb-c"]["pose"] = pose
            problems = tool.check_placements(placements)
            self.assertEqual(len(problems), 1, pose)
            self.assertIn("parts.usb-c.pose must be {axis: [x, y, z], angle_deg}", problems[0])
        for pose in ({"axis": [1, 0, 0], "angle_deg": 30}, {"axis": [0.0, 1.0, 1.0], "angle_deg": -180}):
            placements = copy.deepcopy(PLACEMENTS)
            placements["parts"]["usb-c"]["pose"] = pose
            self.assertEqual(tool.check_placements(placements), [], pose)

    def test_a_pose_without_its_envelope_read_in_its_frame_or_on_a_wire_is_refused(self):
        placements = copy.deepcopy(PLACEMENTS)
        placements["parts"]["usb-c"]["pose"] = {"axis": [1, 0, 0], "angle_deg": 30}
        placements["parts"]["wire"] = {"pose": {"axis": [1, 0, 0], "angle_deg": 30}}
        message = self.refused(placements=placements)
        self.assertIn("usb-c: its envelope was not read in the pose's frame", message)
        self.assertIn("wire: a wire is drawn along its routes and takes no pose", message)

    # Issue #228: a push switch is its body and a plunger nose.

    def push_switch(self):
        """The circuit with s-half bought as the latching push switch, whose
        catalogue entry states a body and a plunger."""

        electrical = small_circuit()
        next(item for item in electrical["parts"] if item["id"] == "s-half")["bought"] = "switch-push-latching-8x8"
        contract, catalogue = sealed(electrical)
        self.electrical, self.parts = contract["electrical"], catalogue["bought_parts"]
        boxes = bounds()
        boxes[envelope_path("s-half")] = PUSH_ENVELOPE
        return boxes

    def test_a_box_with_a_plunger_is_its_body_and_a_nose_on_its_facing_side(self):
        boxes = self.push_switch()
        placements = copy.deepcopy(PLACEMENTS)
        placements["parts"]["s-half"] = {"facing": "+z"}
        switch = next(body for body in self.plan(placements=placements, boxes=boxes)["bodies"]
                      if body["part"] == "s-half")
        self.assertEqual((switch["form"], switch["size_mm"]), ("box", [8.5, 8.5, 7.5]))
        self.assertEqual(switch["detail"], {"nose_mm": [3.0, 3.0, 5.5]})
        # Seated on the envelope's floor, the nose's tip at 7.5 + 5.5.
        self.assertEqual(switch["bounds"], [[12.25, -0.75, 0.0], [20.75, 7.75, 13.0]])
        placements["parts"]["s-half"] = {"facing": "-z"}
        down = next(body for body in self.plan(placements=placements, boxes=boxes)["bodies"]
                    if body["part"] == "s-half")
        self.assertEqual(down["bounds"], [[12.25, -0.75, 0.0], [20.75, 7.75, 13.0]])
        self.assertEqual(down["seat"][2], 13.0)

    def test_a_box_with_a_plunger_needs_a_facing_and_room_for_its_nose(self):
        boxes = self.push_switch()
        placements = copy.deepcopy(PLACEMENTS)
        placements["parts"]["s-half"] = {}
        self.assertIn("s-half: no facing in measure/bought-placements.json: a box with a plunger",
                      self.refused(placements=placements, boxes=boxes))
        placements["parts"]["s-half"] = {"facing": "+z"}
        boxes[envelope_path("s-half")] = ((12.0, -1.0, 0.0), (21.0, 8.0, 10.0))
        self.assertIn("s-half: the box body and its plunger are 13.00 along z, its sealed mount envelope "
                      "only 10.00", self.refused(placements=placements, boxes=boxes))

    def test_without_a_body_with_plunger_out_size_the_nose_is_the_plunger_s_length(self):
        entry = {"sizes": [{"what": "body", "max_mm": [8.5, 8.5, 7.5]},
                           {"what": "plunger", "max_mm": [3.0, 3.0, 4.0]}]}
        self.assertEqual(tool._plunger(entry), ([8.5, 8.5, 7.5], [3.0, 3.0, 4.0], 4.0))
        self.assertIsNone(tool._plunger({"sizes": [{"what": "body", "max_mm": [8.5, 8.5, 7.5]}]}))
        # A box without a plunger keeps its one block.
        body, _ = tool.plan_body("box", {"sizes": [{"what": "body", "max_mm": [8.5, 8.5, 7.5]}]},
                                 (0.0, 0.0, 0.0), (9.0, 9.0, 9.0), {})
        self.assertNotIn("detail", body)
        self.assertEqual(sorted(body["size_mm"]), [7.5, 8.5, 8.5])


PUSH_ENVELOPE = ((12.0, -1.0, 0.0), (21.0, 8.0, 13.0))


class AssemblyTextTest(unittest.TestCase):
    """The README's wording follows the contract's who-assembles fields."""

    def text(self, **changes):
        electrical = small_circuit(pcba=changes.pop("pcba", True))
        electrical.update(changes)
        contract, catalogue = sealed(electrical)
        return tool.assembly_text(contract["electrical"], catalogue["bought_parts"])

    def test_a_pcba_says_which_parts_the_factory_assembles_and_what_the_maker_solders(self):
        text = self.text()
        self.assertIn("3 parts arrive factory-assembled on one board (PCBA); their joins are made in the "
                      "factory. The maker fits the other 1 part and solders its wires to the board.", text)
        self.assertIn("| r-screen | Resistor 150 ohm, 0805 SMD | 1 | on the PCBA, in the factory |", text)
        self.assertIn("| s-half |", text)
        self.assertNotIn("Everything is soldered by hand", text)
        self.assertEqual(text, self.text(), "the text is deterministic")

    def test_without_a_board_the_contract_s_assembler_makes_every_join(self):
        self.assertIn("The maker fits every part and solders every join.", self.text(pcba=False))
        text = self.text(pcba=False, assembled_by="buyer", joins="solderless")
        self.assertIn("The buyer fits every part and joins without solder every join.", text)
        self.assertNotIn("factory-assembled", text)

    def test_the_wiring_diagram_marks_board_traces_solder_joins_the_plug_and_the_return(self):
        contract, catalogue = sealed(small_circuit())
        layout = tool.wiring_layout(contract["electrical"])
        kinds = [(link["from"], link["to"], link["kind"], link["by"]) for link in layout["links"]]
        self.assertEqual(kinds, [
            ("usb-supply", "usb-c", "plug", "buyer"),
            ("usb-c", "s-half", "solder", "maker"),
            ("s-half", "r-screen", "solder", "maker"),
            ("r-screen", "screen-led", "board", "factory"),
            ("screen-led", "usb-supply", "return", "maker"),
        ])
        self.assertEqual(layout["columns"], [["usb-supply"], ["usb-c"], ["s-half"], ["r-screen"], ["screen-led"]])
        image = tool.draw_wiring(contract["electrical"], catalogue["bought_parts"])
        self.assertEqual(tool.png_bytes(image), tool.png_bytes(tool.draw_wiring(
            contract["electrical"], catalogue["bought_parts"])))


def _package(printed, bought, bought_colour=MAGENTA):
    occurrences = [{"id": "o%d" % i, "name": name, "component": "c", "transform": list(IDENTITY_TRANSFORM),
                    "color": [0.1, 0.1, 0.1, 1.0]} for i, name in enumerate(printed)]
    occurrences += [{"id": "b%d" % i, "name": name, "component": "c", "transform": list(IDENTITY_TRANSFORM),
                     "color": bought_colour} for i, name in enumerate(bought)]
    return quarterhoot_package(occurrences=occurrences,
                               stats={"occurrenceCount": len(occurrences), "shapeCount": len(occurrences)})


class BoughtOccurrenceTest(unittest.TestCase):
    """A magenta bought_ body is no print part: no colour name, no parts/ STEP."""

    def test_bought_bodies_need_no_colour_name_or_production_step(self):
        package = read_assembly_package(json.dumps(
            _package(["body_black", "base_cream"], ["bought_usb_c", "bought_pcba"])).encode())
        self.assertEqual(occurrences_missing_colour_names(package), ())
        self.assertEqual(missing_production_parts(package, ["parts/body_black.step", "parts/base_cream.step"]), ())
        self.assertEqual([item.name for item in package.printed_occurrences], ["body_black", "base_cream"])

    def test_one_printed_part_beside_bought_bodies_binds_nothing(self):
        package = read_assembly_package(json.dumps(_package(["shell"], ["bought_led"])).encode())
        self.assertEqual(occurrences_missing_colour_names(package), ())
        self.assertEqual(missing_production_parts(package, []), ())

    def test_a_bought_name_in_a_printed_colour_is_a_print_part(self):
        package = read_assembly_package(json.dumps(
            _package(["body_black"], ["bought_led"], bought_colour=[0.1, 0.1, 0.1, 1.0])).encode())
        self.assertEqual(occurrences_missing_colour_names(package), ("bought_led",))
        self.assertEqual(missing_production_parts(package, ["parts/body_black.step"]), ("parts/bought_led.step",))


PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16


class MadeFixture:
    """A sealed Made product with its bought bodies, pictures and README."""

    def setUp(self):
        self.run_root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.run_root)
        self.contract, self.catalogue = sealed(small_circuit())
        self.product = self.run_root / PRODUCT
        self.cad = self.product / "cad"
        names = expected_bodies(self.contract["electrical"], self.catalogue["bought_parts"])
        bodies = []
        for name in names:
            data = ("STEP %s" % name).encode()
            self.write("cad/bought/%s.step" % name, data)
            bodies.append({"name": name, "step": "bought/%s.step" % name,
                           "step_sha256": hashlib.sha256(data).hexdigest()})
        bodies[-1].update(source="contract", bounds=BOARD)
        self.bodies = {"kind": "bought-bodies", "schema_version": 1, "bodies": bodies, "routes": []}
        self.text = tool.assembly_text(self.contract["electrical"], self.catalogue["bought_parts"])
        self.write("cad/measure/verification-pipeline.md", self.pipeline("rc=0"))
        self.write("assembled.step.json", json.dumps(_package(["body_black", "base_cream"], names)))
        self.write("README.md", "# Night light\n\nA lamp.\n\n%s\n" % self.text)
        self.seal()

    def write(self, relative, content):
        path = self.product / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode() if isinstance(content, str) else content)

    def pipeline(self, status):
        return ("# Verification pipeline record\n\n| # | command | status | s |\n|---|---|---|---|\n"
                "| 1 | `/v/bin/python /r/skills/cad/scripts/gen cad/toy.step.py --write --json` | rc=0 | 1.00 |\n"
                "| 2 | `/v/bin/python /r/skills/make-round/scripts/bought_model.py cad --final` | %s | 1.00 |\n"
                % status)

    def seal(self, pictures=None):
        raw = json.dumps(self.bodies, sort_keys=True).encode()
        self.write("cad/measure/bought-bodies.json", raw)
        files = {}
        for name in ("exploded.png", "cutaway.png", "wiring.png"):
            data = (pictures or {}).get(name, PNG + name.encode())
            self.write("cad/measure/electrical/%s" % name, data)
            files[name] = hashlib.sha256(PNG + name.encode()).hexdigest()
        self.write("cad/measure/electrical/assembly.md", self.text)
        files["assembly.md"] = hashlib.sha256(self.text.encode()).hexdigest()
        self.write("cad/measure/electrical/electrical.json", json.dumps({
            "kind": "electrical-pictures", "schema_version": 1, "files": files,
            "bodies_sha256": hashlib.sha256(raw).hexdigest()}))

    def made(self):
        manifest = build_artifact_manifest(self.product, created_at="content-addressed")
        return types.SimpleNamespace(product_root=PRODUCT, cad_project_path="cad", product_manifest=manifest)

    def verify(self, contract=None, catalogue=None):
        return verify_made_bought(self.run_root, self.made(), contract or self.contract,
                                  catalogue if catalogue is not None else self.catalogue)

    def refused(self):
        with self.assertRaises(ContractError) as caught:
            self.verify()
        return str(caught.exception)



class MadeBoughtTest(MadeFixture, unittest.TestCase):
    """The host check on sealed bytes, with no geometry rebuilt."""

    def test_a_drawn_model_whose_pictures_and_readme_match_is_accepted(self):
        account = self.verify()
        self.assertEqual((account["bought_bodies"], account["routes"], account["pcba"]), (5, 0, "pcba"))
        self.assertEqual(account["pictures"]["cutaway.png"], "cad/measure/electrical/cutaway.png")

    def test_a_run_without_catalogue_models_a_kit_or_no_circuit_is_not_checked(self):
        bare = copy.deepcopy(self.catalogue)
        for entry in bare["bought_parts"].values():
            entry.pop("model", None)
        self.assertFalse(draws_bought_parts(self.contract, bare))
        self.assertIsNone(self.verify(catalogue=bare))
        self.assertFalse(draws_bought_parts(dict(self.contract, assembly_tree={"parts": []}), self.catalogue))
        self.assertFalse(draws_bought_parts({"schema_version": 9}, self.catalogue))

    def test_a_failed_or_missing_final_run_is_refused(self):
        self.write("cad/measure/verification-pipeline.md", self.pipeline("rc=1"))
        self.assertIn("did not pass bought_model.py", self.refused())
        self.write("cad/measure/verification-pipeline.md", self.pipeline("rc=0").replace(
            "/r/skills/make-round/scripts/bought_model.py cad --final", "/r/skills/cad/scripts/check_mesh cad"))
        self.assertIn("did not pass bought_model.py", self.refused())

    def test_a_missing_part_body_is_refused(self):
        self.bodies["bodies"] = [item for item in self.bodies["bodies"] if item["name"] != "bought_s_half"]
        self.seal()
        self.assertIn("missing bought_s_half", self.refused())

    def test_a_board_body_without_a_pcba_in_the_contract_is_refused(self):
        self.contract, self.catalogue = sealed(small_circuit(pcba=False))
        self.assertIn("extra bought_pcba", self.refused())

    def test_a_board_not_at_the_contract_s_outline_is_refused(self):
        board = self.bodies["bodies"][-1]
        board.update(source="make-estimate", bounds=BOARD)
        self.seal()
        self.assertIn("the board body is not the contract's pcba.bounds_mm", self.refused())
        board.update(source="contract", bounds=[[-12.0, 0.0, 0.0], [12.0, 1.6, 31.0]])
        self.seal()
        self.assertIn("the board body is not the contract's pcba.bounds_mm", self.refused())

    def test_a_body_step_that_is_not_the_listed_one_is_refused(self):
        self.write("cad/bought/bought_usb_c.step", b"another body")
        self.assertIn("bought/bought_usb_c.step is not the STEP", self.refused())

    def test_an_assembly_without_the_bought_group_is_refused(self):
        self.write("assembled.step.json", json.dumps(_package(["body_black", "base_cream"], ["bought_usb_c"])))
        self.assertIn("add bought_group() to the assembly entry", self.refused())

    def test_a_bought_occurrence_in_a_printed_colour_is_refused(self):
        names = [item["name"] for item in self.bodies["bodies"]]
        document = _package(["body_black"], names)
        document["occurrences"][-1]["color"] = [0.1, 0.1, 0.1, 1.0]
        self.write("assembled.step.json", json.dumps(document))
        self.assertIn("not in the not-printed #ff00ff: bought_pcba", self.refused())

    def test_a_picture_that_is_not_the_one_drawn_is_refused(self):
        self.seal(pictures={"cutaway.png": PNG + b"edited"})
        self.assertIn("measure/electrical/cutaway.png is not the file", self.refused())

    def test_a_readme_without_the_contract_s_assembly_text_is_refused(self):
        self.write("README.md", "# Night light\n\nEverything is soldered by hand.\n")
        self.assertIn("does not carry measure/electrical/assembly.md verbatim", self.refused())

    def test_bytes_that_differ_from_the_manifest_are_refused(self):
        made = self.made()
        self.write("cad/measure/bought-bodies.json", b"{}")
        with self.assertRaises(ContractError) as caught:
            verify_made_bought(self.run_root, made, self.contract, self.catalogue)
        self.assertIn("differs from the Made manifest", str(caught.exception))


class PublishedModelTest(MadeFixture, unittest.TestCase):
    """The toy projection ships the bodies beside the models and the toy
    README shows the pictures and the contract's assembly text."""

    def test_the_bodies_ship_as_models_and_the_pictures_as_reports(self):
        from workshop.release.public_archive import _copy_made_tree

        written = {}
        made = self.made()
        made.cad_verification_path = "cad/measure/none.json"
        _copy_made_tree(lambda path, content: written.__setitem__(path, content), self.run_root, made)
        self.assertIn("make/models/cad/bought/bought_usb_c.step", written)
        self.assertIn("make/verification/reports/electrical/cutaway.png", written)
        self.assertIn("make/verification/reports/bought-bodies.json", written)

    def test_the_toy_readme_carries_the_pictures_and_the_assembly_text(self):
        from workshop.release.public_example import _electrical_markdown

        staging = self.run_root / "staging"
        self.assertEqual(_electrical_markdown(staging), "")
        reports = staging / "make/verification/reports/electrical"
        shutil.copytree(self.cad / "measure/electrical", reports)
        section = _electrical_markdown(staging)
        self.assertTrue(section.startswith("## Electrical assembly\n\n![Every Bought Part in place"))
        for name in ("cutaway.png", "exploded.png", "wiring.png"):
            self.assertIn("(make/verification/reports/electrical/%s)" % name, section)
        self.assertIn("The maker fits the other 1 part and solders its wires to the board.", section)

    def test_the_accepted_model_is_read_back_for_the_receipt(self):
        from workshop.workflow.native_run import _bought_model_history

        host = self.run_root / "host"
        self.assertEqual(_bought_model_history(host), [])
        (host / "gates").mkdir(parents=True)
        account = self.verify()
        (host / "gates" / "0002-make.json").write_text(
            json.dumps({"evidence": {"checks": {"bought_model": [account]}}}))
        self.assertEqual(_bought_model_history(host), [account])


class BuildAndFinalTest(unittest.TestCase):
    """The real tool on a small circuit: build123d bodies, then --final."""

    def test_build_then_final_draws_every_body_and_refuses_a_changed_one(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root)
        contract, catalogue = sealed(small_circuit())
        (root / "WISH.json").write_text(json.dumps({"context": {"design_contract": contract,
                                                                "kit_catalogue": catalogue}}))
        project = root / "cad"
        from build123d import Box, Pos, export_step

        components = []
        for part, (lo, hi) in ENVELOPES.items():
            size = [hi[i] - lo[i] for i in range(3)]
            centre = [(hi[i] + lo[i]) / 2 for i in range(3)]
            path = project / envelope_path(part)
            path.parent.mkdir(parents=True, exist_ok=True)
            export_step(Pos(*centre) * Box(*size), str(path))
            components.append({"id": part, "cad": {"mode": "validation_envelope",
                                                       "source": envelope_path(part)}})
        (project / "measure").mkdir()
        (project / "measure/power.json").write_text(json.dumps({"components": components}))
        (project / "measure/bought-placements.json").write_text(json.dumps(PLACEMENTS))

        document = tool.build(project)
        self.assertEqual([body["name"] for body in document["bodies"]],
                         expected_bodies(contract["electrical"], catalogue["bought_parts"]))
        module = (project / "bought/__init__.py").read_text()
        self.assertIn("def bought_group(", module)
        report = tool.final(project)
        self.assertEqual(sorted(report["files"]), ["assembly.md", "cutaway.png", "exploded.png", "wiring.png"])
        self.assertEqual((project / "measure/electrical/assembly.md").read_text(),
                         tool.assembly_text(contract["electrical"], catalogue["bought_parts"]))
        self.assertFalse(any(path.name.startswith("part_") for path in (project / "bought").iterdir()))

        (project / "bought/bought_usb_c.step").write_bytes(b"edited")
        with self.assertRaises(tool.Refused) as caught:
            tool.final(project)
        self.assertIn("bought/bought_usb_c.step changed since --build", caught.exception.reasons)
        placements = copy.deepcopy(PLACEMENTS)
        placements["parts"]["s-half"]["hinge"] = "-x"
        (project / "measure/bought-placements.json").write_text(json.dumps(placements))
        with self.assertRaises(tool.Refused) as caught:
            tool.final(project)
        self.assertIn("placements_sha256", "; ".join(caught.exception.reasons))

    def test_a_posed_part_is_drawn_turned_inside_its_turned_envelope(self):
        """Issue #225: an LED seated square to a face tilted 30 degrees."""

        from build123d import Axis, Box, Pos, export_step, import_step

        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root)
        contract, catalogue = sealed(small_circuit())
        (root / "WISH.json").write_text(json.dumps({"context": {"design_contract": contract,
                                                                "kit_catalogue": catalogue}}))
        project = root / "cad"
        components = []
        for part, (lo, hi) in ENVELOPES.items():
            size = [hi[i] - lo[i] for i in range(3)]
            centre = [(hi[i] + lo[i]) / 2 for i in range(3)]
            shape = Pos(*centre) * Box(*size)
            if part == "screen-led":
                shape = shape.rotate(Axis(tuple(centre), (1, 0, 0)), 30)
            path = project / envelope_path(part)
            path.parent.mkdir(parents=True, exist_ok=True)
            export_step(shape, str(path))
            components.append({"id": part, "cad": {"mode": "validation_envelope", "source": envelope_path(part)}})
        (project / "measure").mkdir()
        (project / "measure/power.json").write_text(json.dumps({"components": components}))
        envelope = import_step(str(project / envelope_path("screen-led")))

        def outside(placements):
            (project / "measure/bought-placements.json").write_text(json.dumps(placements))
            document = tool.build(project)
            led = next(body for body in document["bodies"] if body["part"] == "screen-led")
            drawn = import_step(str(project / led["step"]))
            return led, drawn, drawn.volume - (drawn & envelope).volume

        led, drawn, poking = outside(PLACEMENTS)
        self.assertNotIn("pose", led)
        self.assertGreater(poking, 1.0, "drawn square to the world, the LED pokes out of its tilted seat")

        posed = copy.deepcopy(PLACEMENTS)
        posed["parts"]["screen-led"]["pose"] = {"axis": [1, 0, 0], "angle_deg": 30}
        led, drawn, poking = outside(posed)
        self.assertLess(poking, 1e-3, "the posed LED stays inside its envelope")
        self.assertEqual(led["pose"], {"axis": [1.0, 0.0, 0.0], "angle_deg": 30.0, "centre": [0.0, 8.0, 14.0]})
        # Turned back, it sits where an unposed LED sits in the untilted seat.
        lo, hi = tool._step_bounds(project / led["step"], led["pose"])
        for i in range(3):
            self.assertAlmostEqual(lo[i], led["bounds"][0][i], delta=tool.BOUND_TOLERANCE_MM)
            self.assertAlmostEqual(hi[i], led["bounds"][1][i], delta=tool.BOUND_TOLERANCE_MM)
        box = drawn.bounding_box()
        self.assertGreater(box.max.Z - box.min.Z, hi[2] - lo[2] + 1.0, "the drawn LED is turned")
        report = tool.final(project)
        self.assertIn("bought_screen_led", report["bodies"])

    def test_a_posed_push_switch_is_drawn_as_body_and_nose_inside_its_stepped_envelope(self):
        """Issue #228: the switch square to a 30 degree deck, its plunger in
        a cap's socket, as the Sunset Slider seats it."""

        from build123d import Align, Axis, Box, Pos, export_step, import_step

        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root)
        electrical = small_circuit()
        next(item for item in electrical["parts"] if item["id"] == "s-half")["bought"] = "switch-push-latching-8x8"
        contract, catalogue = sealed(electrical)
        (root / "WISH.json").write_text(json.dumps({"context": {"design_contract": contract,
                                                                "kit_catalogue": catalogue}}))
        project = root / "cad"
        boxes = dict(ENVELOPES, **{"s-half": PUSH_ENVELOPE})
        centre = (16.5, 3.5, 6.5)
        bottom = (Align.CENTER, Align.CENTER, Align.MIN)
        stepped = Pos(16.5, 3.5, 0.0) * (Box(8.5, 8.5, 7.5, align=bottom)
                                         + Pos(0, 0, 7.5) * Box(3.0, 3.0, 5.5, align=bottom))
        # A cap above the body whose 3.4 square socket the plunger enters.
        cap = Pos(16.5, 3.5, 10.0) * (Box(12.0, 12.0, 4.0, align=bottom)
                                      - Box(3.4, 3.4, 3.0, align=bottom))
        tilt = Axis(centre, (1, 0, 0))
        components = []
        for part, (lo, hi) in boxes.items():
            size = [hi[i] - lo[i] for i in range(3)]
            middle = [(hi[i] + lo[i]) / 2 for i in range(3)]
            shape = stepped.rotate(tilt, 30) if part == "s-half" else Pos(*middle) * Box(*size)
            path = project / envelope_path(part)
            path.parent.mkdir(parents=True, exist_ok=True)
            export_step(shape, str(path))
            components.append({"id": part, "cad": {"mode": "validation_envelope", "source": envelope_path(part)}})
        (project / "measure").mkdir()
        (project / "measure/power.json").write_text(json.dumps({"components": components}))
        placements = copy.deepcopy(PLACEMENTS)
        placements["parts"]["s-half"] = {"facing": "+z", "pose": {"axis": [1, 0, 0], "angle_deg": 30}}
        (project / "measure/bought-placements.json").write_text(json.dumps(placements))

        document = tool.build(project)
        switch = next(body for body in document["bodies"] if body["part"] == "s-half")
        self.assertEqual(switch["detail"], {"nose_mm": [3.0, 3.0, 5.5]})
        drawn = import_step(str(project / switch["step"]))
        self.assertEqual(len(drawn.solids()), 1, "body and nose are one leaf")
        self.assertAlmostEqual(drawn.volume, 8.5 * 8.5 * 7.5 + 3.0 * 3.0 * 5.5, places=3)
        envelope = import_step(str(project / envelope_path("s-half")))
        # Coincident faces leave boolean noise far below the 1.0 mm3 interference tolerance.
        self.assertLess(drawn.volume - (drawn & envelope).volume, 0.01, "inside its stepped envelope")
        self.assertLess((drawn & cap.rotate(tilt, 30)).volume, 0.01, "the nose clears the cap's socket")
        report = tool.final(project)
        self.assertIn("bought_s_half", report["bodies"])


if __name__ == "__main__":
    unittest.main()
