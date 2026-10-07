"""The print gates name the failing feature and tell an open mesh apart (#82)."""

import contextlib
import io
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

from workshop.runtime.package_data import product_run_domain_skill_roots


ROOTS = product_run_domain_skill_roots()
SCRIPTS = ROOTS["cad"] / "scripts"
LIBRARY = ROOTS["print-details"] / "scripts" / "print_details.py"


def printlib():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    import printlib as module
    return module


def box_soup(x1=10.0, y1=10.0, z1=5.0, *, open_top=False):
    """A closed axis-aligned box as triangle soup; `open_top` drops its lid."""
    box = runpy.run_path(str(SCRIPTS / "check_overhang"))["_box"]
    tris = box(0, 0, 0, x1, y1, z1)
    if open_top:
        tris = tris[2:]
    return np.asarray(tris, dtype=float)


def bowtie():
    """A shape that is not a valid B-rep: one face bounded by a self-crossing wire."""
    from build123d import Compound, Face, Wire
    return Compound(children=[Face(Wire.make_polygon(
        [(0, 0, 0), (10, 10, 0), (10, 0, 0), (0, 10, 0)], close=True))])


class PrintedMeshTest(unittest.TestCase):
    """`printlib.printed_mesh`: what an open tessellation means."""

    def test_a_closed_mesh_is_measured_as_tessellated(self):
        lib = printlib()
        calls = []

        def mesh(shape, deviation, angular):
            calls.append(deviation)
            return box_soup()
        record = lib.printed_mesh(object(), mesh=mesh)
        self.assertEqual(record["status"], "closed")
        self.assertFalse(record["retessellated"])
        self.assertEqual(calls, [lib.MESH_DEVIATION])

    def test_an_invalid_brep_with_open_edges_reports_its_invalid_faces(self):
        lib = printlib()
        record = lib.printed_mesh(bowtie(), mesh=lambda *_: box_soup(open_top=True))
        self.assertEqual(record["status"], "invalid")
        self.assertGreater(record["open_edges"], 0)
        self.assertEqual([face["index"] for face in record["invalid_faces"]], [0])
        self.assertEqual(record["invalid_faces"][0]["centre"], (5.0, 5.0, 0.0))
        text = "\n".join(lib.mesh_refusal("part_x.step.py", record))
        self.assertIn("not a valid solid", text)
        self.assertIn("face 0 (plane", text)
        self.assertIn("centred at (5.0, 5.0, 0.0)", text)

    def test_a_valid_solid_whose_coarse_mesh_is_open_passes_after_the_finer_retry(self):
        from build123d import Box
        lib = printlib()
        calls = []

        def mesh(shape, deviation, angular):
            calls.append((deviation, angular))
            return box_soup(open_top=deviation == lib.MESH_DEVIATION)
        record = lib.printed_mesh(Box(10, 10, 5), mesh=mesh)
        self.assertEqual(record["status"], "closed")
        self.assertTrue(record["retessellated"])
        self.assertEqual(record["deviation"], lib.FINE_DEVIATION)
        self.assertEqual(calls, [(lib.MESH_DEVIATION, lib.MESH_ANGULAR),
                                 (lib.FINE_DEVIATION, lib.FINE_ANGULAR)])
        self.assertIsNotNone(record["faces"])

    def test_a_valid_solid_whose_mesh_stays_open_is_unmeasurable(self):
        from build123d import Box
        lib = printlib()
        record = lib.printed_mesh(Box(10, 10, 5), mesh=lambda *_: box_soup(open_top=True))
        self.assertEqual(record["status"], "unmeasurable")
        self.assertIsNone(record["faces"])
        text = "\n".join(lib.mesh_refusal("part_x.step.py", record))
        self.assertIn("valid solid", text)
        self.assertIn("has not failed a print limit", text)


