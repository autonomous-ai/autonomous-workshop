"""Issue #108: check_mesh names the non-manifold edges it fails on.

A component round now runs check_mesh beside the thickness and overhang gates,
and its repair input has to say where the defect is, not only how many edges
it has. Two boxes fused along one shared edge give exactly one edge that four
faces share.
"""

from __future__ import annotations

import runpy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

SCRIPTS = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts"
MESHLIB = runpy.run_path(str(SCRIPTS / "meshlib.py"))

EDGE_SHARED = """from build123d import Align, Box, Pos


def gen_step():
    a = Box(10, 10, 10, align=(Align.MIN, Align.MIN, Align.MIN))
    b = Pos(10, 10, 0) * Box(10, 10, 10, align=(Align.MIN, Align.MIN, Align.MIN))
    return a.fuse(b)
"""
SOUND = """from build123d import Box


def gen_step():
    return Box(10, 10, 10)
"""


def run_check_mesh(source: str) -> subprocess.CompletedProcess:
    with tempfile.TemporaryDirectory() as tmp:
        part = Path(tmp) / "part_block.step.py"
        part.write_text(source)
        return subprocess.run([sys.executable, str(SCRIPTS / "check_mesh"), str(part)], cwd=tmp,
                              capture_output=True, text=True, timeout=300)


class NonManifoldEdgesTest(unittest.TestCase):
    def test_summarize_lists_each_edge_more_than_two_faces_share(self):
        # Two tetrahedra-like fans sharing the edge (0,0,0)-(0,0,1) with a third face on it.
        verts = np.array([[0, 0, 0], [0, 0, 1], [1, 0, 0], [0, 1, 0], [-1, 0, 0]], dtype=float)
        faces = np.array([[0, 1, 2], [1, 0, 3], [0, 1, 4]])
        summary = MESHLIB["summarize"](verts, faces)
        self.assertEqual(summary["nonmanifold_edges"], 1)
        self.assertEqual(summary["nonmanifold_at"], [{"a": [0.0, 0.0, 0.0], "b": [0.0, 0.0, 1.0], "faces": 3}])

    def test_a_non_manifold_part_fails_and_names_the_edge(self):
        try:
            import build123d  # noqa: F401
        except ImportError:  # pragma: no cover
            self.skipTest("build123d is not installed")
        done = run_check_mesh(EDGE_SHARED)
        self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
        self.assertIn("FAIL  manifold edges", done.stdout)
        self.assertIn("1. [edge ] (10.00, 10.00, 0.00) - (10.00, 10.00, 10.00)  4 faces", done.stdout)

    def test_a_sound_part_passes_and_names_no_edge(self):
        try:
            import build123d  # noqa: F401
        except ImportError:  # pragma: no cover
            self.skipTest("build123d is not installed")
        done = run_check_mesh(SOUND)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertNotIn("[edge ]", done.stdout)
        self.assertIn("RESULT: printable", done.stdout)


if __name__ == "__main__":
    unittest.main()
