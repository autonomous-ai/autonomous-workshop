"""Narrow assembly failures must be available before the visual review."""
import hashlib
from pathlib import Path
import runpy
import tempfile
import unittest


VERIFIER = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts/verify_project"


class AssemblyPreflightTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.verifier = runpy.run_path(str(VERIFIER))

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = Path(temporary.name).resolve()
        self.assembly = self.project / "selected.step.py"
        self.parts = [self.project / "part_body.step.py", self.project / "part_rotor.step.py"]

    def runner(self, batch_result=0, generation_result=0):
        project = self.project

        class Runner:
            cwd = project

            def __init__(self):
                self.events = []

            def command(self, argv, **kwargs):
                args = [str(arg) for arg in argv]
                self.events.append(("command", args))
                return generation_result if Path(args[1]).name == "gen" else 0

            def inspect_batch(self, requests):
                self.events.append(("inspect", requests))
                if isinstance(batch_result, Exception):
                    raise batch_result
                return batch_result

            def note(self, label, detail):
                self.events.append(("note", label, detail))

        return Runner()

    def run_preflight(self, runner, printables=None):
        return self.verifier["_print_preflight"](
            runner, self.project, self.parts if printables is None else printables,
            assembly=self.assembly, bed=(220, 220, 220),
        )

    def test_generates_selected_assembly_and_checks_it_before_printable_work(self):
        runner = self.runner()
        self.assertEqual(self.run_preflight(runner), 0)
        self.assertEqual(runner.events[0][1][2:5], ["selected.step.py", "part_body.step.py", "part_rotor.step.py"])
        self.assertEqual(runner.events[1], ("inspect", [
            {"id": "validate:assembly", "argv": ["validate", "selected.step.py"]},
            {"id": "interfere:assembly", "argv": ["interfere", "selected.step.py", "--tolerance", "1.0"]},
        ]))
        self.assertEqual(runner.events[2][0:2], ("note", "assembly preflight"))
        fit = next(args for kind, *rest in runner.events if kind == "command" for args in rest if Path(args[1]).name == "check_fit")
        self.assertNotIn("selected.step.py", fit)
        self.assertIn("part_body.step.py", fit)
        self.assertIn("part_rotor.step.py", fit)

    def test_printable_combined_entry_is_generated_only_once(self):
        runner = self.runner()
        self.assertEqual(self.run_preflight(runner, [self.assembly]), 0)
        self.assertEqual(runner.events[0][1].count("selected.step.py"), 1)
        self.assertTrue(any(event[0] == "command" and Path(event[1][1]).name == "check_mesh" and event[1][2] == "selected.stl" for event in runner.events))

    def test_inspection_failure_or_error_stops_without_passing_evidence(self):
        for code in (1, 2):
            with self.subTest(code=code):
                runner = self.runner(batch_result=code)
                self.assertEqual(self.run_preflight(runner), 1)
                self.assertEqual([event[0] for event in runner.events], ["command", "inspect"])

    def test_generation_failure_prevents_inspection_and_success_record(self):
        runner = self.runner(generation_result=2)
        self.assertEqual(self.run_preflight(runner), 1)
        self.assertEqual(len(runner.events), 1)

    def test_unexpected_inspection_error_does_not_create_success_record(self):
        runner = self.runner(batch_result=RuntimeError("inspection failed"))
        with self.assertRaisesRegex(RuntimeError, "inspection failed"):
            self.run_preflight(runner)
        self.assertFalse(any(event[0] == "note" for event in runner.events))

    def report(self, assembly_row):
        text = "# Verification pipeline record\n\n- Mode: `print-preflight`\n- Result: **PASS** (exit 0)\n"
        text += assembly_row + "\n"
        for part in ("body", "rotor"):
            for command in (f"check_mesh part_{part}.stl", f"check_overhang part_{part}.stl --angle 45.0", f"check_thickness part_{part}.stl --nozzle 0.4"):
                text += f"| 1 | `{command}` | rc=0 | 0.01 |\n"
        path = self.project / "measure/print-preflight.md"
        path.parent.mkdir(exist_ok=True)
        path.write_text(text)
        return path.read_bytes()

    def test_review_requires_evidence_for_selected_assembly_and_fixed_checks(self):
        detail = '{"assembly":"selected.step.py","checks":["validate","interfere"],"interference_tolerance_mm3":1.0}'
        row = f"| 0 | `assembly preflight  # NOTE: {detail}` | note | 0.00 |"
        raw = self.report(row)
        require = self.verifier["_required_print_preflight"]
        self.assertEqual(require(self.project, self.parts, self.assembly), hashlib.sha256(raw).hexdigest())
        for bad in ("", row.replace("selected.step.py", "wrong.step.py"), row.replace('"validate",', ""), row.replace(',"interfere"', ""), row.replace('mm3":1.0', 'mm3":100.0'), row.replace("| note |", "| rc=1 |")):
            with self.subTest(record=bad):
                self.report(bad)
                with self.assertRaisesRegex(ValueError, "assembly validity"):
                    require(self.project, self.parts, self.assembly)


if __name__ == "__main__":
    unittest.main()
