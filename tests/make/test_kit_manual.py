"""ADR 0092 decision 9: Make writes a schema 7 kit's Manual deterministically
from its Assembly Tree and the built geometry. The geometry is injected:
these tests pass box meshes in the assembly frame and run the real
rasteriser and PDF writer on them."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from workshop.runtime.package_data import product_run_domain_skill_roots
from tests.make.test_kit_tree import LAYOUT, kit_tree, sealed_kit

TOOL = product_run_domain_skill_roots()["make-round"] / "scripts" / "kit_manual.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("kit_manual_under_test", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


kit_manual = load_tool()

COMPANY = {
    "schema_version": 1, "kind": "workshop-company", "name": "Test Co",
    "after_sales": {"contact": "help@example.invalid", "confirmed": True},
    "warnings": {"small_parts": "Small parts warning.", "batteries": "Battery warning."},
}


def box_mesh(lo, hi):
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    points = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    faces = [(0, 1, 3), (0, 3, 2), (4, 6, 7), (4, 7, 5), (0, 4, 5), (0, 5, 1),
             (2, 3, 7), (2, 7, 6), (0, 2, 6), (0, 6, 4), (1, 5, 7), (1, 7, 3)]
    return points, faces


def meshes_for(kit, layout=None, extra=None):
    """Box meshes keyed as kit_tree keys the bodies; ``extra`` adds boxes to
    a body (an L-shaped door is not the same flipped)."""

    plan = kit_tree.Plan(kit)
    found = {}
    for (role, instance), items in sorted((layout or LAYOUT).items()):
        bodies = [kit_tree.Body(label, shape) for label, shape in items]
        for key, body in kit_tree.keyed(plan, role, bodies, instance).items():
            points, faces = box_mesh(*body.shape)
            for lo, hi in (extra or {}).get(body.label, ()):
                more, more_faces = box_mesh(lo, hi)
                faces = faces + [tuple(i + len(points) for i in face) for face in more_faces]
                points = points + more
            leaf = key.split("#")[0]
            colour = kit_manual.part_colour(plan, leaf) or kit_manual.BOUGHT_GREY
            found[key] = kit_manual.Mesh(points, faces, colour)
    return found


# The cabinet door, with a handle on one side, looks different turned round.
DOOR_HANDLE = {"B02-cabinet-door": [((33, 50, 18), (35, 56, 22))]}


def manual_kit():
    kit = sealed_kit()
    kit["catalogue"]["bought_parts"]["steel-pin-1.5x29.5"]["sizes"] = [
        {"what": "diameter", "mm": [1.5]}, {"what": "length", "mm": [29.5]}]
    return kit


def pdf_text(path):
    import pypdfium2

    document = pypdfium2.PdfDocument(str(path))
    try:
        return "\n".join(document[index].get_textpage().get_text_range() for index in range(len(document)))
    finally:
        document.close()


class KitManualTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def write(self, kit=None, meshes=None, name="cad"):
        kit = kit or manual_kit()
        project = self.root / name
        project.mkdir(exist_ok=True)
        if meshes is None:
            meshes = meshes_for(kit, extra=DOOR_HANDLE)
        document, code = kit_manual.write_manual(project, kit, COMPANY, meshes)
        return project, document, code

    def test_the_manual_is_written_from_the_tree_in_rolife_order(self):
        project, document, code = self.write()
        self.assertEqual(code, 0, document["failures"])
        pdf = project / "manual" / "manual.pdf"
        self.assertTrue(pdf.read_bytes().startswith(b"%PDF"))
        report = json.loads((project / "manual" / "manual.json").read_text())
        self.assertEqual(report["pdf"]["sha256"], hashlib.sha256(pdf.read_bytes()).hexdigest())
        self.assertTrue(report["passed"])
        self.assertEqual(report["tree_sha256"], kit_tree.tree_digest(manual_kit()))
        # One section per Component in the Manual order of its first step,
        # then one join section per step across Components.
        self.assertEqual([section["id"] for section in report["sections"]],
                         ["component:cabinet", "component:desk", "component:case",
                          "join:S07-furniture", "join:S08-wiring"])
        self.assertEqual([section["bag"] for section in report["sections"]], [1, 2, 3, None, None])
        cabinet = report["sections"][0]
        self.assertEqual(cabinet["steps"], ["S01-cabinet-shelf", "S02-cabinet-spines", "S03-hang-door"])
        self.assertEqual(cabinet["materials"], {
            "printed": [{"id": "B01-cabinet-carcass", "count": 1}, {"id": "B02-cabinet-door", "count": 1},
                        {"id": "D01-inkwell", "count": 1}],
            "paper": [{"id": "M01-spine-strip", "count": 1}],
            "bought": [{"id": "P01-hinge-pin", "count": 1}, {"id": "P02-jar", "count": 1}],
        })
        # Counts are per toy: two desks, two books.
        desk = report["sections"][1]
        self.assertEqual(desk["make"], 2)
        self.assertEqual(desk["materials"]["paper"], [{"id": "M02-desk-book", "count": 2}])
        # A 1:1 gauge for the pin, from its catalogue length.
        self.assertEqual(cabinet["gauges"], [{"id": "P01-hinge-pin", "length_mm": 29.5}])
        # The light Check Step comes first, naming the bag its Parts are in.
        self.assertEqual(report["checks"], [{
            "id": "light-test", "parts": ["P03-ball-led", "P04-battery-box"], "bags": [3],
            "text": "Join the LED to the battery box, switch on, then take them apart."}])
        # Front page: the materials, a screwdriver for the battery box,
        # scissors for the paper and batteries for the box.
        front = report["front"]
        self.assertEqual(front["included"], ["tweezers", "foam-tape", "Screwdriver"])
        self.assertEqual(front["self_prepared"], ["Scissors", "Batteries for P04-battery-box (battery-box-2aa-switch)"])
        self.assertEqual(front["warnings"], ["Small parts warning.", "Battery warning."])
        # Q29: every Bought Part is listed as bought, not printed.
        self.assertEqual(front["not_printed"], [
            "P01-hinge-pin  steel-pin-1.5x29.5  x1", "P02-jar  clear-jar-6x7  x1",
            "P03-ball-led  led-3v-cool-white  x1", "P04-battery-box  battery-box-2aa-switch  x1"])
        self.assertEqual(report["not_printed"], [
            {"body": "P01-hinge-pin#1", "bought": "steel-pin-1.5x29.5"},
            {"body": "P02-jar#1", "bought": "clear-jar-6x7"},
            {"body": "P03-ball-led#1", "bought": "led-3v-cool-white"},
            {"body": "P04-battery-box#1", "bought": "battery-box-2aa-switch"}])
        self.assertEqual(report["company"], {"name": "Test Co", "after_sales": "help@example.invalid",
                                             "confirmed": True})
        text = pdf_text(pdf)
        for needle in ("Assembly Manual", "Included tools", "Self-prepared", "Warnings",
                       "Check all Parts against the material lists before you start.", "Light check",
                       "Join the LED to the battery box", "Bag 1", "Printed", "Paper", "Bought, not printed",
                       "These come bought. Do not print them", "P02-jar clear-jar-6x7 x1",
                       "Set the door between the lugs and push the pin down.", "Correct", "Incorrect",
                       "P01-hinge-pin: 29.5 mm, 1:1", "M01-spine-strip [printed side out]",
                       "Lead of P03-ball-led comes out: Out of the hole under the dais.",
                       "S01 (Cabinet with jar and inkwell)", "Completion", "help@example.invalid"):
            self.assertIn(needle, text)

    def test_every_leaf_is_in_exactly_one_material_list(self):
        _project, document, _code = self.write()
        listed = [row["id"] for section in document["sections"]
                  for column in section["materials"].values() for row in column]
        kit = manual_kit()
        leaves = ([part["id"] for part in kit["assembly_tree"]["parts"]]
                  + [piece["id"] for piece in kit["pieces"]])
        self.assertEqual(sorted(listed), sorted(leaves))

    def test_the_same_tree_and_build_give_byte_identical_files(self):
        first, _document, _code = self.write(name="one")
        kit_manual._MODULES.clear()  # a fresh process reads its tools again
        second, _document, _code = self.write(name="two")
        for name in ("manual.pdf", "manual.json"):
            self.assertEqual((first / "manual" / name).read_bytes(), (second / "manual" / name).read_bytes(), name)
        # Another build gives another Manual: the pictures are the build's.
        layout = copy.deepcopy(LAYOUT)
        layout[("cabinet", 1)][0] = ("B01-cabinet-carcass", ((40, 40, 5), (75, 60, 40)))
        third, _document, _code = self.write(meshes=meshes_for(manual_kit(), layout, DOOR_HANDLE), name="three")
        self.assertNotEqual((first / "manual" / "manual.pdf").read_bytes(),
                            (third / "manual" / "manual.pdf").read_bytes())

    def test_an_error_prone_step_shows_the_input_half_turned(self):
        _project, document, _code = self.write()
        self.assertEqual(document["steps"]["S03-hang-door"], {"picture": "exploded", "error_picture": "half-turn"})
        self.assertIn("right:S03-hang-door", document["pictures"])
        self.assertIn("wrong:S03-hang-door", document["pictures"])
        # A door that looks the same turned round gets the placeholder.
        _project, document, _code = self.write(meshes=meshes_for(manual_kit()), name="plain")
        self.assertEqual(document["steps"]["S03-hang-door"]["error_picture"], "same-either-way")
        self.assertNotIn("wrong:S03-hang-door", document["pictures"])
        text = pdf_text(_project / "manual" / "manual.pdf")
        self.assertIn("No incorrect picture: this input looks the same either way round", text)

    def test_a_step_without_an_instruction_writes_no_manual(self):
        kit = manual_kit()
        kit["assembly_tree"]["steps"][2]["text"] = " "
        project, document, code = self.write(kit)
        self.assertEqual(code, 1)
        self.assertIn("S03-hang-door has no instruction", "; ".join(document["failures"]))
        self.assertFalse((project / "manual" / "manual.pdf").exists())
        report = json.loads((project / "manual" / "manual.json").read_text())
        self.assertFalse(report["passed"])

    def test_an_unknown_part_id_writes_no_manual(self):
        kit = manual_kit()
        kit["assembly_tree"]["steps"][0]["inputs"].append({"id": "E09-ghost", "direction": [0, 1, 0]})
        _project, document, code = self.write(kit)
        self.assertEqual(code, 1)
        self.assertIn("S01-cabinet-shelf takes 'E09-ghost', which is no Part, Print Piece or earlier step",
                      "; ".join(document["failures"]))

    def test_a_leaf_in_two_sections_writes_no_manual(self):
        kit = manual_kit()
        # The jar also goes into the case: an install no sealed contract gives.
        kit["assembly_tree"]["steps"][4]["inputs"].append({"id": "P02-jar", "direction": [0, 0, 1]})
        _project, document, code = self.write(kit)
        self.assertEqual(code, 1)
        self.assertIn("P02-jar is in the material lists of component:cabinet and join:S05-case-lamp",
                      "; ".join(document["failures"]))

    def test_a_check_step_without_an_instruction_or_with_an_unknown_part_is_refused(self):
        kit = manual_kit()
        kit["assembly_tree"]["checks"][0]["parts"].append("P09-ghost")
        _project, document, code = self.write(kit)
        self.assertEqual(code, 1)
        self.assertIn("names 'P09-ghost', which is no Bought Part", "; ".join(document["failures"]))
        kit["assembly_tree"]["checks"][0]["text"] = ""
        _project, document, code = self.write(kit, name="other")
        self.assertIn("Check Step light-test has no instruction", "; ".join(document["failures"]))

    def test_loose_cells_and_a_soldered_leads_step_reach_the_front_page(self):
        # ADR 0095: two loose cells are the batteries themselves; a soldered
        # leads step needs the iron, solder and the company's heat warning.
        kit = manual_kit()
        kit["catalogue"]["bought_parts"]["battery-box-2aa-switch"].update(category="cell", name="AAA cell")
        wiring = next(item for item in kit["assembly_tree"]["steps"] if item["id"] == "S08-wiring")
        wiring["method"] = "solder"
        company = copy.deepcopy(COMPANY)
        company["warnings"]["soldering"] = "Soldering warning."
        document = kit_manual.plan_manual(kit, company)
        self.assertEqual(document["failures"], [])
        front = document["front"]
        self.assertEqual(front["self_prepared"], ["Scissors", "Batteries: 1 x AAA cell", "Soldering iron", "Solder"])
        self.assertEqual(front["warnings"], ["Small parts warning.", "Battery warning.", "Soldering warning."])
        self.assertEqual(kit_manual.LEAD_METHOD_LABELS["solder"], "Solder the leads")
        # Without the company's warning nothing is written.
        self.assertIn("a leads step is soldered, but the company configuration has no soldering warning",
                      kit_manual.plan_manual(kit, COMPANY)["failures"])

    def test_the_packaged_company_configuration_warns_of_soldering(self):
        company = json.loads((TOOL.parent.parent / "company.json").read_text())
        self.assertIn("soldering", company["warnings"])

    def test_the_packaged_company_configuration_is_an_unconfirmed_placeholder(self):
        company = kit_manual.load_company(kit_manual.COMPANY_FILE)
        self.assertFalse(company["after_sales"]["confirmed"])
        self.assertIn("PLACEHOLDER", company["after_sales"]["contact"])
        bad = self.root / "company.json"
        bad.write_text(json.dumps({**COMPANY, "after_sales": {"contact": ""}}))
        with self.assertRaises(kit_manual.UsageError):
            kit_manual.load_company(bad)

    def test_the_command_line_refuses_a_project_without_a_tree(self):
        project = self.root / "empty"
        project.mkdir()
        self.assertEqual(kit_manual.main([str(project)]), 2)
        self.assertEqual(kit_manual.main(["--self-check"]), 0)


class FinalVerificationManualTest(unittest.TestCase):
    def test_final_verification_writes_the_manual_of_a_schema_7_run(self):
        import contextlib
        import io
        import runpy

        from workshop.wish.design_contract import parse_design_contract
        from tests.make.test_kit_tree import sealed_block
        from tests.wish.test_assembly_tree import _catalogues
        from tests.wish.test_design_contract import _contract_text

        verifier = runpy.run_path(str(product_run_domain_skill_roots()["cad"] / "scripts" / "verify_project"))
        self.assertIn(TOOL, verifier["_sweep_tool_paths"](image_derived=False))
        with tempfile.TemporaryDirectory() as temporary:
            run_root = Path(temporary)
            project = run_root / "cad"
            project.mkdir()
            parsed = parse_design_contract(_contract_text(sealed_block()), catalogues=_catalogues())
            (run_root / "WISH.json").write_text(json.dumps({"references": [], "context": {
                "design_contract": parsed.to_dict(), "kit_catalogue": parsed.kit_catalogue()}}))
            runner = verifier["Runner"](cwd=project, dry_run=False, verbose=False)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(verifier["_run_kit_manual"](runner, project), 1)
            self.assertIn("kit manual  # FAILED", runner.records[-1]["command"])
            kit_tree.install(project, run_root / "WISH.json")
            runner = verifier["Runner"](cwd=project, dry_run=True, verbose=False)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(verifier["_run_kit_manual"](runner, project), 0)
            self.assertIn("kit_manual.py", runner.records[-1]["command"])
            # An earlier contract writes no Manual.
            (run_root / "WISH.json").write_text(json.dumps({"references": [], "context": {
                "design_contract": dict(parsed.to_dict(), schema_version=6)}}))
            runner = verifier["Runner"](cwd=project, dry_run=True, verbose=False)
            self.assertEqual(verifier["_run_kit_manual"](runner, project), 0)
            self.assertEqual(runner.records, [])


def _build123d_imports() -> bool:
    try:
        import build123d  # noqa: F401
    except Exception:  # noqa: BLE001 - this environment cannot build geometry
        return False
    return True


PART_SOURCE = """from build123d import Box, Color, Compound, Location, Pos

