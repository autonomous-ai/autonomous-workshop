"""Issues #165 and #166: `gen --write` reports the B-rep identity of the shape
a part's STEP export holds, however that export's bytes were written.

A STEP export of an unchanged shape is not byte-reproducible, and the Colour
Module reaches a part only through its import closure. So a recolour must
re-export the STEP in its new colour, and a current export (after `--force`
or a fresh verifier run) must still report the identity of the shape it was
built from; make_round then never records an export's bytes as the shape a
review judged.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from workshop.runtime.package_data import product_run_domain_skill_roots

from tests.make.test_make_round import load_module

CAD_SCRIPTS = product_run_domain_skill_roots()["cad"] / "scripts"
HAS_CAD = importlib.util.find_spec("build123d") is not None and importlib.util.find_spec("OCP") is not None

COLOURS = '"""Filament choices."""\nHEAD = (%r, "catalogue")\n'

PART = """\
from build123d import Box, Color, Cylinder

from colours import HEAD

COLOURS = {"mint": (0.6, 0.9, 0.75), "green": (0.0, 0.73, 0.19)}


def gen_step():
    shape = Box(12, 10, 6) - Cylinder(2, 20)
    shape.color = Color(*COLOURS[HEAD[0]])
    shape.label = "head"
    return shape
"""


@unittest.skipUnless(HAS_CAD, "needs build123d and OCP")
class StepExportIdentityTest(unittest.TestCase):
    def _gen(self, project: Path, *extra: str, write: bool = True) -> dict:
        environment = dict(os.environ, CADGEN_WARM="0")
        done = subprocess.run(
            [sys.executable, str(CAD_SCRIPTS / "gen"), "part_head.step.py", *(["--write"] if write else []),
             "--json", *extra],
            cwd=project, env=environment, capture_output=True, text=True, timeout=600)
        self.assertEqual(done.returncode, 0, done.stderr[-2000:])
        return json.loads(done.stdout.strip().splitlines()[-1])

    def _step(self, project: Path) -> str:
        return hashlib.sha256((project / "part_head.step").read_bytes()).hexdigest()

    def test_a_recolour_re_exports_and_a_re_export_keeps_the_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "colours.py").write_text(COLOURS % "mint")
            (project / "part_head.step.py").write_text(PART)

            built = self._gen(project)
            self.assertEqual(built["outcome"], "built")
            identity, mint = built["identitySha256"], self._step(project)

            current = self._gen(project)
            self.assertEqual(current["outcome"], "current")
            self.assertEqual(current["identitySha256"], identity)
            self.assertEqual(self._step(project), mint)

            # Issue #165: a recolour reaches the part only through colours.py,
            # and a `gen` without --write recomposes the render package in the
            # new colour first, leaving the export behind it.
            (project / "colours.py").write_text(COLOURS % "green")
            self.assertEqual(self._gen(project, write=False)["outcome"], "built")
            self.assertEqual(self._step(project), mint)
            recoloured = self._gen(project)
            self.assertEqual(recoloured["outcome"], "built")
            self.assertEqual(recoloured["identitySha256"], identity)
            green = self._step(project)
            self.assertNotEqual(green, mint)

            # Issue #166: --force writes new bytes for the same shape, and the
            # next current run reports that shape, not the bytes.
            forced = self._gen(project, "--force")
            self.assertEqual(forced["identitySha256"], identity)
            after = self._gen(project)
            self.assertEqual(after["outcome"], "current")
            self.assertEqual(after["identitySha256"], identity)
            # make_round's own reader of a Component's current geometry (the
            # interface check and its staleness) sees the shape, not the bytes.
            out = project / "measure" / "probe"
            out.mkdir(parents=True)
            self.assertEqual(load_module().component_identity(project, "head", out, CAD_SCRIPTS), identity)

            # A STEP put back from elsewhere is not the recorded export.
            (project / "part_head.step").write_bytes(b"ISO-10303-21;\nEND-ISO-10303-21;\n")
            restored = self._gen(project)
            self.assertEqual(restored["outcome"], "built")
            self.assertEqual(restored["identitySha256"], identity)


if __name__ == "__main__":
    unittest.main()
