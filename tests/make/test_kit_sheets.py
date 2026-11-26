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


# The good Sheet widened for a fit-test pair (ADR 0092 amendment
# 2026-11-26): the two panels, then T1 and T2 on their own gates.
FIT_SHEET = '''
from build123d import Align, Box, Pos
A = (Align.MIN, Align.MIN, Align.MIN)


def plate(x, y, w, h, t):
    return Pos(x, y, 0) * Box(w, h, t, align=A)


T2 = dict(w=18, h=10, t=2.0)


def sheet():
    frame = plate(0, 0, 112, 2.4, 1.6) + plate(0, 27.6, 112, 2.4, 1.6)
    parts = []
    for x, name, size in ((8, "A01-panel", dict(w=18, h=10, t=2.0)), (34, "A01-panel", dict(w=18, h=10, t=2.0)),
                          (60, "T1", dict(w=18, h=10, t=2.0)), (86, "T2", T2)):
        part = plate(x, 10.0, size["w"], size["h"], size["t"])
        middle = x + size["w"] / 2
        gate = plate(middle - 0.8, 2.4, 1.6, 7.6, 1.2)
        parts.append({"id": name, "shape": part, "gates": [{"shape": gate, "x": middle, "y": 10.0, "d": 1}]})
    return {"frame": frame, "parts": parts}
'''

FIT_SPEC = {**SPEC, "fit_test": {"pieces": [{"id": "T1", "name": "Fit slots"}, {"id": "T2", "name": "Fit tab"}],
                                 "text": "Press T2 into T1: it goes in firmly and holds."}}