class GateRefusalTest(unittest.TestCase):
    """Both gates turn an unmeasured mesh into its own verdict and report."""

    def run_gate(self, gate, record):
        module = runpy.run_path(str(SCRIPTS / gate))
        main = module["main"]
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "report.md"
            entry = Path(tmp) / "part_fixture.step.py"
            patches = {
                "resolve_single_entry": lambda _: entry,
                "entry_role": lambda _: "fixture",
                "entry_shape": lambda *_: None,
                "printed_mesh": lambda _shape: record,
            }
            out = io.StringIO()
            with mock.patch.dict(main.__globals__, patches), \
                    mock.patch.object(sys, "argv", [gate, str(entry), "--report", str(report)]), \
                    contextlib.redirect_stdout(out):
                code = main()
            return code, out.getvalue(), report.read_text(encoding="utf-8")

    def test_a_persistent_open_mesh_is_unmeasurable_not_a_failure(self):
        record = {"status": "unmeasurable", "open_edges": 6, "invalid_faces": None}
        for gate in ("check_thickness", "check_overhang"):
            with self.subTest(gate=gate):
                code, stdout, report = self.run_gate(gate, record)
                self.assertEqual(code, 4)
                self.assertIn("RESULT: UNMEASURABLE MESH", stdout)
                self.assertNotIn("FAIL", stdout)
                self.assertEqual(report.count("RESULT:"), 1)
                self.assertTrue(report.rstrip().endswith("RESULT: UNMEASURABLE MESH"))

    def test_an_invalid_solid_fails_with_its_faces_listed(self):
        record = {"status": "invalid", "open_edges": 3, "invalid_faces": [
            {"index": 4, "type": "bspline", "area": 1.5, "centre": (1.0, 2.0, 3.0)}]}
        for gate in ("check_thickness", "check_overhang"):
            with self.subTest(gate=gate):
                code, stdout, report = self.run_gate(gate, record)
                self.assertEqual(code, 1)
                self.assertIn("RESULT: INVALID SOLID", stdout)
                self.assertIn("face 4 (bspline, 1.50 mm2) centred at (1.0, 2.0, 3.0)", report)


class MeshGateAgreementTest(unittest.TestCase):
    """`check_mesh`, which final verification runs first, reads the same
    `printed_mesh` as the two gates a component round runs: a part that passes
    its rounds is not refused at the end for a tessellation they retried."""

    def run_gate(self, gate, record):
        module = runpy.run_path(str(SCRIPTS / gate))
        main = module["main"]
        with tempfile.TemporaryDirectory() as tmp:
            entry = Path(tmp) / "part_fixture.step.py"
            argv = [gate, str(entry)]
            if gate != "check_mesh":
                argv += ["--report", str(Path(tmp) / "report.md")]
            patches = {
                "resolve_single_entry": lambda _: entry,
                "entry_role": lambda _: "fixture",
                "entry_shape": lambda *_: None,
                "printed_mesh": lambda _shape: record,
            }
            out = io.StringIO()
            with mock.patch.dict(main.__globals__, patches), \
                    mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(out):
                code = main()
            return code, out.getvalue()

    def retried_box(self):
        lib = printlib()
        return lib.printed_mesh(
            object(), mesh=lambda _shape, deviation, _angular:
            box_soup(open_top=deviation == lib.MESH_DEVIATION))

    def test_a_mesh_closed_by_the_finer_retry_passes_check_mesh_as_it_passes_the_gates(self):
        lib = printlib()
        lib.invalid_faces, saved = (lambda _shape: None), lib.invalid_faces
        try:
            record = self.retried_box()
        finally:
            lib.invalid_faces = saved
        self.assertTrue(record["retessellated"])
        for gate in ("check_mesh", "check_thickness", "check_overhang"):
            with self.subTest(gate=gate):
                code, stdout = self.run_gate(gate, record)
                self.assertEqual(code, 0, stdout)
        _, stdout = self.run_gate("check_mesh", record)
        self.assertIn("PASS  watertight (no open edges)", stdout)
        self.assertIn("closed only at the finer", stdout)
        self.assertIn("RESULT: printable", stdout)

    def test_check_mesh_gives_the_same_verdict_as_the_gates_on_an_unmeasured_mesh(self):
        records = {
            4: {"status": "unmeasurable", "open_edges": 6, "invalid_faces": None},
            1: {"status": "invalid", "open_edges": 3, "invalid_faces": [
                {"index": 4, "type": "bspline", "area": 1.5, "centre": (1.0, 2.0, 3.0)}]},
        }
        for expected, record in records.items():
            for gate in ("check_mesh", "check_thickness", "check_overhang"):
                with self.subTest(gate=gate, status=record["status"]):
                    code, _ = self.run_gate(gate, record)
                    self.assertEqual(code, expected)
        _, stdout = self.run_gate("check_mesh", records[4])
        self.assertIn("RESULT: UNMEASURABLE MESH", stdout)
        self.assertNotIn("FAIL", stdout)
        _, stdout = self.run_gate("check_mesh", records[1])
        self.assertIn("RESULT: INVALID SOLID", stdout)
        self.assertIn("face 4 (bspline, 1.50 mm2) centred at (1.0, 2.0, 3.0)", stdout)


