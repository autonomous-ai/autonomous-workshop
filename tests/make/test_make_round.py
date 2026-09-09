"""The make-round skill: one Make iteration as one command."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

from workshop.runtime.package_data import product_run_domain_skill_roots

SCRIPT = product_run_domain_skill_roots()["make-round"] / "scripts" / "make_round"


def load_module():
    spec = importlib.util.spec_from_loader("make_round_script", loader=None)
    module = importlib.util.module_from_spec(spec)
    code = compile(SCRIPT.read_text(encoding="utf-8"), str(SCRIPT), "exec")
    module.__file__ = str(SCRIPT)
    exec(code, module.__dict__)
    return module


class MakeRoundTest(unittest.TestCase):
    def test_skill_is_registered_with_its_tool_card(self):
        root = product_run_domain_skill_roots()["make-round"]
        text = (root / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\nname: make-round\n"))
        for tool in ("export", "check_thickness", "render_views.py", "check_motion", "verify_project"):
            self.assertIn(tool, text)
        self.assertIn("at most once per round", text)
        self.assertTrue(SCRIPT.is_file())
        self.assertTrue(SCRIPT.stat().st_mode & 0o100)

    def test_self_check_passes_under_the_workshop_python(self):
        done = subprocess.run(
            [sys.executable, str(SCRIPT), "--self-check"], capture_output=True, text=True, timeout=120
        )
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn("all fixtures pass", done.stdout)

    def test_pure_helpers_read_tool_output_and_diff_rounds(self):
        module = load_module()
        parsed = module.parse_thickness(
            "  FAIL  wall >= 0.80 mm  9 samples\n        1. [wall ] 0.71 mm at (0, 0, 0)\nRESULT: WALL BELOW MINIMUM\n"
        )
        self.assertEqual((parsed["verdict"], parsed["thinnest_mm"]), ("FAIL", 0.71))
        self.assertEqual(module.diff_parts({"a": "x"}, {"a": "x", "b": "y"}), ["b"])
        self.assertEqual(module.parse_refs(["hero=ref/hero.png"], []), [("hero", "ref/hero.png")])
        # render_views --json prints one pretty-printed object whose ``views`` carry the IoU.
        stdout = json.dumps(
            {"source": "/p/cad/duck.step.py", "views": [{"label": "hero", "iou": 0.9029, "ok": True, "az": -82.5, "el": -1.875}], "ok": True},
            indent=2,
        )
        self.assertEqual(module.parse_render_views(stdout, "hero")["iou"], 0.9029)
        self.assertIsNone(module.parse_render_views(stdout, "side"))
        self.assertIsNone(module.parse_render_views("no json here\n", "hero"))
        summary = {
            "round": 1, "project": "/p", "parts": ["a"], "changed": ["a"], "checked": ["a"],
            "thickness": {"a": {"verdict": "PASS", "thinnest_mm": None, "failures": []}},
            "likeness": [], "min": 0.9, "motion": None, "full": None, "ok": True, "out": "/p/measure/rounds/r0001",
        }
        self.assertTrue(module.render_summary(summary).splitlines()[-1].startswith("  PASS"))

    def test_a_directory_without_an_entry_cannot_run(self):
        import tempfile

        with tempfile.TemporaryDirectory() as temporary:
            done = subprocess.run(
                [sys.executable, str(SCRIPT), temporary], capture_output=True, text=True, timeout=120
            )
        self.assertEqual(done.returncode, 2)
        self.assertIn("entry", done.stderr)


if __name__ == "__main__":
    unittest.main()
