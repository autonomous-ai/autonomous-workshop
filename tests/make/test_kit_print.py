"""ADR 0104 decision 4: a kit's print layout, the STEP Factory weighs.

Contract: ``kit_print.py layout`` writes ``measure/kit/print.step`` with
one leaf per Sheet, ``<Sheet>``, its frame, gates and copies fused into one
connected solid, and one leaf per loose copy of every printed Part the toy
uses, ``loose/<Part>#n``, each its own solid; no Bought Part.
``measure/kit/print.json`` (schema 2) records its hash, the tree it was
laid out for and the copies. A Sheet that does not hold its contract copies,
or does not fuse into one connected solid, fails and writes nothing.

Since 2026-11-23 it also writes ``measure/kit/scene.step``, the assembly
STEP final verification wrote less the bodies ``measure/not-printed.json``
lists, and records it under ``printed_scene``; a project with no assembly
STEP fails."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from collections import Counter
from pathlib import Path

from tests.make.test_kit_sheets import KitSheetsProjectTest
from workshop.make.kit_tree import tree_digest
from workshop.release.printed_primary import scene_bodies

SCRIPT = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/make-round/scripts/kit_print.py"


def write_assembly_scene(project: Path) -> bytes:
    """The assembly STEP final verification writes before the layout: two
    printed bodies and one magenta Bought Part pin, listed not printed."""

    from build123d import Box, Color, Compound, Pos, export_step

    bodies = []
    for index, (name, colour) in enumerate((("A01-case-shell", (0.1, 0.1, 0.4)),
                                            ("C01-desk-body", (0.8, 0.6, 0.4)),
                                            ("P01-hinge-pin#1", (1.0, 0.0, 1.0)))):
        body = Pos(index * 30.0, 0, 0) * Box(10, 8, 4 + index)
        body.label, body.color = name, Color(*colour)
        bodies.append(body)
    (project / "toy.step.py").write_text("def gen_step(): pass\n")
    export_step(Compound(children=bodies, label="toy"), str(project / "toy.step"))
    (project / "measure").mkdir(exist_ok=True)
    (project / "measure/not-printed.json").write_text(json.dumps(
        {"kind": "kit-not-printed", "bodies": [{"body": "P01-hinge-pin#1", "part": "P01-hinge-pin"}]}))
    return (project / "toy.step").read_bytes()


class KitPrintLayoutTest(unittest.TestCase):
    PANEL = KitSheetsProjectTest.PANEL
    install = KitSheetsProjectTest.install

    def setUp(self):
        KitSheetsProjectTest.setUp(self)
        self.scene = write_assembly_scene(self.project)
    write_parts = KitSheetsProjectTest.write_parts

    def layout(self):
        return subprocess.run([sys.executable, str(SCRIPT), "layout", str(self.project)],
                              capture_output=True, text=True, timeout=600)

    def test_the_layout_holds_every_sheet_and_every_loose_copy_and_no_bought_part(self):
        done = self.layout()
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        report = json.loads((self.project / "measure/kit/print.json").read_text())
        step = (self.project / "measure/kit/print.step").read_bytes()
        self.assertEqual(report["kind"], "kit-print-layout")
        self.assertEqual(report["tree_sha256"], tree_digest(self.kit))
        self.assertEqual(report["sha256"], __import__("hashlib").sha256(step).hexdigest())
        # The toy uses one inkwell; its tree entry declares one spare.
        self.assertEqual(report["loose"], {"D01-inkwell": 2})
        self.assertEqual(report["copies"], {"A01-case-shell": 1, "B01-cabinet-carcass": 1, "B02-cabinet-door": 1,
                                            "C01-desk-body": 2, "D01-inkwell": 2})
        bodies = scene_bodies(step)
        names = sorted(body.name for body in bodies)
        self.assertEqual(names, report["bodies"])
        self.assertEqual(report["schema_version"], 2)
        self.assertEqual(names, ["A1", "B1", "C1", "loose/D01-inkwell#1", "loose/D01-inkwell#2"])
        self.assertFalse(any("bought" in name or name.startswith("P") for name in names))
        # Each Sheet and each loose copy is one connected solid.
        self.assertEqual(Counter((len(b.solids), b.outer_shells) for b in bodies), Counter({(1, 1): 5}))
        # Fused, a Sheet weighs its frame, gates and copies: B1 holds two panels.
        volume = {b.name: b.total[0] for b in bodies}
        self.assertGreater(volume["B1"], 2 * 20 * 12 * 2)
        # The printed-only scene: the assembly less its listed pin.
        printed = (self.project / "measure/kit/scene.step").read_bytes()
        self.assertEqual(report["printed_scene"], {
            "step": "measure/kit/scene.step", "sha256": __import__("hashlib").sha256(printed).hexdigest(),
            "scene": "toy.step", "scene_sha256": __import__("hashlib").sha256(self.scene).hexdigest(),
            "removed": ["P01-hinge-pin#1"]})
        self.assertEqual(sorted(b.name for b in scene_bodies(printed)), ["A01-case-shell", "C01-desk-body"])

    def test_a_kit_without_its_assembly_step_fails(self):
        (self.project / "toy.step").unlink()
        done = self.layout()
        self.assertEqual(done.returncode, 1)
        self.assertIn("no assembly STEP", done.stdout)

    def test_a_loose_part_without_spares_prints_once_per_use(self):
        del next(p for p in self.kit["assembly_tree"]["parts"] if p["id"] == "D01-inkwell")["spares"]
        self.install()
        done = self.layout()
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        report = json.loads((self.project / "measure/kit/print.json").read_text())
        self.assertEqual(report["loose"], {"D01-inkwell": 1})
        self.assertEqual([b for b in report["bodies"] if b.startswith("loose/")], ["loose/D01-inkwell#1"])
        self.assertNotIn("spares", report)

    def test_a_kit_that_ships_no_spares_records_it(self):
        # ADR 0104 amendment 2026-11-26.
        tree = self.kit["assembly_tree"]
        del next(p for p in tree["parts"] if p["id"] == "D01-inkwell")["spares"]
        tree["spares"] = "none"
        self.install()
        done = self.layout()
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        report = json.loads((self.project / "measure/kit/print.json").read_text())
        self.assertEqual((report["spares"], report["loose"]), ("none", {"D01-inkwell": 1}))

    def test_a_loose_part_of_two_solids_fails_and_writes_nothing(self):
        self.write_parts(inkwell=(8.0, 8.0, 8.0), split={"D01-inkwell"})
        done = self.layout()
        self.assertEqual(done.returncode, 1)
        self.assertIn("loose Part D01-inkwell is 2 solids, not one connected solid", done.stdout)
        self.assertFalse((self.project / "measure/kit/print.json").exists())

    def test_a_sheet_that_does_not_fuse_into_one_solid_fails_and_writes_nothing(self):
        sheet = self.project / "sheet_A1.py"
        # The gate stops 0.6 mm short of the runner: the copy floats.
        sheet.write_text(sheet.read_text().replace("Pos(middle - 0.8, 2.4, 0) * Box(1.6, 7.6, 1.2",
                                                   "Pos(middle - 0.8, 3.0, 0) * Box(1.6, 7.0, 1.2"))
        done = self.layout()
        self.assertEqual(done.returncode, 1)
        self.assertIn("Sheet A1 does not fuse into one connected solid but 2 piece(s)", done.stdout)
        self.assertFalse((self.project / "measure/kit/print.json").exists())

    def test_a_sheet_that_does_not_hold_its_copies_fails_and_writes_nothing(self):
        self.kit["assembly_tree"]["sheets"][2]["parts"][0]["count"] = 3
        self.install()
        done = self.layout()
        self.assertEqual(done.returncode, 1)
        self.assertIn("sheet_C1.py holds", done.stdout)
        self.assertFalse((self.project / "measure/kit/print.json").exists())


    def fit_test_sheet(self, t2=(18.0, 10.0, 2.0)):
        """Sheet A1 with a declared fit-test pair (ADR 0092 amendment
        2026-11-26): the case shell, then T1 and T2 as plain plates."""

        from tests.make.test_kit_sheets import SHEET_FILE

        source = SHEET_FILE.format(copies=[("case", "A01-case-shell")]).replace(
            "    for role, part in COPIES:\n        shape = _printed(role)[part]\n",
            "    for role, part in COPIES + TESTS:\n"
            "        shape = Box(*role, align=A) if isinstance(role, tuple) else _printed(role)[part]\n")
        source += "\nTESTS = %r\n" % [((18.0, 10.0, 2.0), "T1"), (t2, "T2")]
        (self.project / "sheet_A1.py").write_text(source)
        self.kit["assembly_tree"]["sheets"][0]["fit_test"] = {
            "pieces": [{"id": "T1", "name": "Fit slots"}, {"id": "T2", "name": "Fit tab"}],
            "text": "Press T2 into T1."}
        self.install()

    def test_fit_test_pieces_print_fused_on_their_sheet(self):
        from tests.make.test_kit_sheets import ks

        self.fit_test_sheet()
        self.assertEqual(ks.check_project(self.project)["failures"], [])
        done = self.layout()
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        report = json.loads((self.project / "measure/kit/print.json").read_text())
        self.assertEqual(report["sheets"][0], {"id": "A1", "filament": "navy", "copies": {"A01-case-shell": 1},
                                               "fit_tests": ["T1", "T2"]})
        self.assertNotIn("T1", report["copies"])
        step = (self.project / "measure/kit/print.step").read_bytes()
        bodies = scene_bodies(step)
        self.assertEqual(sorted(b.name for b in bodies), ["A1", "B1", "C1", "loose/D01-inkwell#1",
                                                          "loose/D01-inkwell#2"])
        # Fused with A1: its volume holds both 18 x 10 x 2 plates.
        self.assertGreater({b.name: b.total[0] for b in bodies}["A1"], 20 * 12 * 2 + 2 * 18 * 10 * 2)

    def test_an_undeclared_or_undersized_fit_test_piece_fails(self):
        from tests.make.test_kit_sheets import ks

        self.fit_test_sheet(t2=(6.0, 3.0, 1.2))
        fails = ks.check_project(self.project)["failures"]
        self.assertTrue(any("fit-test piece T2 is under the minimum loose-part size" in line for line in fails),
                        fails)
        self.fit_test_sheet()
        self.kit["assembly_tree"]["sheets"][0]["fit_test"]["pieces"].pop()
        self.install()
        self.assertIn("sheet_A1.py: holds 1 x T2, but the contract's Sheet A1 lists 0",
                      ks.check_project(self.project)["failures"])
        done = self.layout()
        self.assertEqual(done.returncode, 1)
        self.assertIn("sheet_A1.py holds", done.stdout)
        self.assertFalse((self.project / "measure/kit/print.json").exists())

    def test_final_verification_lays_out_every_kit_and_nothing_else(self):
        import contextlib
        import io
        import runpy

        verifier = runpy.run_path(str(SCRIPT.parents[2] / "cad" / "scripts" / "verify_project"))
        runner = verifier["Runner"](cwd=self.project, dry_run=True, verbose=False)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(verifier["_run_kit_print_layout"](runner, self.project), 0)
        self.assertIn("kit_print.py", runner.records[-1]["command"])
        self.assertIn(" layout ", runner.records[-1]["command"])
        (self.project / "tree" / "kit.json").unlink()
        runner = verifier["Runner"](cwd=self.project, dry_run=True, verbose=False)
        self.assertEqual(verifier["_run_kit_print_layout"](runner, self.project), 0)
        self.assertEqual(runner.records, [])


if __name__ == "__main__":
    unittest.main()
