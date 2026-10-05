"""The print-details skill: printable decorative detail for Component Workers."""

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from workshop.runtime.package_data import product_run_domain_skill_roots


REPOSITORY = Path(__file__).resolve().parents[2]
ROOT = product_run_domain_skill_roots()["print-details"]
SCRIPT = ROOT / "scripts" / "print_details.py"
CAD = product_run_domain_skill_roots()["cad"] / "scripts"


def load_module():
    spec = importlib.util.spec_from_file_location("workshop_test_print_details", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_printlib():
    spec = importlib.util.spec_from_file_location("workshop_test_printlib", CAD / "printlib.py")
    module = importlib.util.module_from_spec(spec)
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
                     "panel(", "window(", "slit(", "slits(", "bore(", "blunt_tip(", "rib_end(",
                     "flat land at least one print minimum across",
                     "never from\na geometry's `wall_min_mm`", "--install", "--self-check",
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

    def test_every_feature_is_tagged_with_the_line_that_made_it(self):
        from build123d import Box, Pos
        pd = self.module.Details()
        self.module.PRINT_DETAIL_TAGS.clear()
        body = pd.rivet(self.block, (0, 0, 12))
        body = pd.band(body, pd.segment((-8, -12, 6), (8, -12, 6)))
        body = pd.panel(body, (6, 6, 12), width=4, height=4)
        body = pd.bore(body, (0, 12, 6), d=3, depth=3, through=False)
        rib = pd.rib_end(Pos(0, -12.6, 6) * Box(2, 1.2, 10), (0, -12.6, 3), (0, 0, -1))
        tags = list(self.module.PRINT_DETAIL_TAGS)
        self.assertEqual([tag["kind"] for tag in tags], ["rivet", "band", "panel", "bore", "rib-end"])
        self.assertEqual([tag["name"] for tag in tags], ["rivet-1", "band-1", "panel-1", "bore-1", "rib-end-1"])
        for tag in tags:
            with self.subTest(tag=tag["name"]):
                self.assertTrue(tag["site"].startswith("test_print_details.py:"), tag["site"])
                self.assertGreater(len(tag["shape"].faces()), 0)
        self.assertTrue(body.is_valid)
        self.assertTrue(rib.is_valid)
        # A refused feature leaves no tag.
        with self.assertRaises(self.module.PrintLimitError):
            pd.rivet(self.block, (0, 0, 12), d=1.0)
        self.assertEqual(len(self.module.PRINT_DETAIL_TAGS), len(tags))

    def test_a_blunt_tip_leaves_a_land_one_minimum_wall_across(self):
        import math
        from build123d import Plane, Polygon, extrude
        pd = self.module.Details(nozzle=0.4)
        chisel = extrude(Plane.XZ * Polygon((0, 0), (30, 0), (30, 3), align=None), 10, both=True)
        blunt = pd.blunt_tip(chisel, (0, 0, 0), (-1, 0, 0), reach=12)
        self.assertTrue(blunt.is_valid)
        box = blunt.bounding_box()
        # The 1:10 chisel is 0.8 mm high 8 mm back from its edge.
        self.assertAlmostEqual(box.min.X, 8.0, delta=0.05)
        self.assertEqual((box.min.Y, box.max.Y), (-10.0, 10.0))
        land = pd._section_width(blunt, self.module._vec((box.min.X + 1e-3, 0, 0)), self.module._vec((-1, 0, 0)), 12)
        self.assertGreaterEqual(land, 0.8 - 0.01)
        vault = 4 + 5 * math.tan(math.radians(50))
        roof = extrude(Plane.XZ * Polygon((-5, 0), (5, 0), (5, 4), (0, vault), (-5, 4), align=None), 10, both=True)
        ridge = pd.blunt_tip(roof, (0, 0, vault), (0, 0, 1), reach=12).bounding_box()
        self.assertLess(ridge.max.Z, vault - 0.3)

    def test_rib_end_and_a_hanging_land_are_refused_below_the_limits(self):
        from build123d import Box, Cone, Pos
        pd = self.module.Details(nozzle=0.4)
        with self.assertRaises(self.module.PrintLimitError) as raised:
            pd.rib_end(Box(10, 0.6, 2), (3, 0, 0), (1, 0, 0))
        self.assertIn("min wall", str(raised.exception))
        with self.assertRaises(self.module.PrintLimitError) as raised:
            pd.blunt_tip(self.block + Pos(0, 0, 30) * Cone(0, 3, 8), (0, 0, 26), (0, 0, -1))
        self.assertIn("face down", str(raised.exception))
        # A rib end that would look straight down is ramped back instead: its
        # end face rises at 52 deg across the rib's 2 mm, through `end`.
        import math
        ramped = pd.rib_end(Pos(0, 0, 5) * Box(2, 1.2, 10), (0, 0, 3), (0, 0, -1))
        self.assertTrue(ramped.is_valid)
        box = ramped.bounding_box()
        self.assertAlmostEqual(box.min.Z, 3 - math.tan(math.radians(52)), delta=0.02)
        self.assertEqual(round(box.max.Z, 6), 10.0)

    def _build(self, steps):
        """Run `steps(pd)` as a build: refusals are collected, then returned."""
        previous = os.environ.get(self.module.BUILD_ENV)
        os.environ[self.module.BUILD_ENV] = "1"
        self.module.DETAIL_REFUSALS.clear()
        try:
            body = steps(self.module.Details(nozzle=0.4))
            return body, self.module.refusal_error()
        finally:
            if previous is None:
                os.environ.pop(self.module.BUILD_ENV, None)
            else:
                os.environ[self.module.BUILD_ENV] = previous

    def test_a_build_reports_every_detail_refusal_at_once_with_a_passing_value(self):
        # Issue #86: three bad details fail the build once, all three named.
        def steps(pd):
            body = pd.rivet(self.block, (0, 0, 12), d=1.5)
            body = pd.band(body, pd.segment((-5, 6, 12), (5, 6, 12)), width=0.6)
            body = pd.boss(body, (6, -6, 12))
            return pd.rivets(body, pd.along((-2, -6, 12), (2, -6, 12), 3), d=2.0, h=0.6)
        body, error = self._build(steps)
        self.assertIsInstance(error, self.module.DetailRefusals)
        self.assertIsInstance(error, self.module.PrintLimitError)
        refusals = error.refusals
        self.assertEqual([item["feature"] for item in refusals], ["rivet", "band", "rivet"])
        for item in refusals:
            with self.subTest(refusal=item["site"]):
                self.assertTrue(item["site"].startswith("test_print_details.py:"), item["site"])
                self.assertTrue(item["passes"])
        self.assertEqual(refusals[0]["passes"], "d >= 2.00 mm")
        self.assertIn("min feature", refusals[0]["reason"])
        self.assertEqual(refusals[1]["passes"], "width >= 0.90 mm")
        self.assertEqual(refusals[2]["passes"], "copies at least 2.50 mm apart, centre to centre (now 2.00 mm)")
        self.assertIn("gap between copies", refusals[2]["reason"])
        # Each refusal is one parseable line of the error, for make_round.
        lines = [line for line in str(error).splitlines() if line.startswith(self.module.REFUSAL_LINE)]
        self.assertEqual(len(lines), 3)
        self.assertEqual(self.module.DETAIL_REFUSALS, [])
        # The good boss between them was still made; nothing else was.
        boss = self.module.Details().boss(self.block, (6, -6, 12))
        self.assertAlmostEqual(body.volume, boss.volume, places=3)

    def test_a_passing_value_passes_at_that_spot(self):
        from build123d import Cylinder, Pos
        drum = Pos(0, 0, 8) * Cylinder(3, 16)
        _, error = self._build(lambda pd: pd.rivet(drum, (0, -3, 8), d=4.0, h=0.6))
        (refusal,) = error.refusals
        self.assertIn("the host falls", refusal["reason"])
        taller, smaller = re.fullmatch(r"h >= ([0-9.]+) mm or d <= ([0-9.]+) mm at this spot",
                                       refusal["passes"]).groups()
        pd = self.module.Details(nozzle=0.4)
        self.assertTrue(pd.rivet(drum, (0, -3, 8), d=4.0, h=float(taller)).is_valid)
        self.assertTrue(pd.rivet(drum, (0, -3, 8), d=float(smaller), h=0.6).is_valid)
        helm = Pos(0, 0, 8) * Cylinder(4, 16)
        path = ((0, -4, 2), (0, -4, 10))
        _, error = self._build(lambda pd: pd.band(helm, pd.segment(*path), width=6.5, height=0.8))
        taller, smaller = re.fullmatch(r"height >= ([0-9.]+) mm or width <= ([0-9.]+) mm at this spot",
                                       error.refusals[0]["passes"]).groups()
        self.assertTrue(pd.band(helm, pd.segment(*path), width=6.5, height=float(taller)).is_valid)
        self.assertTrue(pd.band(helm, pd.segment(*path), width=float(smaller), height=0.8).is_valid)

    def test_outside_a_build_a_refusal_raises_at_once_with_its_passing_value(self):
        self.assertNotEqual(os.environ.get(self.module.BUILD_ENV), "1")
        pd = self.module.Details(nozzle=0.4)
        with self.assertRaises(self.module.PrintLimitError) as raised:
            pd.rivet(self.block, (0, 0, 12), d=1.5)
        self.assertNotIsInstance(raised.exception, self.module.DetailRefusals)
        self.assertEqual(raised.exception.passing, "d >= 2.00 mm")
        self.assertEqual(self.module.DETAIL_REFUSALS, [])

    def test_a_build_boundary_raises_the_refusals_with_the_error_that_stopped_it(self):
        # A rivet standing on a refused band is no longer on the host: the
        # build reports the band's refusal and then that error.
        printlib = _load_printlib()

        def steps(pd):
            body = pd.band(self.block, pd.segment((-5, 0, 12), (5, 0, 12)), width=0.6)
            return pd.rivet(body, (0, 0, 13.0), d=2.0)
        with self.assertRaises(self.module.DetailRefusals) as raised:
            with printlib.detail_build():
                steps(self.module.Details(nozzle=0.4))
        self.assertEqual([item["feature"] for item in raised.exception.refusals], ["band"])
        self.assertIsInstance(raised.exception.after, ValueError)
        self.assertIn("then the build stopped: ValueError", str(raised.exception))
        self.assertNotEqual(os.environ.get(self.module.BUILD_ENV), "1")
        with printlib.detail_build():
            self.module.Details().boss(self.block, (0, 0, 12))

    def test_gen_fails_once_with_every_refusal_of_the_part(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            self.module.install(project)
            (project / "part_helm.step.py").write_text(
                "from build123d import *\n"
                "from features import print_details\n\n"
                "pd = print_details.Details(nozzle=0.4)\n\n\n"
                "def gen_step():\n"
                "    body = Pos(0, 0, 6) * Box(24, 24, 12)\n"
                "    body = pd.rivet(body, (0, 0, 12), d=1.5)\n"
                "    body = pd.band(body, pd.segment((-5, 6, 12), (5, 6, 12)), width=0.6)\n"
                "    return pd.slit(body, (6, -6, 12), width=0.3)\n", encoding="utf-8")
            done = subprocess.run([sys.executable, str(CAD / "gen"), "part_helm.step.py", "--write", "--json"],
                                  cwd=project, capture_output=True, text=True, timeout=600)
            self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
            self.assertFalse((project / "part_helm.step").exists())
            lines = [line for line in done.stderr.splitlines() if line.startswith("detail-refusal ")]
            self.assertEqual([json.loads(line[len("detail-refusal "):])["site"] for line in lines],
                             ["part_helm.step.py:9", "part_helm.step.py:10", "part_helm.step.py:11"])
            self.assertIn("3 Detail Refusals in this build", done.stderr)

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
                       "45 degrees", "print-details", "ends in a flat land at least one print minimum", "never the geometry's wall_min_mm",
                       "Never ask for a sharp tip, a knife edge",
                       "a chamfer or taper that leaves an edge thinner than that"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, reviewer)

    def test_design_a_toy_takes_its_minimums_from_the_library(self):
        # Issue #87: one source for the print minimums, at design time too.
        design = (REPOSITORY / ".claude/skills/design-a-toy/SKILL.md").read_text(encoding="utf-8")
        stage = design[design.index("## Stage 3c"):design.index("## Stage 3d")]
        rows = re.findall(r"^\|[^|\n]+\| [^|\n]*?([0-9.]+) mm[^|\n]*\| `(\w+)` \|$", stage, re.MULTILINE)
        fine = self.module.limits(0.4)
        self.assertEqual({name for _value, name in rows},
                         {"min_wall", "min_feature", "min_relief_width", "min_relief_height",
                          "min_cut_width", "min_cut_depth", "min_web"})
        for value, name in rows:
            with self.subTest(limit=name):
                self.assertAlmostEqual(float(value), fine[name][0])
        flat = " ".join(design.split())
        for phrase in ("print_details.py --limits --nozzle N",
                       "A drawn detail under the print minimums is enlarged to the minimum; when the "
                       "enlarged detail does not fit its spot, it is left out, and this contract names it.",
                       "The host is at least the detail's size plus 0.5 mm on each side",
                       "keeps at least 0.5 mm above it",
                       "Copies in a row keep a 0.5 mm gap",
                       "a bigger toy, then a bigger host, then the detail left out",
                       "Worked example: Broken God's crest helm",
                       "The brow band is a plain raised band and carries no rivets"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, flat)
        self.assertNotIn("rivet, boss, ridge or groove | 1.0 mm", stage)
        contract_format = " ".join((REPOSITORY / ".claude/skills/build-a-toy/CONTRACT-FORMAT.md"
                                    ).read_text(encoding="utf-8").split())
        self.assertIn("## Print minimums in the prose", contract_format)
        self.assertIn("a rivet, boss or dome is at least 2.0 mm across", contract_format)
        self.assertIn("it is left out, and this contract names it.", contract_format)

    def test_workers_and_the_make_reference_name_the_library(self):
        worker = " ".join(
            (REPOSITORY / "src/workshop/make/agents/component-worker.toml").read_text(encoding="utf-8").split())
        make = " ".join((REPOSITORY / ".agents/product-run/.agents/skills/autonomous-workshop/references/make.md"
                         ).read_text(encoding="utf-8").split())
        self.assertIn("from features import print_details", worker)
        self.assertIn("pd.blunt_tip(body, tip, toward)", worker)
        self.assertIn("An `again` line means the same feature failed", worker)
        self.assertIn(".agents/skills/print-details/scripts/print_details.py --install", make)


if __name__ == "__main__":
    unittest.main()
