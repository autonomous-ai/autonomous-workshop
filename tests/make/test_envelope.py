"""B12 (ADR 0096 pilot): DETECT measures a STEP file's true envelope.

``inspect refs --facts`` gave the beaver coaster keeper a loose box on its
curved faces, 308.8 x 350.5 x 183.0 mm against the true 186.3 x 312.5 x
183.0, a false ``envelope`` finding. ``workshop.make.envelope`` reports the
union of every solid's exact bounding box, and refuses, rather than sizes, a
file it cannot read."""

from __future__ import annotations

import importlib.util
import json
from contextlib import redirect_stderr, redirect_stdout
import io
import tempfile
import unittest
from pathlib import Path

from workshop.make import envelope

HAS_CAD = importlib.util.find_spec("build123d") is not None


class UnionTest(unittest.TestCase):
    def test_union_of_boxes(self):
        self.assertEqual(
            envelope.union([[0, 0, 0, 1, 2, 3], [-1, 1, 0.5, 0.5, 4, 2]]),
            [-1, 0, 0, 1, 4, 3],
        )

    def test_no_box_is_refused(self):
        with self.assertRaises(envelope.EnvelopeError):
            envelope.union([])


class RefusalTest(unittest.TestCase):
    def test_a_missing_file_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.json"
            code = envelope.main([str(Path(tmp) / "missing.step"), "--json", str(out)])
            self.assertEqual(code, 2)
            self.assertFalse(out.exists())

    @unittest.skipUnless(HAS_CAD, "needs build123d")
    def test_an_unreadable_file_exits_2_with_a_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.step"
            bad.write_text("not a step file\n", encoding="utf-8")
            stdout, stderr = io.StringIO(), io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = envelope.main([str(bad)])
            self.assertEqual(code, 2)
            self.assertIn("envelope:", stderr.getvalue())
            self.assertEqual(stdout.getvalue(), "")


@unittest.skipUnless(HAS_CAD, "needs build123d")
class ExactEnvelopeTest(unittest.TestCase):
    def test_curved_solids_measure_their_exact_extents(self):
        import build123d as bd

        # A sphere and a tilted cylinder: curved faces whose loose box is
        # larger than the solid. The true envelope is analytic.
        sphere = bd.Pos(0, 0, 10) * bd.Sphere(10)
        cylinder = bd.Pos(40, 0, 0) * bd.Rot(0, 90, 0) * bd.Cylinder(5, 20)
        with tempfile.TemporaryDirectory() as tmp:
            step = Path(tmp) / "pair.step"
            bd.export_step(bd.Compound([sphere, cylinder]), str(step))
            out = Path(tmp) / "env.json"
            self.assertEqual(envelope.main([str(step), "--json", str(out)]), 0)
            report = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(report["solids"], 2)
        self.assertEqual(report["method"], envelope.METHOD)
        for got, want in zip(report["size"], [60.0, 20.0, 25.0]):
            self.assertAlmostEqual(got, want, delta=1e-3)
        for got, want in zip(report["bbox"], [-10.0, -10.0, -5.0, 50.0, 10.0, 20.0]):
            self.assertAlmostEqual(got, want, delta=1e-3)

    def test_a_step_with_no_solid_exits_2(self):
        import build123d as bd

        with tempfile.TemporaryDirectory() as tmp:
            step = Path(tmp) / "face.step"
            bd.export_step(bd.Face(bd.Rectangle(10, 10).wire()), str(step))
            with self.assertRaises(envelope.EnvelopeError):
                envelope.measure(step)


if __name__ == "__main__":
    unittest.main()
