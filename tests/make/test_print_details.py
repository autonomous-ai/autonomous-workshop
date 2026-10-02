"""The print-details skill: printable decorative detail for Component Workers."""

import hashlib
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from workshop.runtime.package_data import product_run_domain_skill_roots


REPOSITORY = Path(__file__).resolve().parents[2]
ROOT = product_run_domain_skill_roots()["print-details"]
SCRIPT = ROOT / "scripts" / "print_details.py"


def load_module():
    spec = importlib.util.spec_from_file_location("workshop_test_print_details", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class PrintDetailsSkillTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()
        from build123d import Box, Pos

        cls.block = Pos(0, 0, 6) * Box(24, 24, 12)

    def test_skill_is_registered_with_its_tool_card(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\nname: print-details\n"))
        for call in ("boss(", "rivet(", "rivets(", "dome(", "band(", "rim(", "pipe(",
                     "panel(", "window(", "slit(", "slits(", "--install", "--self-check",
                     "--limits", "features/print_details.py"):
            self.assertIn(call, text)
        self.assertTrue(SCRIPT.is_file())
        self.assertTrue(SCRIPT.stat().st_mode & 0o100)

    def test_self_check_passes_under_the_workshop_python(self):
        done = subprocess.run(
            [sys.executable, str(SCRIPT), "--self-check"],
            capture_output=True, text=True, timeout=1800,
        )
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn("pass both print gates, and every limit refuses", done.stdout)
        self.assertNotIn("FAIL", done.stdout)

    def test_a_size_below_a_limit_is_refused_naming_the_limit_and_its_page(self):
        pd = self.module.Details(nozzle=0.4)
        top = (0, 0, 12)
        line = pd.segment((-5, 0, 12), (5, 0, 12))
        cases = (
            (lambda: pd.rivet(self.block, top, d=1.9), "min feature", "fdm-minimum-feature-sizes.md"),
            (lambda: pd.boss(self.block, top, h=0.4), "min relief height", "fdm-minimum-feature-sizes.md"),
            (lambda: pd.dome(self.block, top, d=1.9, h=0.6), "min feature", "fdm-minimum-feature-sizes.md"),
            (lambda: pd.band(self.block, line, width=0.85), "min relief width", "fdm-minimum-feature-sizes.md"),
            (lambda: pd.pipe(self.block, line, d=0.85), "min relief width", "fdm-minimum-feature-sizes.md"),
            (lambda: pd.slit(self.block, top, width=0.45), "min cut width", "fdm-minimum-feature-sizes.md"),
            (lambda: pd.panel(self.block, top, depth=0.45), "min cut depth", "fdm-minimum-feature-sizes.md"),
            (lambda: pd.slits(self.block, pd.along((-2, 0, 12), (2, 0, 12), 3), width=1.2),
             "min web", "wall-thickness-and-hollowing.md"),
            (lambda: pd.dome(self.block, (0, -12, 6), d=8, h=3),
             "", "overhangs-and-print-orientation.md"),
            (lambda: pd.window(self.block, (0, -12, 6), arch="flat", depth=2),
             "", "overhangs-and-print-orientation.md"),
        )
        for probe, limit, page in cases:
            with self.subTest(limit=limit, page=page):
                with self.assertRaises(self.module.PrintLimitError) as raised:
                    probe()
                self.assertIn(limit, str(raised.exception))
                self.assertIn(".agents/skills/wiki/pages/printing/" + page, str(raised.exception))

    def test_defaults_build_one_valid_solid_on_a_top_face_and_a_wall(self):
        pd = self.module.Details()
        for spot in ((0, 0, 12), (0, -12, 6)):
            for name, call in (
                ("boss", lambda: pd.boss(self.block, spot)),
                ("rivet", lambda: pd.rivet(self.block, spot)),
                ("dome", lambda: pd.dome(self.block, spot)),
                ("panel", lambda: pd.panel(self.block, spot, height=8)),
                ("slit", lambda: pd.slit(self.block, spot)),
            ):
                with self.subTest(feature=name, spot=spot):
                    result = call()
                    self.assertEqual(len(result.solids()), 1)
                    self.assertTrue(result.is_valid)
                    self.assertNotAlmostEqual(result.volume, self.block.volume, places=3)

    def test_limits_follow_the_nozzle(self):
        fine, coarse = self.module.limits(0.4), self.module.limits(0.6)
        self.assertEqual(fine["min_wall"][0], 0.8)
        self.assertEqual(fine["min_feature"][0], 2.0)
        self.assertAlmostEqual(fine["min_relief_width"][0], 0.9)
        self.assertAlmostEqual(fine["min_cut_width"][0], 0.5)
        self.assertAlmostEqual(coarse["min_wall"][0], 1.2)
        self.assertAlmostEqual(coarse["min_feature"][0], 2.4)
        self.assertGreater(coarse["min_relief_width"][0], fine["min_relief_width"][0])
        for name, (_value, _unit, page, _why) in fine.items():
            with self.subTest(limit=name):
                self.assertTrue(
                    (REPOSITORY / "src/workshop/make/skills/wiki/pages" / page).is_file(), page)

    def test_install_copies_the_exact_bytes_and_refuses_an_edited_copy(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            digest = self.module.install(project)
            copy = project / "features" / "print_details.py"
            self.assertEqual(copy.read_bytes(), SCRIPT.read_bytes())
            self.assertEqual(digest, hashlib.sha256(SCRIPT.read_bytes()).hexdigest())
            self.assertEqual(self.module.install(project), digest)
            copy.write_text("EDITED = True\n", encoding="utf-8")
            with self.assertRaises(SystemExit):
                self.module.install(project)

    def test_the_reviewer_asks_within_the_library_limits(self):
        reviewer = " ".join(
            (REPOSITORY / "src/workshop/make/agents/component-reviewer.toml").read_text(encoding="utf-8").split())
        for phrase in ("0.8 mm", "at least 2 mm across", "at least 0.9 mm wide",
                       "at least 0.5 mm wide", "0.5 mm high", "0.5 mm deep", "1.6 mm",
                       "45 degrees", "print-details"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, reviewer)

    def test_workers_and_the_make_reference_name_the_library(self):
        worker = " ".join(
            (REPOSITORY / "src/workshop/make/agents/component-worker.toml").read_text(encoding="utf-8").split())
        make = " ".join((REPOSITORY / ".agents/product-run/.agents/skills/autonomous-workshop/references/make.md"
                         ).read_text(encoding="utf-8").split())
        self.assertIn("from features import print_details", worker)
        self.assertIn(".agents/skills/print-details/scripts/print_details.py --install", make)


if __name__ == "__main__":
    unittest.main()