PRINTED = {printed!r}
BOUGHT = {bought!r}
SHIFT = {shift!r}


def _bodies(items, colour):
    found = []
    for label, (lo, hi) in items:
        size = [h - l for l, h in zip(lo, hi)]
        body = Pos(*[(l + h) / 2 for l, h in zip(lo, hi)]) * Box(*size)
        body.label = label
        body.color = Color(*colour)
        found.append(body)
    return Compound(children=found)


def gen_step():
    return _bodies(PRINTED, (0.07, 0.13, 0.2))


def bought_parts():
    return _bodies(BOUGHT, (1.0, 0.0, 1.0)) if BOUGHT else None


def assembly_pose(shape, pose, instance=1):
    return shape.moved(Location(tuple(SHIFT.get(str(instance), (0, 0, 0)))))
"""


@unittest.skipUnless(_build123d_imports(), "build123d does not import here: the real geometry path is not run")
class RealGeometryManualTest(unittest.TestCase):
    """The real path: each Component built from its source by kit_tree's
    CadGeometry, tessellated, and rendered; twice, to the same bytes."""

    def test_the_manual_of_a_built_project_is_deterministic(self):
        kit = manual_kit()
        with tempfile.TemporaryDirectory() as temporary:
            outputs = []
            for name in ("one", "two"):
                project = Path(temporary) / name
                (project / "tree").mkdir(parents=True)
                (project / "tree" / "kit.json").write_bytes(kit_tree.document_bytes(kit))
                for role in ("case", "cabinet", "desk"):
                    items = LAYOUT[(role, 1)]
                    printed = [(label, shape) for label, shape in items if not label.startswith("P")]
                    bought = [(label, shape) for label, shape in items if label.startswith("P")]
                    shift = {}
                    if role == "desk":
                        a, b = LAYOUT[("desk", 1)][0][1][0], LAYOUT[("desk", 2)][0][1][0]
                        shift = {"2": [y - x for x, y in zip(a, b)]}
                    (project / ("part_%s.step.py" % role)).write_text(
                        PART_SOURCE.format(printed=printed, bought=bought, shift=shift))
                company = Path(temporary) / "company.json"
                company.write_text(json.dumps(COMPANY))
                kit_manual._MODULES.clear()
                self.assertEqual(kit_manual.main([str(project), "--company", str(company)]), 0)
                outputs.append((project / "manual" / "manual.pdf").read_bytes())
            self.assertEqual(outputs[0], outputs[1])
            # Q29 on real geometry: the Bought Parts read back in the
            # reserved magenta and the printed Parts in their filaments.
            plan = kit_tree.Plan(kit)
            geometry = kit_tree.CadGeometry(project, {"desk": 2})
            bodies = [body for role in ("case", "cabinet") for body in geometry.component(role, 1)]
            self.assertIn("#ff00ff", {colour for body in bodies for colour in body.colours})
            self.assertEqual(kit_tree.colour_failures(plan, bodies), [])


if __name__ == "__main__":
    unittest.main()
