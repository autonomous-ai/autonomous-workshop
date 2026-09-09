"""Bind the Workshop-owned CAD tool contract to the vendored CAD skill.

`references/cad-tool-contracts-v1.md` exists so a Make Goal never has to read
2,288 lines of `verify_project` to learn a mode, a report path, or an ordering
rule.  That only helps while the reference is true.  A vendored-skill resync
that renames a flag or moves a report must fail here rather than silently leave
a confident, wrong contract in front of every product run.
"""

import re
import subprocess
import sys
import unittest
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[2]
SCRIPTS = REPOSITORY / "src" / "workshop" / "make" / "skills" / "cad" / "scripts"
REFERENCE = (
    REPOSITORY
    / ".agents"
    / "product-run"
    / ".agents"
    / "skills"
    / "autonomous-workshop"
    / "references"
    / "cad-tool-contracts-v1.md"
)


def _help(tool, *arguments):
    completed = subprocess.run(
        [sys.executable, str(SCRIPTS / tool), *arguments, "--help"],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if completed.returncode != 0:
        raise AssertionError(
            "%s --help failed: %s" % (tool, completed.stderr[-2000:])
        )
    return completed.stdout


class CadToolContractReferenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = REFERENCE.read_text(encoding="utf-8")
        cls.verify_help = _help("verify_project")
        cls.verify_source = (SCRIPTS / "verify_project").read_text(
            encoding="utf-8"
        )

    def test_every_verify_project_flag_named_in_the_reference_exists(self):
        # The reference names flags in backticks, sometimes with a value or a
        # choice list after them.  Take the leading option token only.
        named = {
            match.group(1)
            for match in re.finditer(r"`(--[a-z][a-z-]*)", self.reference)
        }
        # Flags documented for the other tools are checked separately below.
        other_tools = {
            "--write",
            "--force",
            "--stl",
            "--3mf",
            "--glb",
            "--json",
            "--view",
            "--size",
            "--base",
            "--accent",
            "--background",
            "--pose-degrees",
            "--motion-sheet",
            "--motion-view",
            "--motion-angles",
            "--state-sheet",
            "--state-stl",
            "--state-view",
            "--min-state-difference",
            "--list-parts",
            "--mesh-tolerance",
            "--mesh-angular-tolerance",
            "--lock-timeout",
        }
        self.assertTrue(named, "the reference names no flags at all")
        for flag in sorted(named - other_tools):
            with self.subTest(flag=flag):
                self.assertIn(flag, self.verify_help)

    def test_documented_modes_and_exclusions_still_hold(self):
        for flag in ("--quick", "--print-preflight", "--exports", "--dry-run"):
            with self.subTest(flag=flag):
                self.assertIn(flag, self.verify_help)
        # Final-mode-only flags the reference says cannot join --quick.
        for flag in (
            "--exports",
            "--strict-fit",
            "--strict-mount",
            "--skip-thickness",
            "--powered",
            "--unpowered",
            "--image-derived",
        ):
            with self.subTest(exclusive=flag):
                self.assertRegex(
                    self.verify_source,
                    r"args\.quick and .*%s" % flag.lstrip("-").replace("-", "_"),
                )
        self.assertIn(
            "--print-preflight and --quick are mutually exclusive",
            self.verify_source,
        )
        self.assertIn(
            "--powered and --unpowered are mutually exclusive",
            self.verify_source,
        )
        self.assertIn(
            "--unpowered is only needed with --image-derived",
            self.verify_source,
        )

    def test_documented_report_and_declaration_paths_still_hold(self):
        for path in (
            "measure/print-preflight.md",
            "measure/verification-pipeline.md",
            "measure/motion.json",
            "measure/power.json",
            "measure/mounts.json",
            "snap/SIGNATURE-REVIEW.json",
        ):
            with self.subTest(path=path):
                self.assertIn(path, self.reference)
        self.assertIn('"print-preflight.md"', self.verify_source)
        self.assertIn('"verification-pipeline.md"', self.verify_source)
        self.assertIn('Path("snap/SIGNATURE-REVIEW.json")', self.verify_source)

    def test_final_mode_still_refuses_before_geometry(self):
        self.assertIn(
            "final verification requires a passing measure/print-preflight.md",
            self.verify_source,
        )
        self.assertIn(
            "final verification requires snap/SIGNATURE-REVIEW.json",
            self.verify_source,
        )
        self.assertIn(
            "signature review is not bound to the passing print preflight",
            self.verify_source,
        )
        self.assertIn("schema_version\") != 6", self.verify_source)

    def test_help_alone_would_not_teach_the_modes(self):
        # The reason this reference exists: the parser description is only the
        # first docstring line, so the mode composition below it never reaches
        # --help.  If upstream ever shows the full docstring, this reference
        # can shrink, and this test says so.
        self.assertIn("description=__doc__.splitlines()[0]", self.verify_source)
        self.assertNotIn("Print-preflight mode is the one cheap gate", self.verify_help)

    def test_gen_still_owns_step_writing_and_export_owns_meshes(self):
        # argparse wraps help text, so compare on collapsed whitespace.
        gen_help = " ".join(_help("gen").split())
        export_help = " ".join(_help("export").split())
        self.assertIn("--write", gen_help)
        self.assertIn("only way to write a .step file", gen_help)
        self.assertIn("--lock-timeout", gen_help)
        self.assertIn("Writes no .step file", export_help)
        self.assertNotIn("[--write", export_help)
        for flag in ("--stl", "--3mf", "--glb"):
            with self.subTest(flag=flag):
                self.assertIn(flag, export_help)

    def test_render_product_defaults_named_in_the_reference_still_hold(self):
        source = (SCRIPTS / "render_product").read_text(encoding="utf-8")
        self.assertIn('"--motion-angles"', source)
        self.assertIn("default=(-12.0, 0.0, 12.0)", source)
        self.assertIn('"--min-state-difference", type=float, default=2.0', source)
        for flag, default in (("--motion-view", "front"), ("--state-view", "front")):
            with self.subTest(flag=flag):
                self.assertRegex(
                    source,
                    r'"%s",\s*choices=\("iso", "front", "right", "top"\),\s*'
                    r'default="%s",' % (flag, default),
                )
        self.assertIn('"--view", choices=("iso", "front", "right", "top"), default="iso"', source)
        self.assertIn('"--size", type=int, default=900', source)


if __name__ == "__main__":
    unittest.main()
