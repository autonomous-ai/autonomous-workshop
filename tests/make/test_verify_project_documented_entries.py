"""A documented CAD entry that does not exist cannot pass final verification.

A preserved product passed its host Make gate while its README file map and
rebuild command named a `part_token.step.py` entry absent from the delivered
project; the documented `gen` command failed with FileNotFoundError. The
verifier must reject that stale documentation before geometry work, without
rejecting wildcard or placeholder prose in accepted projects.
"""
from __future__ import annotations

import contextlib
import io
import os
from pathlib import Path
import runpy
import tempfile
import unittest


VERIFIER = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts/verify_project"
ENTRY = "PRINTABLE = True\n\n\ndef gen_step():\n    return None\n"


class DocumentedEntryReferenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.verifier = runpy.run_path(str(VERIFIER))

    def missing(self, project):
        return self.verifier["_documented_entry_references"](project)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.project = self.root / "proj"
        (self.project / "measure").mkdir(parents=True)
        (self.project / "widget.step.py").write_text(ENTRY, encoding="utf-8")
        (self.project / "part_body.step.py").write_text(ENTRY, encoding="utf-8")

    def write(self, name: str, text: str) -> None:
        (self.project / name).write_text(text, encoding="utf-8")

    def test_existing_entries_and_prose_patterns_are_not_missing(self):
        self.write("README.md", "\n".join([
            "# Widget",
            "- `widget.step.py` is the combined entry; `part_body.step.py` prints.",
            "- Generate every `part_*.step.py`; entries are named `<name>.step.py`.",
            "- From the parent: `proj/widget.step.py` and `./part_body.step.py`.",
            "- Keep `widget.step.py.bak` and `oldwidget.step.pyc` out of the tree.",
            "Run gen widget.step.py.",
            "",
        ]))
        self.write("widget_spec.md", "# spec\n\nThe printable target is `part_body.step.py`.\n")
        self.assertEqual(self.missing(self.project), [])

    def test_missing_entry_in_file_map_is_reported_with_its_line(self):
        self.write("README.md", "# Widget\n\n## Files\n\n- `widget.step.py` entry.\n- `part_token.step.py` review entry.\n")
        self.assertEqual(self.missing(self.project), ["README.md:6: part_token.step.py"])

    def test_missing_entry_in_a_path_prefixed_rebuild_command_is_reported(self):
        self.write("README.md", "\n".join([
            "# Widget",
            "```bash",
            'PYTHONPATH=.agents/skills/cad/scripts "$WORKSHOP_PYTHON" -m gen '
            "artifacts/make/r0001/product/cad/proj/widget.step.py "
            "artifacts/make/r0001/product/cad/proj/part_token.step.py --write",
            "```",
            "",
        ]))
        self.assertEqual(
            self.missing(self.project),
            ["README.md:3: artifacts/make/r0001/product/cad/proj/part_token.step.py"],
        )

    def test_missing_entry_in_spec_is_reported(self):
        self.write("widget_spec.md", "# spec\n\n`part_token.step.py` is a non-printable review entry.\n")
        self.assertEqual(self.missing(self.project), ["widget_spec.md:3: part_token.step.py"])

    def test_absent_documents_report_nothing(self):
        self.assertEqual(self.missing(self.project), [])

    def run_main(self, argv):
        err, out = io.StringIO(), io.StringIO()
        cwd = Path.cwd()
        os.chdir(self.root)
        try:
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
                try:
                    code = self.verifier["main"](argv)
                except SystemExit as exc:
                    code = exc.code
        finally:
            os.chdir(cwd)
        return code, err.getvalue(), out.getvalue()

    def test_final_refuses_before_any_geometry_work(self):
        self.write("README.md", "# Widget\n\n- `part_token.step.py` review entry.\n")
        code, err, out = self.run_main(["proj"])
        self.assertNotIn(code, (0, None))
        self.assertIn("does not exist in the project: README.md:3: part_token.step.py", err)
        self.assertNotIn("check_layout", out)

    def test_quick_mode_does_not_gate_documentation(self):
        self.write("README.md", "# Widget\n\n- `part_token.step.py` review entry.\n")
        code, err, _out = self.run_main(["proj", "--quick", "--dry-run"])
        self.assertNotIn("does not exist in the project", err)

    def test_final_refusal_is_recorded_in_the_pipeline_report(self):
        self.write("README.md", "# Widget\n\n- `part_token.step.py` review entry.\n")
        self.run_main(["proj"])
        report = self.project / "measure" / "verification-pipeline.md"
        self.assertTrue(report.is_file())
        text = report.read_text(encoding="utf-8")
        self.assertIn("| refused |", text)
        self.assertIn("part_token.step.py", text)


if __name__ == "__main__":
    unittest.main()
