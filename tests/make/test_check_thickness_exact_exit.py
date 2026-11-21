"""`check_thickness` reads a wall near the minimum exactly, not on the voxel grid.

A wall's two faces each land on a voxel boundary up to half a pitch from where
they are, and the march finds the exit one half-pitch step late or early. The
limit allowed only half a pitch for that, so a plane slab exactly at the 0.8 mm
minimum failed as a wall at some grid offsets (0.667 at the default 0.133 pitch,
0.69 at the 0.197 a whole kit sheet coarsens to) while a 0.75 mm slab passed at
0.277. A reading near the limit is now re-measured against the mesh triangles
and judged against the minimum itself; the minimum does not move.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import unittest
from pathlib import Path

from build123d import Cylinder, Pos

CAD = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts"


def _load():
    loader = importlib.machinery.SourceFileLoader("check_thickness_gate", str(CAD / "check_thickness"))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


GATE = _load()
PITCHES = (0.1333, 0.154, 0.197, 0.236, 0.277)


def _walls(tris, pitch):
    got = GATE._measure(tris, 0.8, 1.2, pitch)
    return [r for r in got["regions"] if r.get("kind") == "wall"], got


class ExactExitTest(unittest.TestCase):
    def test_slab_at_the_minimum_passes_at_every_pitch_and_offset(self):
        for pitch in PITCHES:
            for z0 in (0.0, 0.37):
                walls, got = _walls(GATE._slab(0, 0, z0, 40, 30, z0 + 0.8), pitch)
                self.assertEqual(walls, [], (pitch, z0))
                self.assertEqual(got["thin_share"], 0.0, (pitch, z0))
                self.assertGreater(got["exact"], 0, (pitch, z0))

    def test_slab_under_the_minimum_fails_at_every_pitch(self):
        for t in (0.75, 0.79):
            for pitch in PITCHES:
                walls, got = _walls(GATE._slab(0, 0, 0.37, 40, 30, 0.37 + t), pitch)
                self.assertTrue(walls, (t, pitch))
                self.assertAlmostEqual(min(r["thinnest"] for r in walls), t, places=6)
                self.assertGreater(got["thin_share"], 0.95, (t, pitch))

    def test_exact_reading_is_the_true_thickness(self):
        tris = GATE._slab(0, 0, 0.37, 40, 30, 1.17)
        verts, faces = GATE.weld(__import__("numpy").array(tris, dtype=float))
        import numpy as np
        pts = np.array([[10.0, 10.0, 1.17], [20.0, 5.0, 0.37]])
        dirs = np.array([[0, 0, -1.0], [0, 0, 1.0]])
        got = GATE.exact_exit(verts, faces, pts, dirs, np.array([2.0, 2.0]))
        np.testing.assert_allclose(got, [0.8, 0.8], atol=1e-9)
        # nothing within reach reads inf, so the grid reading stands
        self.assertTrue(np.isinf(GATE.exact_exit(verts, faces, pts, dirs, np.array([0.5, 0.5]))).all())

    def test_overlapping_solids_read_their_union(self):
        # a kit sheet cell: a copy (Z 0.998 to 3.0) sitting on a 1.0 gate bar as a separate solid, 0.002 into
        # it. A ray down from the bar's buried top crosses the copy's bottom first; the union is what prints.
        plate = GATE._slab(0, 0, 0.998, 20, 10, 3.0)
        bar = GATE._slab(5, 2, 0, 15, 8, 1.0)
        for pitch in (0.1333, 0.197):
            walls, _ = _walls(plate + bar, pitch)
            self.assertEqual(walls, [], pitch)

    def test_curved_shell_at_the_minimum_passes(self):
        shell = Pos(0, 0, 0) * Cylinder(10.0, 12.0).cut(Cylinder(9.2, 12.0))
        verts, faces = shell.tessellate(0.02, 0.1)
        pts = [(v.X, v.Y, v.Z) for v in verts]
        tris = [[list(pts[i]) for i in face] for face in faces]
        for pitch in (0.1333, 0.197):
            walls, _ = _walls(tris, pitch)
            self.assertEqual(walls, [], pitch)

    def test_the_minimum_itself_is_unchanged(self):
        self.assertAlmostEqual(GATE.thin_limit(0.8, 0.2), 0.7, places=6)
        import numpy as np
        mask = GATE.thin_mask(np.array([0.79, 0.7998, 0.72]), np.array([True, True, False]), 0.8, 0.2)
        self.assertEqual(mask.tolist(), [True, False, False])


if __name__ == "__main__":
    unittest.main()
