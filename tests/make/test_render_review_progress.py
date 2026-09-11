"""CLI phase diagnostics survive failure without changing rendered evidence."""
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch

from tests.make.test_make_round import load_module


RENDERER = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts/render_review"
PREFIX = "render_review progress: "


class ReviewProgressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = runpy.run_path(str(RENDERER))

    def records(self, output):
        return [json.loads(line[len(PREFIX):]) for line in output.splitlines()
                if line.startswith(PREFIX)]

    def test_cli_paths_and_png_bytes_match_quiet_library_with_exact_counts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "assembly.step.py"
            source.write_text(
                "from build123d import Box, Color, Compound\n"
                "def gen_step():\n"
                "    red = Box(4, 5, 6)\n"
                "    red.color = Color(1, 0, 0)\n"
                "    return Compound(children=[red, Box(2, 3, 4).translate((7, 0, 0))])\n")
            stdout, stderr = io.StringIO(), io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                _, shape = self.tool["build_shape"](source)
                occurrences = self.tool["tessellate_occurrences"](shape, .08)
                expected = {}
                for view in ("front", "iso"):
                    azimuth, elevation = self.tool["NAMED_VIEWS"][view]
                    image = self.tool["render"](occurrences, azimuth, elevation, 128, .07)
                    buffer = io.BytesIO()
                    image.save(buffer, format="PNG")
                    expected[view] = buffer.getvalue()
            self.assertEqual(stdout.getvalue(), "")
            self.assertEqual(stderr.getvalue(), "")

            out = root / "images"
            with redirect_stdout(stdout), redirect_stderr(stderr):
                status = self.tool["main"]([str(source), "--view", "front", "--view", "iso",
                                            "--size", "128", "-o", str(out)])
            self.assertEqual(status, 0)
            self.assertEqual(stdout.getvalue().splitlines(),
                             [str(out / "front.png"), str(out / "iso.png")])
            for view, data in expected.items():
                self.assertEqual((out / f"{view}.png").read_bytes(), data)
            records = self.records(stderr.getvalue())
            self.assertEqual([(r["phase"], r["event"]) for r in records], [
                (phase, event) for phase in ("source-load-build", "tessellation", "raster-save", "raster-save")
                for event in ("start", "complete")])
            counts = records[3]
            self.assertEqual(counts["occurrences"], len(occurrences))
            self.assertEqual(counts["vertices"], sum(len(points) for points, _, _ in occurrences))
            self.assertEqual(counts["triangles"], sum(len(faces) for _, faces, _ in occurrences))
            self.assertEqual([r["view"] for r in records if r["phase"] == "raster-save"],
                             ["front", "front", "iso", "iso"])
            self.assertTrue(all(r["elapsed_seconds"] >= 0 for r in records if r["event"] == "complete"))
            self.assertEqual(len(stderr.getvalue().splitlines()), len(records))

    def test_phase_failure_propagates_without_completion_or_success_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "assembly.step.py"
            source.write_text("from build123d import Box\ndef gen_step(): return Box(2, 3, 4)\n")
            for function, phase in (("build_shape", "source-load-build"),
                                    ("tessellate_occurrences", "tessellation"),
                                    ("render", "raster-save")):
                with self.subTest(phase=phase):
                    stdout, stderr = io.StringIO(), io.StringIO()
                    failure = RuntimeError("synthetic phase failure")
                    def fail(*args, **kwargs):
                        raise failure
                    with patch.dict(self.tool["main"].__globals__, {function: fail}), \
                            redirect_stdout(stdout), redirect_stderr(stderr):
                        with self.assertRaises(RuntimeError) as raised:
                            self.tool["main"]([str(source), "--size", "128", "-o", str(root / "out")])
                    self.assertIs(raised.exception, failure)
                    records = self.records(stderr.getvalue())
                    self.assertEqual((records[-1]["phase"], records[-1]["event"]), (phase, "start"))
                    self.assertEqual(stdout.getvalue(), "")
                    self.assertFalse((root / "out" / "iso.png").exists())

    def test_real_runner_timeout_preserves_flushed_source_phase_and_failure(self):
        runner = load_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "assembly.step.py"
            source.write_text("import time\ndef gen_step():\n    time.sleep(30)\n")
            log = root / "visual-render.log"
            done = runner.run([sys.executable, str(RENDERER), str(source), "--size", "128",
                               "-o", str(root / "out")], cwd=root, log=log, timeout=2)
            self.assertEqual(done.returncode, 124)
            text = log.read_text()
            self.assertIn("TIMEOUT after 2s", text)
            self.assertIn('"phase": "source-load-build"', text)
            self.assertIn('"event": "start"', text)
            self.assertNotIn('"event": "complete"', text)
            self.assertFalse(done.stdout)
            self.assertFalse((root / "out" / "iso.png").exists())


if __name__ == "__main__":
    unittest.main()
