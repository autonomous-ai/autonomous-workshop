"""ADR 0104 decision 3: a kit's Sheets pass make_round's check_sheet.

Contract: ``kit_sheets.py describe`` builds a Sheet file's ``sheet()`` into
plan measures, and ``check`` passes a Sheet that holds exactly its contract
copies, equal to their ``print_parts()`` shapes, flat, separable, every gate
reachable by a nipper and every fragile tip in open space; it names each
broken rule otherwise. ``part_failures`` holds every printed Part to
MIN-PART-SIZE R1 unless it states ``small_reason``, and asks a spare of a
Part under 15 mm."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/make-round/scripts/kit_sheets.py"


def _module():
    spec = importlib.util.spec_from_file_location("kit_sheets_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ks = _module()

# Two 18 x 10 x 2 panels between two runners, each on one gate from below.
SHEET = '''
from build123d import Align, Box, Polygon, Pos, extrude
A = (Align.MIN, Align.MIN, Align.MIN)


def plate(x, y, w, h, t):
    return Pos(x, y, 0) * Box(w, h, t, align=A)


PANEL = dict(w=18, h=10, t=2.0)
XS = (8, 34)
GATES = (9.0,)        # each gate's place along the panel, from its left edge
PANEL_Y = 10.0
EXTRA = None          # a further shape placed on the plate: ("part"|"spike", x, y)


def sheet():
    frame = plate(0, 0, 60, 2.4, 1.6) + plate(0, 27.6, 60, 2.4, 1.6)
    parts = []
    for x in XS:
        part = plate(x, PANEL_Y, PANEL["w"], PANEL["h"], PANEL["t"])
        gates = [{"shape": plate(x + g - 0.8, 2.4, 1.6, PANEL_Y - 2.4, 1.2), "x": x + g, "y": PANEL_Y, "d": 1}
                 for g in GATES]
        parts.append({"id": "A01-panel", "shape": part, "gates": gates})
    if EXTRA and EXTRA[0] == "spike":
        # A spire pointing up at the top runner, 1 mm wide at its tip.
        _kind, x, y = EXTRA
        spike = Pos(0, 0, 0) * extrude(Polygon((x, y), (x + 6, y), (x + 3.5, y + 10), (x + 2.5, y + 10), align=None), 2.0)
        gate = plate(x + 2.2, 2.4, 1.6, y - 2.4, 1.2)
        parts.append({"id": "A02-spire", "shape": spike, "gates": [{"shape": gate, "x": x + 3.0, "y": y, "d": 1}]})
    return {"frame": frame, "parts": parts}
'''

SPEC = {"id": "A1", "filament": "oak", "parts": [{"id": "A01-panel", "count": 2}]}
PANEL = {"volume": 360.0, "area": 2 * 180 + 2 * 28 * 2.0, "size": [2.0, 10.0, 18.0]}


class KitSheetCheckTest(unittest.TestCase):
    def _describe(self, **overrides):
        with tempfile.TemporaryDirectory() as tmp:
            source = SHEET + "".join("\n%s = %r\n" % item for item in overrides.items())
            entry = Path(tmp) / "sheet_A1.py"
            entry.write_text(textwrap.dedent(source))
            done = subprocess.run([sys.executable, str(SCRIPT), "describe", str(entry)],
                                  capture_output=True, text=True, timeout=300)
        return ks.parse(done.stdout, done.returncode)

    def _check(self, spec=SPEC, measures=None, **overrides):
        return ks.check(self._describe(**overrides), spec, measures or {"A01-panel": PANEL})

    def test_a_good_sheet_passes(self):
        described = self._describe()
        self.assertIsNone(described["error"])
        self.assertEqual([item["id"] for item in described["parts"]], ["A01-panel", "A01-panel"])
        self.assertEqual(ks.check(described, SPEC, {"A01-panel": PANEL}), [])

    def test_the_copies_are_the_contract_entries_and_the_print_parts_shape(self):
        fails = self._check(spec={**SPEC, "parts": [{"id": "A01-panel", "count": 3}]})
        self.assertIn("holds 2 x A01-panel, but the contract's Sheet A1 lists 3", fails[0])
        fails = self._check(measures={"A01-panel": {**PANEL, "volume": 300.0}})
        self.assertTrue(any("print_parts() builds it at 300.0 mm3" in line for line in fails), fails)

    def test_a_sheet_is_a_flat_plate(self):
        fails = self._check(PANEL={"w": 18, "h": 10, "t": 3.5}, measures={"A01-panel": {**PANEL, "volume": 630.0,
                                                                                        "area": 360 + 56 * 3.5}})
        self.assertTrue(any("3.5 mm tall; a Sheet is a flat plate" in line for line in fails), fails)

    def test_a_sheet_fits_the_printers_bed(self):
        from shapely.geometry import box
        from shapely import wkt

        described = self._describe()
        frame = wkt.loads(described["frame"]["footprint"])
        lo_x, lo_y = frame.bounds[:2]

        def framed(width, depth):
            # The frame's runner extended to a plate of the given plan size.
            outline = frame.union(box(lo_x, lo_y, lo_x + width, lo_y + 1.0)).union(
                box(lo_x, lo_y, lo_x + 1.0, lo_y + depth))
            return {**described, "frame": {**described["frame"], "footprint": outline.wkt}}

        self.assertEqual(ks.SHEET_MAX_MM, 250.0)
        self.assertEqual(ks.check(framed(250.0, 250.0), SPEC, {"A01-panel": PANEL}), [])
        for width, depth in ((250.5, 40.0), (40.0, 251.0)):
            fails = ks.check(framed(width, depth), SPEC, {"A01-panel": PANEL})
            self.assertEqual(len(fails), 1, fails)
            self.assertIn("in plan; it must fit 250 x 250 mm, the 256 mm bed", fails[0])

    def test_a_copy_too_near_the_frame_is_not_separable(self):
        # The panel 1.0 mm above the runner: under 2.0 from the frame, and
        # the runner stands in the gate's 2 mm keep-out.
        fails = self._check(PANEL_Y=3.4)
        self.assertTrue(any("1.00 mm from the frame" in line for line in fails), fails)
        self.assertTrue(any("nipper cannot reach" in line and "the frame" in line for line in fails), fails)

    def test_a_gate_beside_another_is_out_of_the_nippers_reach(self):
        # Two gates 4 mm apart: each bar stands in the other's 6 mm keep-out.
        fails = self._check(GATES=(6.0, 10.0))
        self.assertTrue(any("nipper cannot reach the gate of A01-panel" in line and "another gate" in line
                            for line in fails), fails)

    def test_a_gate_on_a_corner_is_not_on_a_straight_edge(self):
        fails = self._check(GATES=(17.5,))
        self.assertTrue(any("not straight or convex" in line for line in fails), fails)

    def test_a_fragile_tip_pointing_at_the_runner_fails(self):
        spec = {**SPEC, "parts": SPEC["parts"] + [{"id": "A02-spire", "count": 1}]}
        fails = self._check(spec=spec, EXTRA=("spike", 52.5, 12.0), XS=(4, 26))
        self.assertTrue(any("fragile tip of A02-spire" in line and "pointing up" in line for line in fails), fails)

    def test_a_sheet_that_does_not_build_names_the_rule(self):
        fails = ks.check({"kind": ks.KIND, "error": "sheet_A1.py defines no sheet()"}, SPEC, {})
        self.assertIn("defines no sheet()", fails[0])
        self.assertIn("sheet() returning", fails[0])


class KitPartSizeTest(unittest.TestCase):
    SHEETS = [{"id": "A1", "filament": "oak", "parts": [{"id": "A01-panel", "count": 2}]}]

    def test_a_part_under_r1_needs_a_small_reason(self):
        tiny = {"size": [0.8, 5.0, 20.0], "volume": 80.0}
        fails, small = ks.part_failures(self.SHEETS, {"A01-panel": {}}, {"A01-panel": 1}, {"A01-panel": tiny})
        self.assertIn("thickness 0.8 < 1.6", fails[0])
        fails, small = ks.part_failures(self.SHEETS, {"A01-panel": {"small_reason": "a band glued flat"}},
                                        {"A01-panel": 1}, {"A01-panel": tiny})
        self.assertEqual((fails, small), ([], ["A01-panel"]))

    def test_a_small_part_has_a_spare_on_its_sheets(self):
        short = {"size": [2.0, 5.0, 12.0], "volume": 120.0}
        fails, _ = ks.part_failures(self.SHEETS, {"A01-panel": {}}, {"A01-panel": 2}, {"A01-panel": short})
        self.assertIn("its Sheets carry 2, the toy uses 2; add one spare", fails[0])
        fails, _ = ks.part_failures(self.SHEETS, {"A01-panel": {}}, {"A01-panel": 1}, {"A01-panel": short})
        self.assertEqual(fails, [])

    def test_an_unmeasured_part_fails(self):
        fails, _ = ks.part_failures(self.SHEETS, {"A01-panel": {}}, {"A01-panel": 1}, {})
        self.assertIn("print_parts() did not measure it", fails[0])


if __name__ == "__main__":
    unittest.main()


PART_FILE = '''
from build123d import Align, Box
A = (Align.MIN, Align.MIN, Align.MIN)
SIZES = {sizes!r}


def gen_step():
    return None


def print_parts():
    return {{part: Box(*size, align=A) for part, size in SIZES.items()}}
'''

SHEET_FILE = '''
import importlib.util
from pathlib import Path
from build123d import Align, Box, Pos
A = (Align.MIN, Align.MIN, Align.MIN)
COPIES = {copies!r}


def _printed(role):
    spec = importlib.util.spec_from_file_location("sheet_src_" + role, Path(__file__).with_name("part_%s.step.py" % role))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.print_parts()


def sheet():
    x, parts, top = 4.0, [], 0.0
    for role, part in COPIES:
        shape = _printed(role)[part]
        box = shape.bounding_box()
        placed = Pos(x - box.min.X, 10 - box.min.Y, -box.min.Z) * shape
        middle = x + box.size.X / 2
        gate = Pos(middle - 0.8, 2.4, 0) * Box(1.6, 7.6, 1.2, align=A)
        parts.append({{"id": part, "shape": placed, "gates": [{{"shape": gate, "x": middle, "y": 10.0, "d": 1}}]}})
        x += box.size.X + 8.0
        top = max(top, 10 + box.size.Y)
    # Two runners and the side rails that join them into one frame.
    frame = (Pos(0, 0, 0) * Box(x, 2.4, 1.6, align=A) + Pos(0, top + 4.0, 0) * Box(x, 2.4, 1.6, align=A)
             + Pos(0, 0, 0) * Box(1.6, top + 6.4, 1.6, align=A) + Pos(x - 1.6, 0, 0) * Box(1.6, top + 6.4, 1.6, align=A))
    return {{"frame": frame, "parts": parts}}
'''


class KitSheetsProjectTest(unittest.TestCase):
    PANEL = (20.0, 12.0, 2.0)

    def setUp(self):
        from tests.make.test_kit_tree import sealed_kit

        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = Path(temporary.name)
        self.kit = sealed_kit()
        tree = self.kit["assembly_tree"]
        next(p for p in tree["parts"] if p["id"] == "D01-inkwell")["loose_reason"] = "A round pot."
        tree["sheets"] = [
            {"id": "A1", "filament": "navy", "parts": [{"id": "A01-case-shell", "count": 1}]},
            {"id": "B1", "filament": "dark-oak", "parts": [{"id": "B01-cabinet-carcass", "count": 1},
                                                           {"id": "B02-cabinet-door", "count": 1}]},
            {"id": "C1", "filament": "oak", "parts": [{"id": "C01-desk-body", "count": 2}]},
        ]
        self.write_parts(inkwell=(8.0, 8.0, 8.0))
        for sheet in tree["sheets"]:
            role = {"A": "case", "B": "cabinet", "C": "desk"}[sheet["id"][0]]
            copies = [(role, entry["id"]) for entry in sheet["parts"] for _ in range(entry["count"])]
            (self.project / ("sheet_%s.py" % sheet["id"])).write_text(SHEET_FILE.format(copies=copies))
        self.install()

    def install(self):
        (self.project / "tree").mkdir(exist_ok=True)
        (self.project / "tree" / "kit.json").write_text(json.dumps(self.kit))

    def write_parts(self, inkwell):
        sizes = {"case": {"A01-case-shell": self.PANEL},
                 "cabinet": {"B01-cabinet-carcass": self.PANEL, "B02-cabinet-door": self.PANEL, "D01-inkwell": inkwell},
                 "desk": {"C01-desk-body": self.PANEL}}
        for role, parts in sizes.items():
            (self.project / ("part_%s.step.py" % role)).write_text(PART_FILE.format(sizes=parts))

    def run_check(self):
        done = subprocess.run([sys.executable, str(SCRIPT), "check", str(self.project)],
                              capture_output=True, text=True, timeout=600)
        return done.returncode, ks.parse_report(done.stdout, done.returncode)

    def test_a_kit_whose_sheets_and_parts_follow_the_rules_passes(self):
        code, report = self.run_check()
        self.assertEqual((code, report["failures"]), (0, []))
        self.assertEqual(report["sheets"], ["A1", "B1", "C1"])

    def test_a_small_loose_part_needs_its_reason_and_a_missing_or_stray_sheet_fails(self):
        self.write_parts(inkwell=(6.0, 6.0, 6.0))
        (self.project / "sheet_C1.py").rename(self.project / "sheet_C9.py")
        code, report = self.run_check()
        self.assertEqual(code, 1)
        text = "\n".join(report["failures"])
        self.assertIn("D01-inkwell is under the minimum loose-part size (long side 6.0 < 8.0", text)
        self.assertIn("sheet_C1.py is missing", text)
        self.assertIn("sheet_C9.py is no Sheet of the contract", text)
        next(p for p in self.kit["assembly_tree"]["parts"] if p["id"] == "D01-inkwell")["small_reason"] = "A pot."
        (self.project / "sheet_C9.py").rename(self.project / "sheet_C1.py")
        self.install()
        code, report = self.run_check()
        self.assertEqual((code, report["small"]), (0, ["D01-inkwell"]))

    def test_without_sheets_nothing_is_checked(self):
        del self.kit["assembly_tree"]["sheets"]
        self.install()
        self.assertEqual(self.run_check(), (0, {"kind": ks.REPORT, "verdict": "PASS", "sheets": [], "small": [],
                                               "failures": []}))


class SheetsRoundTest(unittest.TestCase):
    """make_round runs ``kit_sheets.py check`` in an assembly round and in
    ``--print-gates-only`` of a kit with Sheets, never in a component round,
    and a failing report fails the round; final verification runs it too."""

    def setUp(self):
        from tests.make.test_kit_print_parts import GatedRound
        from tests.make.test_kit_tree import sealed_kit
        from tests.make.test_make_round import _install_gate_identity

        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = Path(temporary.name)
        (self.project / "toy.step.py").write_text("def gen_step(): pass\n")
        (self.project / "part_cabinet.step.py").write_text("def gen_step(): pass\ndef print_parts(): pass\n")
        _install_gate_identity(self.project)
        self.kit = sealed_kit()
        self.kit["assembly_tree"]["sheets"] = [
            {"id": "B1", "filament": "dark-oak", "parts": [{"id": "B01-cabinet-carcass", "count": 1}]}]
        (self.project / "tree").mkdir()
        (self.project / "tree" / "kit.json").write_text(json.dumps(self.kit))
        self.report = {"kind": "kit-sheets-report", "verdict": "PASS", "sheets": ["B1"], "small": [],
                       "failures": []}
        test = self

        class Round(GatedRound):
            def fake_run(self, command, **kwargs):
                if Path(command[1]).name == "kit_sheets.py":
                    self.calls.append(command)
                    code = 0 if test.report["verdict"] == "PASS" else 1
                    return subprocess.CompletedProcess(command, code, json.dumps(test.report) + "\n", "")
                return super().fake_run(command, **kwargs)

        self.round = Round(self.project)

    def sheet_calls(self, since=0):
        return [c for c in self.round.calls[since:] if Path(c[1]).name == "kit_sheets.py"]

    def assembly(self):
        from tests.make.test_make_round import load_module

        printed = self.round.main(load_module(), [], 1)
        rounds = sorted((self.project / "measure" / "rounds").iterdir())
        return json.loads((rounds[-1] / "summary.json").read_text()), printed

    def test_an_assembly_round_checks_the_sheets_and_a_failure_fails_it(self):
        summary, printed = self.assembly()
        self.assertEqual([c[2:] for c in self.sheet_calls()], [["check", str(self.project)]])
        self.assertEqual(summary["sheets"]["verdict"], "PASS")
        self.assertIn("sheets PASS 1 Sheet(s)", printed)
        self.report = dict(self.report, verdict="FAIL", failures=["sheet_B1.py: gate g1 is under 3.0 mm of open space"])
        before = len(self.round.calls)
        summary, printed = self.assembly()
        self.assertEqual(len(self.sheet_calls(before)), 1)
        self.assertEqual(summary["sheets"]["verdict"], "FAIL")
        self.assertFalse(summary["checks_ok"])
        self.assertIn("sheet_B1.py: gate g1", printed)

    def test_a_component_round_does_not_check_the_sheets(self):
        from tests.make.test_make_round import load_module

        self.round.main(load_module(), ["--component", "part_cabinet.step.py"], 1)
        self.assertEqual(self.sheet_calls(), [])

    def test_print_gates_only_checks_the_sheets_against_the_kit_it_read(self):
        from tests.make.test_make_round import load_module

        self.report = dict(self.report, verdict="FAIL", failures=["sheet_B1.py is missing"])
        printed = self.round.main(load_module(), ["--print-gates-only"], 1)
        (call,) = self.sheet_calls()
        self.assertEqual(call[2:4], ["check", str(self.project)])
        self.assertEqual(call[4], "--kit")
        self.assertEqual(json.loads(Path(call[5]).read_text())["assembly_tree"]["sheets"],
                         self.kit["assembly_tree"]["sheets"])
        self.assertIn("sheets FAIL 1 Sheet(s)", printed)
        self.assertIn("sheet_B1.py is missing", printed)

    def test_final_verification_checks_the_sheets_of_a_kit_that_has_them(self):
        import contextlib
        import io
        import runpy

        verifier = runpy.run_path(str(SCRIPT.parents[2] / "cad" / "scripts" / "verify_project"))
        runner = verifier["Runner"](cwd=self.project, dry_run=True, verbose=False)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(verifier["_run_kit_sheets"](runner, self.project), 0)
        self.assertIn("kit_sheets.py", runner.records[-1]["command"])
        self.assertIn(" check ", runner.records[-1]["command"])
        # A kit without Sheets runs nothing.
        del self.kit["assembly_tree"]["sheets"]
        (self.project / "tree" / "kit.json").write_text(json.dumps(self.kit))
        runner = verifier["Runner"](cwd=self.project, dry_run=True, verbose=False)
        self.assertEqual(verifier["_run_kit_sheets"](runner, self.project), 0)
        self.assertEqual(runner.records, [])