ENTRY_HEAD = "from build123d import *\nfrom features import print_details\nPRINTABLE = True\n"


class FeatureNamingTest(unittest.TestCase):
    """A failing region names its print-details feature, else its B-rep face."""

    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.project = Path(cls.temporary.name)
        (cls.project / "features").mkdir()
        shutil.copyfile(LIBRARY, cls.project / "features" / "print_details.py")

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def gate(self, gate, name, body, *extra):
        entry = self.project / ("part_%s.step.py" % name)
        entry.write_text(ENTRY_HEAD + body, encoding="utf-8")
        report = self.project / ("%s-%s.md" % (gate, name))
        done = subprocess.run(
            [sys.executable, str(SCRIPTS / gate), entry.name, *extra, "--report", str(report)],
            cwd=self.project, capture_output=True, text=True, timeout=600)
        return done, report.read_text(encoding="utf-8") if report.is_file() else ""

    def test_a_failing_tagged_feature_is_named_with_its_call_site(self):
        # A 0.8 mm panel cut into a 1.2 mm plate leaves a 0.4 mm floor.
        done, report = self.gate("check_thickness", "thin_panel", (
            "pd = print_details.Details(nozzle=0.4)\n"
            "def gen_step():\n"
            "    plate = Pos(0, 0, 0.6) * Box(30, 30, 1.2)\n"
            "    return pd.panel(plate, (0, 0, 1.2), width=10, height=10, depth=0.8)\n"))
        self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
        self.assertIn("at feature panel@part_thin_panel.step.py:7 -- panel-1 "
                      "(part_thin_panel.step.py:7)", done.stdout)
        self.assertIn("mm under the 0.80 mm wall", done.stdout)
        self.assertIn("| panel-1 (part_thin_panel.step.py:7), ", report)

    def test_an_overhang_on_a_tagged_feature_is_named_with_how_far_it_is_past(self):
        # A boss built for the wrong print direction: its support is swept up,
        # so in the real print its round underside hangs.
        done, report = self.gate("check_overhang", "upside_boss", (
            "pd = print_details.Details(nozzle=0.4, up=(0, 0, -1))\n"
            "def gen_step():\n"
            "    block = Pos(0, 0, 10) * Box(20, 20, 20)\n"
            "    return pd.boss(block, (0, -10, 10), d=6, h=3)\n"), "--angle", "45")
        self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
        self.assertIn("at feature boss@part_upside_boss.step.py:7", done.stdout)
        self.assertRegex(done.stdout, r"steepest \d+ deg from vertical, \d+ deg past the 45 deg limit")
        self.assertIn("mm past the 1.0 mm ledge", report)

    def test_an_untagged_region_falls_back_to_its_nearest_face(self):
        done, report = self.gate("check_thickness", "fin", (
            "def gen_step():\n"
            "    return Pos(0, 0, 5) * Box(20, 20, 10) + Pos(0, 0, 15) * Box(12, 0.5, 10)\n"))
        self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
        self.assertRegex(done.stdout, r"at face plane@\(-?\d+,-?\d+,-?\d+\) -- face \d+ \(plane, ")
        self.assertIn("no print-details feature within 1 mm", report)

    def test_a_wall_exactly_at_the_minimum_passes(self):
        # A 0.8 mm tile reads one march step low, exactly at the gate's limit;
        # float rounding must not tip that reading under it.
        done, _ = self.gate("check_thickness", "min_tile", (
            "def gen_step():\n"
            "    return Pos(0, 0, 0.4) * Box(2.0, 2.0, 0.8)\n"), "--nozzle", "0.4")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)

    def test_a_passing_entry_keeps_its_verdict(self):
        body = ("pd = print_details.Details(nozzle=0.4)\n"
                "def gen_step():\n"
                "    block = Pos(0, 0, 6) * Box(24, 24, 12)\n"
                "    return pd.rivets(block, pd.along((-6, 0, 12), (6, 0, 12), 3))\n")
        for gate in ("check_thickness", "check_overhang"):
            with self.subTest(gate=gate):
                done, report = self.gate(gate, "rivets", body)
                self.assertEqual(done.returncode, 0, done.stdout + done.stderr)


if __name__ == "__main__":
    unittest.main()
