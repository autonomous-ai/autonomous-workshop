"""Source-local imports must work throughout a CAD generator invocation."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts"
CADGEN_SRC = SCRIPTS / "packages/cadgen/src"

# A separate process keeps the real first-party eviction from unloading tests.
RUN_GENERATORS = """
import json
from pathlib import Path
import sys
from cadgen._internal.generation_runner import _run_script_generator_inner
from cadgen._internal.generation_spec import EntrySpec
from cadgen.cli_logging import CliLogger
from cadgen.metadata import parse_generator_metadata
from cadgen.sources import load_source_module

original_path = list(sys.path)
path_object = sys.path
results = []
for item in json.loads(sys.argv[1]):
    path = Path(item['path'])
    try:
        if item.get('mode') == 'load':
            load_source_module(path)
            result = {'loaded': True}
        else:
            spec = EntrySpec(
                source_ref=str(path), cad_ref=str(path.with_suffix('')),
                kind='part', source_path=path, display_name=path.stem,
                source='python', script_path=path, step_path=path.with_suffix(''),
                generator_metadata=parse_generator_metadata(path),
            )
            scene = _run_script_generator_inner(spec, 'gen_step', logger=CliLogger('test'))
            result = {
                'volume': scene.source_compound.volume,
                'closure': scene.source_closure_files,
                'closure_hash': scene.source_closure_hash,
            }
    except Exception as error:
        result = {'error': type(error).__name__, 'missing': getattr(error, 'name', None)}
    result['path_restored'] = sys.path == original_path and sys.path is path_object
    results.append(result)
print(json.dumps(results))
"""


class GenDeferredImportsTest(unittest.TestCase):
    def environment(self):
        return {
            **os.environ, "CADGEN_WARM": "0", "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": str(CADGEN_SRC),
        }

    def write_project(self, parent, name, width=2):
        project = parent / name
        for package in ("parts", "features"):
            (project / package).mkdir(parents=True)
            (project / package / "__init__.py").write_text("")
        (project / "features/primitives.py").write_text(
            f"from build123d import Box\ndef make_box():\n    return Box({width}, 3, 4)\n"
        )
        (project / "parts/late.py").write_text("from features.primitives import make_box\n")
        (project / "parts/wrapper.py").write_text(
            "def make_deferred():\n"
            "    from parts.late import make_box\n"
            "    return make_box()\n"
        )
        (project / "eager.step.py").write_text(
            "from features.primitives import make_box\n"
            "def gen_step():\n    return make_box()\n"
        )
        (project / "deferred.step.py").write_text(
            "from parts.wrapper import make_deferred\n"
            "def gen_step():\n    return make_deferred()\n"
        )
        return project

    def run_generators(self, cwd, items):
        result = subprocess.run(
            [sys.executable, "-c", RUN_GENERATORS, json.dumps(items)],
            cwd=cwd, env=self.environment(), capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        reports = json.loads(result.stdout)
        self.assertTrue(all(report["path_restored"] for report in reports), reports)
        return reports

    def test_bulk_cli_builds_deferred_imports_from_outside_project(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            project = self.write_project(root, "project")
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "gen"),
                 str(project / "eager.step.py"), str(project / "deferred.step.py"),
                 "--write", "--force", "--json"],
                cwd=root, env=self.environment(), capture_output=True, text=True, timeout=60,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            reports = [json.loads(line) for line in result.stdout.splitlines()]
            self.assertEqual(len(reports), 2)
            self.assertTrue(all(report["ok"] for report in reports), reports)
            for name in ("eager", "deferred"):
                self.assertTrue((project / f"{name}.step").is_file())

    def test_deferred_dependencies_are_captured_and_projects_do_not_share_modules(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            first = self.write_project(root, "first", width=2)
            second = self.write_project(root, "second", width=5)
            reports = self.run_generators(root, [
                {"path": str(first / "eager.step.py")},
                {"path": str(first / "deferred.step.py")},
                {"path": str(second / "deferred.step.py")},
            ])
            for report, volume in zip(reports, (24, 24, 60)):
                self.assertNotIn("error", report)
                self.assertAlmostEqual(report["volume"], volume)
            for report in reports[1:]:
                self.assertTrue({
                    "deferred.step.py", "parts/wrapper.py", "parts/late.py",
                    "features/primitives.py",
                }.issubset(report["closure"]), report)
            self.assertNotEqual(reports[1]["closure_hash"], reports[2]["closure_hash"])

    def test_paths_restore_after_load_and_runtime_failures_without_parent_fallback(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            cwd = root / "outside"
            cwd.mkdir()
            project = self.write_project(root, "project")
            (root / "forbidden_parent.py").write_text("VALUE = 7\n")
            (project / "missing.step.py").write_text(
                "from build123d import Box\ndef gen_step():\n"
                "    import forbidden_parent\n    return Box(1, 1, 1)\n"
            )
            (project / "runtime_error.step.py").write_text(
                "from build123d import Box\nimport sys\ndef gen_step():\n"
                "    sys.path.append('generator-path-must-not-leak')\n"
                "    raise RuntimeError('intentional fixture failure')\n"
                "    return Box(1, 1, 1)\n"
            )
            (project / "load_error.step.py").write_text(
                "import sys\nsys.path.append('module-path-must-not-leak')\n"
                "raise RuntimeError('intentional fixture failure')\n"
                "def gen_step():\n    return None\n"
            )
            reports = self.run_generators(cwd, [
                {"path": str(project / "eager.step.py"), "mode": "load"},
                {"path": str(project / "load_error.step.py"), "mode": "load"},
                {"path": str(project / "runtime_error.step.py")},
                {"path": str(project / "missing.step.py")},
                {"path": str(project / "deferred.step.py")},
            ])
            self.assertTrue(reports[0]["loaded"])
            self.assertEqual(reports[1]["error"], "RuntimeError")
            self.assertEqual(reports[2]["error"], "RuntimeError")
            self.assertEqual(reports[3]["error"], "ModuleNotFoundError")
            self.assertEqual(reports[3]["missing"], "forbidden_parent")
            self.assertAlmostEqual(reports[4]["volume"], 24)

    def test_existing_ancestor_package_paths_support_deferred_imports(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            project = root / "library/models/item"
            project.mkdir(parents=True)
            common = root / "library/robot_common"
            common.mkdir()
            (common / "__init__.py").write_text("")
            (common / "shapes.py").write_text(
                "from build123d import Box\ndef shape():\n    return Box(2, 3, 4)\n"
            )
            entry = project / "model.step.py"
            entry.write_text(textwrap.dedent("""\
                def gen_step():
                    from robot_common.shapes import shape
                    return shape()
            """))
            report, = self.run_generators(root, [{"path": str(entry)}])
            self.assertAlmostEqual(report["volume"], 24)
            self.assertIn("../../robot_common/shapes.py", report["closure"])


if __name__ == "__main__":
    unittest.main()
