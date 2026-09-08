"""Pre-review print screening must expose the final gate's support failures."""
import hashlib
from pathlib import Path
import runpy
import tempfile
import unittest


VERIFIER = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts/verify_project"


class PrintPreflightOverhangTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.verifier = runpy.run_path(str(VERIFIER))

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name).resolve()
        self.assembly = self.project / "assembly.step.py"
        self.parts = [self.project / f"part_{name}.step.py" for name in ("body", "rotor")]

    def _run(self, failure_part=None, failure_code=1):
        project = self.project

        class Runner:
            cwd = project

            def __init__(self):
                self.commands = []

            def inspect_batch(self, requests):
                return 0

            def note(self, label, detail):
                pass

            def command(self, argv, **kwargs):
                args = [str(value) for value in argv]
                self.commands.append(args)
                if Path(args[1]).name == "check_overhang" and args[2] == failure_part:
                    return failure_code
                return 0

        runner = Runner()
        result = self.verifier["_print_preflight"](runner, self.project, self.parts, assembly=self.assembly, bed=(220, 220, 220))
        return result, runner.commands

    def test_screens_every_part_before_its_thickness_check(self):
        result, commands = self._run()
        self.assertEqual(result, 0)
        for part in ("body", "rotor"):
            stl = f"part_{part}.stl"
            checks = [args for args in commands if len(args) > 2 and args[2] == stl]
            self.assertEqual([Path(args[1]).name for args in checks], ["check_mesh", "check_overhang", "check_thickness"])
            self.assertIn("45.0", checks[1])
            self.assertIn(f"measure/overhang-{part}.md", checks[1])

    def test_support_failure_or_checker_error_stops_preflight(self):
        for part in ("body", "rotor"):
            for code in (1, 2):
                with self.subTest(part=part, code=code):
                    result, commands = self._run(f"part_{part}.stl", code)
                    self.assertEqual(result, 1)
                    self.assertEqual(Path(commands[-1][1]).name, "check_overhang")
                    self.assertEqual(commands[-1][2], f"part_{part}.stl")

    def _report(self, overhang_rows):
        text = "# Verification pipeline record\n\n- Mode: `print-preflight`\n- Result: **PASS** (exit 0)\n"
        detail = self.verifier["_assembly_preflight_detail"](self.assembly)
        text += f"| 0 | `assembly preflight  # NOTE: {detail}` | note | 0.00 |\n"
        for part in ("body", "rotor"):
            text += f"| 1 | check_mesh part_{part}.stl | rc=0 | 0.01 |\n"
            text += f"| 2 | check_thickness part_{part}.stl --nozzle 0.4 | rc=0 | 0.01 |\n"
        text += "\n".join(overhang_rows) + "\n"
        path = self.project / "measure/print-preflight.md"
        path.parent.mkdir(exist_ok=True)
        path.write_text(text)
        return path.read_bytes()

    def test_review_binding_requires_standard_support_success_for_every_part(self):
        good = [f"| 3 | check_overhang part_{part}.stl --angle 45.0 | rc=0 | 0.01 |" for part in ("body", "rotor")]
        raw = self._report(good)
        self.assertEqual(self.verifier["_required_print_preflight"](self.project, self.parts, self.assembly), hashlib.sha256(raw).hexdigest())
        for rows in ([], good[:1], [good[0], good[1].replace("rc=0", "rc=1")], [good[0], good[1].replace("45.0", "10.0")], [good[0], good[1].replace("45.0", "45.0e-3")]):
            with self.subTest(rows=rows):
                self._report(rows)
                with self.assertRaisesRegex(ValueError, "overhang"):
                    self.verifier["_required_print_preflight"](self.project, self.parts, self.assembly)


if __name__ == "__main__":
    unittest.main()