class FitTestPieceTest(unittest.TestCase):
    """ADR 0092 amendment 2026-11-26: a Sheet's declared fit-test pieces
    are printed on it and pass every Sheet rule, but are no Part."""

    def _check(self, spec=FIT_SPEC, **overrides):
        with tempfile.TemporaryDirectory() as tmp:
            source = FIT_SHEET + "".join("\n%s = %r\n" % item for item in overrides.items())
            entry = Path(tmp) / "sheet_A1.py"
            entry.write_text(textwrap.dedent(source))
            done = subprocess.run([sys.executable, str(SCRIPT), "describe", str(entry)],
                                  capture_output=True, text=True, timeout=300)
        described = ks.parse(done.stdout, done.returncode)
        self.assertIsNone(described["error"])
        return ks.check(described, spec, {"A01-panel": PANEL})

    def test_a_declared_fit_test_pair_passes(self):
        self.assertEqual(self._check(), [])
        self.assertEqual(ks.fit_test_ids(FIT_SPEC), ["T1", "T2"])

    def test_a_fit_test_piece_the_sheet_does_not_declare_is_refused(self):
        spec = {**FIT_SPEC, "fit_test": {**FIT_SPEC["fit_test"], "pieces": [{"id": "T1", "name": "Fit slots"}]}}
        self.assertEqual(self._check(spec), ["sheet_A1.py: holds 1 x T2, but the contract's Sheet A1 lists 0"])
        fails = self._check(SPEC)
        self.assertIn("sheet_A1.py: holds 1 x T1, but the contract's Sheet A1 lists 0", fails)
        self.assertIn("sheet_A1.py: holds 1 x T2, but the contract's Sheet A1 lists 0", fails)

    def test_a_fit_test_piece_under_the_minimum_size_is_refused(self):
        fails = self._check(T2={"w": 6, "h": 3, "t": 1.2})
        self.assertTrue(any("fit-test piece T2 is under the minimum loose-part size (thickness 1.2 < 1.6"
                            in line for line in fails), fails)

    def test_a_fit_test_piece_breaks_the_sheet_rules_like_a_part(self):
        fails = self._check(T2={"w": 18, "h": 10, "t": 3.5})
        self.assertTrue(any("a copy of T2 is 3.5 mm tall; a Sheet is a flat plate" in line for line in fails), fails)
        fails = self._check(T2={"w": 18, "h": 16.5, "t": 2.0})
        self.assertTrue(any("a copy of T2 is" in line and "from the frame" in line for line in fails), fails)

    def test_fit_test_pieces_are_no_part_and_no_spare(self):
        # part_failures reads printed Parts only: a fit-test piece is never one,
        # so "spares": "none" neither counts nor refuses it.
        fails, small = ks.part_failures([FIT_SPEC], {"A01-panel": {"id": "A01-panel"}}, {"A01-panel": 2},
                                        {"A01-panel": {**PANEL, "pieces": 1}}, no_spares=True)
        self.assertEqual((fails, small), ([], []))


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

    def test_a_small_loose_part_declares_its_spares(self):
        short = {"size": [2.0, 5.0, 12.0], "volume": 120.0}
        loose = {"T01-pin": {"loose_reason": "round"}}
        fails, _ = ks.part_failures(self.SHEETS, loose, {"T01-pin": 2}, {"T01-pin": short})
        self.assertEqual(fails, ['T01-pin is 12.0 mm long, under 15, and prints loose with no spare: state '
                                 '"spares": 1 or more on its tree entry'])
        loose["T01-pin"]["spares"] = 1
        self.assertEqual(ks.part_failures(self.SHEETS, loose, {"T01-pin": 2}, {"T01-pin": short})[0], [])
        # At 15 mm or longer a loose Part needs no spare, as on a Sheet.
        long_ = {"size": [2.0, 5.0, 15.0], "volume": 150.0}
        self.assertEqual(ks.part_failures(self.SHEETS, {"T01-pin": {"loose_reason": "round"}}, {"T01-pin": 2},
                                          {"T01-pin": long_})[0], [])

    def test_a_kit_that_ships_no_spares_asks_none(self):
        # ADR 0104 amendment 2026-11-26: the owner-approved opt-out.
        short = {"size": [2.0, 5.0, 12.0], "volume": 120.0}
        sheets = [{"id": "A1", "filament": "oak", "parts": [{"id": "A01-panel", "count": 2}]}]
        self.assertEqual(ks.part_failures(sheets, {"A01-panel": {}}, {"A01-panel": 2}, {"A01-panel": short},
                                          no_spares=True)[0], [])
        loose = {"T01-pin": {"loose_reason": "round"}}
        self.assertEqual(ks.part_failures(sheets, loose, {"T01-pin": 2}, {"T01-pin": short}, no_spares=True)[0],
                         [])
        # A spare it still carries is inconsistent with the declaration.
        loose["T01-pin"]["spares"] = 1
        self.assertEqual(ks.part_failures(sheets, loose, {"T01-pin": 2}, {"T01-pin": short}, no_spares=True)[0],
                         ['T01-pin declares spares, but the kit declares spares "none": remove its spares'])
        self.assertEqual(ks.part_failures(sheets, {"A01-panel": {}}, {"A01-panel": 1}, {"A01-panel": short},
                                          no_spares=True)[0],
                         ['A01-panel: its Sheets carry 2, the toy uses 1, but the kit declares spares "none": '
                          'carry exactly 1'])

    def test_the_opt_out_loosens_no_size_rule(self):
        tiny = {"size": [0.8, 5.0, 12.0], "volume": 80.0, "pieces": 2}
        fails, _ = ks.part_failures(self.SHEETS, {"A01-panel": {}}, {"A01-panel": 2}, {"A01-panel": tiny},
                                    no_spares=True)
        self.assertEqual(len(fails), 2)
        self.assertIn("is 2 solids", fails[0])
        self.assertIn("thickness 0.8 < 1.6", fails[1])

    def test_a_part_is_one_connected_solid(self):
        one = {"size": [2.0, 10.0, 20.0], "volume": 400.0, "pieces": 1}
        self.assertEqual(ks.part_failures(self.SHEETS, {"A01-panel": {}}, {"A01-panel": 1}, {"A01-panel": one})[0], [])
        fails, _ = ks.part_failures(self.SHEETS, {"A01-panel": {}}, {"A01-panel": 1},
                                    {"A01-panel": {**one, "pieces": 4}})
        self.assertEqual(fails, ["A01-panel is 4 solids, not one connected solid: join its pieces into one body, "
                                 "or Factory splits them apart and prints the strays"])
        fails, _ = ks.part_failures(self.SHEETS, {"T03-plate": {"loose_reason": "turns"}}, {"T03-plate": 1},
                                    {"T03-plate": {**one, "pieces": 2}})
        self.assertIn("T03-plate is 2 solids", fails[0])

    def test_pieces_counts_solids_and_outer_shells_not_voids(self):
        from build123d import Box, Compound, Pos

        ks._runtime_paths()
        self.assertEqual(ks.pieces(Box(10, 10, 2)), 1)
        self.assertEqual(ks.pieces(Box(20, 20, 6) - Box(6, 6, 2)), 1)
        self.assertEqual(ks.pieces(Compound(children=[Box(10, 10, 2), Pos(20, 0, 0) * Box(4, 4, 2)])), 2)
        self.assertEqual(ks.pieces(Box(10, 10, 2) + Pos(30, 0, 0) * Box(4, 4, 2)), 2)

    def test_an_unmeasured_part_fails(self):
        fails, _ = ks.part_failures(self.SHEETS, {"A01-panel": {}}, {"A01-panel": 1}, {})
        self.assertIn("print_parts() did not measure it", fails[0])


