"""ADR 0104 decision 4: a kit's print layout, the STEP Factory weighs.

Contract: ``kit_print.py layout`` writes ``measure/kit/print.step`` with
one leaf per Sheet, ``<Sheet>``, its frame, gates and copies fused into one
connected solid, and one leaf per loose copy of every printed Part the toy
uses, ``loose/<Part>#n``, each its own solid; no Bought Part.
``measure/kit/print.json`` (schema 2) records its hash, the tree it was
laid out for and the copies. A Sheet that does not hold its contract copies,
or does not fuse into one connected solid, fails and writes nothing."""

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


class KitPrintLayoutTest(unittest.TestCase):
    PANEL = KitSheetsProjectTest.PANEL
    setUp = KitSheetsProjectTest.setUp
    install = KitSheetsProjectTest.install
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
        self.assertEqual(report["loose"], {"D01-inkwell": 1})
        self.assertEqual(report["copies"], {"A01-case-shell": 1, "B01-cabinet-carcass": 1, "B02-cabinet-door": 1,
                                            "C01-desk-body": 2, "D01-inkwell": 1})
        bodies = scene_bodies(step)
        names = sorted(body.name for body in bodies)
        self.assertEqual(names, report["bodies"])
        self.assertEqual(report["schema_version"], 2)
        self.assertEqual(names, ["A1", "B1", "C1", "loose/D01-inkwell#1"])
        self.assertFalse(any("bought" in name or name.startswith("P") for name in names))
        # Each Sheet and each loose copy is one connected solid.
        self.assertEqual(Counter((len(b.solids), b.outer_shells) for b in bodies), Counter({(1, 1): 4}))
        # Fused, a Sheet weighs its frame, gates and copies: B1 holds two panels.
        volume = {b.name: b.total[0] for b in bodies}
        self.assertGreater(volume["B1"], 2 * 20 * 12 * 2)

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
