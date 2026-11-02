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


if __name__ == "__main__":
    unittest.main()