class NearestCopyTest(unittest.TestCase):
    """2026-11-17: ``to_part`` skips a copy whose enclosing box lies farther
    than the best distance found, and is still the exact minimum of every
    pair: the same float, so the same Sheet verdict."""

    def test_the_pruned_nearest_distance_is_the_full_sweep_minimum(self):
        import random

        from build123d import Box, Cylinder, Pos, Rot, Sphere

        rng = random.Random(1117)
        for trial in range(4):
            shapes = []
            for _ in range(14):
                kind = rng.choice((Box(rng.uniform(2, 12), rng.uniform(2, 12), rng.uniform(1, 3)),
                                   Cylinder(rng.uniform(1, 5), rng.uniform(1, 3)),
                                   Sphere(rng.uniform(1, 4))))
                shapes.append(Pos(rng.uniform(0, 60), rng.uniform(0, 60), 0)
                              * Rot(0, 0, rng.uniform(0, 360)) * kind)
            boxes = [ks.enclosing_box(shape) for shape in shapes]
            for index, shape in enumerate(shapes):
                with self.subTest(trial=trial, index=index):
                    full = min(float(shape.distance_to(other)) for j, other in enumerate(shapes) if j != index)
                    self.assertEqual(ks.nearest_distance(index, shapes, boxes), full)

    def test_a_lone_copy_is_99_mm_from_any_other(self):
        from build123d import Box

        shape = Box(2, 2, 2)
        self.assertEqual(ks.nearest_distance(0, [shape], [ks.enclosing_box(shape)]), 99.0)

    def test_the_box_encloses_a_curved_face(self):
        from build123d import Cylinder

        shape = Cylinder(5, 2)
        xmin, ymin, zmin, xmax, ymax, zmax = ks.enclosing_box(shape)
        self.assertLessEqual(xmin, -5.0)
        self.assertGreaterEqual(xmax, 5.0)
        self.assertLessEqual(zmin, -1.0)
        self.assertGreaterEqual(zmax, 1.0)



PART_FILE = '''
from build123d import Align, Box, Compound, Pos
A = (Align.MIN, Align.MIN, Align.MIN)
SIZES = {sizes!r}
SPLIT = {split!r}  # Parts built as their box plus a stray bar cut free of it


def gen_step():
    return None


def _built(part, size):
    body = Box(*size, align=A)
    if part not in SPLIT:
        return body
    return Compound(children=[body, Pos(size[0] + 3, 0, 0) * Box(2, size[1], size[2], align=A)])


def print_parts():
    return {{part: _built(part, size) for part, size in SIZES.items()}}
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
        inkwell = next(p for p in tree["parts"] if p["id"] == "D01-inkwell")
        inkwell["loose_reason"] = "A round pot."
        inkwell["spares"] = 1  # 8 mm long: under 15 mm, a loose Part declares its spare
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

    def write_parts(self, inkwell, split=()):
        sizes = {"case": {"A01-case-shell": self.PANEL},
                 "cabinet": {"B01-cabinet-carcass": self.PANEL, "B02-cabinet-door": self.PANEL, "D01-inkwell": inkwell},
                 "desk": {"C01-desk-body": self.PANEL}}
        for role, parts in sizes.items():
            (self.project / ("part_%s.step.py" % role)).write_text(PART_FILE.format(sizes=parts, split=sorted(split)))

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

    def test_a_small_loose_part_without_spares_fails(self):
        inkwell = next(p for p in self.kit["assembly_tree"]["parts"] if p["id"] == "D01-inkwell")
        del inkwell["spares"]
        self.install()
        code, report = self.run_check()
        self.assertEqual(code, 1)
        self.assertEqual(report["failures"], ['D01-inkwell is 8.0 mm long, under 15, and prints loose with no '
                                              'spare: state "spares": 1 or more on its tree entry'])

    def test_a_kit_that_ships_no_spares_passes_without_them_and_says_so(self):
        tree = self.kit["assembly_tree"]
        inkwell = next(p for p in tree["parts"] if p["id"] == "D01-inkwell")
        del inkwell["spares"]
        tree["spares"] = "none"
        self.install()
        code, report = self.run_check()
        self.assertEqual((code, report["failures"], report["spares"]), (0, [], "none"))
        # The default kit's report carries no spares field.
        del tree["spares"]
        inkwell["spares"] = 1
        self.install()
        code, report = self.run_check()
        self.assertEqual(code, 0)
        self.assertNotIn("spares", report)

    def test_a_kit_that_ships_no_spares_refuses_a_declared_spare(self):
        self.kit["assembly_tree"]["spares"] = "none"
        self.install()
        code, report = self.run_check()
        self.assertEqual(code, 1)
        self.assertEqual(report["failures"], ['D01-inkwell declares spares, but the kit declares spares "none": '
                                              'remove its spares'])

    def test_a_loose_part_of_two_solids_fails(self):
        self.write_parts(inkwell=(8.0, 8.0, 8.0), split={"D01-inkwell"})
        code, report = self.run_check()
        self.assertEqual(code, 1)
        self.assertEqual(report["failures"], ["D01-inkwell is 2 solids, not one connected solid: join its pieces "
                                              "into one body, or Factory splits them apart and prints the strays"])

    def test_a_sheet_part_of_two_solids_fails(self):
        self.write_parts(inkwell=(8.0, 8.0, 8.0), split={"B02-cabinet-door"})
        code, report = self.run_check()
        self.assertEqual(code, 1)
        text = "\n".join(report["failures"])
        self.assertIn("B02-cabinet-door is 2 solids, not one connected solid", text)
        self.assertIn("sheet_B1.py: a copy of B02-cabinet-door is 2 solids, not one connected solid", text)

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

    def test_print_gates_only_starts_the_sheets_before_anything_else(self):
        """2026-11-17: the Sheets build what they check, so they start at
        once; on the Amsterdam kit they took about 15 minutes and waited
        behind every Part's gates. One at a time, they run first."""
        import os
        from unittest import mock

        from tests.make.test_make_round import load_module

        with mock.patch.dict(os.environ, {"MAKE_ROUND_JOBS": "1"}):
            self.round.main(load_module(), ["--print-gates-only"], 0)
        tools = [Path(c[1]).name for c in self.round.calls]
        self.assertEqual(tools[0], "kit_sheets.py", tools)
        first_gate = min(index for index, tool in enumerate(tools) if tool.startswith("check_"))
        self.assertLess(tools.index("kit_print_parts.py"), first_gate, "each Part is gated after describe")

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


class PrintCodeSpareTest(unittest.TestCase):
    """ADR 0092 amendment 2026-11-26: Parts sharing a ``print`` code are one
    print; each must measure the same, and the spare rule counts the code
    once over all its Parts."""

    CAP = {"size": [2.0, 5.0, 12.0], "volume": 120.0, "area": 180.0}
    TOTALS = {"L37-cap-a": 3, "L38-cap-b": 5}

    def sheets(self, a, b):
        return [{"id": "L1", "filament": "black", "parts": [{"id": "L37-cap-a", "count": a},
                                                          {"id": "L38-cap-b", "count": b}]}]

    def printed(self, code="L37"):
        return {part: ({"print": code} if code else {}) for part in self.TOTALS}

    def measures(self, b=None):
        return {"L37-cap-a": dict(self.CAP), "L38-cap-b": dict(b or self.CAP)}

    def test_a_shared_code_with_matching_geometry_counts_one_spare(self):
        self.assertEqual(ks.part_failures(self.sheets(4, 5), self.printed(), self.TOTALS, self.measures())[0], [])
        # Without the code each Part asks its own spare, as before.
        fails = ks.part_failures(self.sheets(4, 5), self.printed(None), self.TOTALS, self.measures())[0]
        self.assertEqual(fails, ["L38-cap-b is 12.0 mm long, under 15: its Sheets carry 5, the toy uses 5; "
                                 "add one spare"])
        # Under one code the print still needs its one spare.
        self.assertEqual(ks.part_failures(self.sheets(3, 5), self.printed(), self.TOTALS, self.measures())[0],
                         ["L37 is 12.0 mm long, under 15: its Sheets carry 8, the toy uses 8; add one spare"])

    def test_mismatched_geometry_under_one_code_is_refused(self):
        for other in ({**self.CAP, "volume": 130.0}, {**self.CAP, "area": 190.0},
                      {**self.CAP, "size": [2.0, 5.0, 12.5]}):
            fails = ks.part_failures(self.sheets(4, 5), self.printed(), self.TOTALS, self.measures(other))[0]
            self.assertIn("L37-cap-a and L38-cap-b share print code L37 but are not the same print", fails[0])
        # Rounding noise is no mismatch.
        close = {**self.CAP, "volume": 120.0004, "size": [2.0, 5.0, 12.001]}
        self.assertEqual(ks.part_failures(self.sheets(4, 5), self.printed(), self.TOTALS, self.measures(close))[0],
                         [])

    def test_a_kit_that_ships_no_spares_carries_a_shared_print_exactly(self):
        self.assertEqual(ks.part_failures(self.sheets(3, 5), self.printed(), self.TOTALS, self.measures(),
                                          no_spares=True)[0], [])
        self.assertEqual(ks.part_failures(self.sheets(4, 5), self.printed(), self.TOTALS, self.measures(),
                                          no_spares=True)[0],
                         ['L37: its Sheets carry 9, the toy uses 8, but the kit declares spares "none": '
                          'carry exactly 8'])

    def test_a_loose_shared_print_takes_one_spare_on_any_of_its_parts(self):
        printed = {part: {"print": "T37", "loose_reason": "round"} for part in ("T37-pin-a", "T38-pin-b")}
        totals = {"T37-pin-a": 2, "T38-pin-b": 2}
        measures = {part: dict(self.CAP) for part in printed}
        self.assertEqual(ks.part_failures([], printed, totals, measures)[0],
                         ['T37 is 12.0 mm long, under 15, and prints loose with no spare: state "spares": 1 '
                          'or more on its tree entry'])
        printed["T38-pin-b"]["spares"] = 1
        self.assertEqual(ks.part_failures([], printed, totals, measures)[0], [])


if __name__ == "__main__":
    unittest.main()
