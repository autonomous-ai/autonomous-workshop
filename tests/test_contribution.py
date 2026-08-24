import json
import os
import tempfile
import unittest
from pathlib import Path

from inventor_workshop.errors import ManifestError
from inventor_workshop.contribution import (
    manifests_for_target,
    run_declared_checks,
    validate_contribution,
)
from inventor_workshop.manifest import load_manifest


def _inventor(root: Path, *, check=None) -> Path:
    folder = root / "sample"
    (folder / "tests").mkdir(parents=True)
    (folder / "README.md").write_text("# Sample\n", encoding="utf-8")
    (folder / "TASTE.md").write_text("# Taste\nSpecific and useful.\n", encoding="utf-8")
    (folder / "run.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
    (folder / "tests/test_smoke.py").write_text(
        "import unittest\n\n"
        "class Smoke(unittest.TestCase):\n"
        "    def test_true(self):\n"
        "        self.assertTrue(True)\n",
        encoding="utf-8",
    )
    document = {
        "schema_version": 4,
        "id": "sample",
        "name": "Sample",
        "niche": "test products",
        "summary": "A test inventor.",
        "autonomy": "autonomous",
        "status": "experimental",
        "entrypoint": ["python3", "run.py"],
        "capabilities": ["testing"],
        "checks": check
        or [["python3", "-m", "unittest", "discover", "-s", "tests", "-v"]],
        "source": {"kind": "local"},
    }
    (folder / "inventor.json").write_text(
        json.dumps(document), encoding="utf-8"
    )
    return folder


class ContributionTest(unittest.TestCase):
    def test_valid_local_inventor_can_run_declared_checks(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = _inventor(Path(temporary))
            manifest = load_manifest(folder / "inventor.json")
            self.assertEqual(validate_contribution(manifest), [])
            self.assertEqual(run_declared_checks(manifest), [])
            self.assertEqual(manifests_for_target(folder), (manifest,))

    def test_relative_current_folder_is_a_valid_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = _inventor(Path(temporary))
            previous = Path.cwd()
            try:
                os.chdir(folder)
                manifests = manifests_for_target(Path("."))
                self.assertEqual(len(manifests), 1)
                self.assertEqual(manifests[0].inventor_id, "sample")
                self.assertTrue(manifests[0].path.is_absolute())
                self.assertEqual(run_declared_checks(manifests[0]), [])
            finally:
                os.chdir(previous)

    def test_static_check_requires_docs_tests_and_safe_runner(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = _inventor(Path(temporary), check=[["bash", "tests/run.sh"]])
            (folder / "README.md").unlink()
            (folder / "tests/test_smoke.py").unlink()
            problems = validate_contribution(load_manifest(folder / "inventor.json"))
            self.assertTrue(any("README.md" in problem for problem in problems))
            self.assertTrue(any("test_*.py" in problem for problem in problems))
            self.assertTrue(any("without a shell" in problem for problem in problems))

    def test_schema_v1_local_inventor_is_grandfathered_only_for_reading(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = _inventor(Path(temporary))
            path = folder / "inventor.json"
            document = json.loads(path.read_text(encoding="utf-8"))
            document["schema_version"] = 1
            document["core_features"] = ["taste.content-addressed"]
            document.pop("checks")
            path.write_text(json.dumps(document), encoding="utf-8")
            manifest = load_manifest(path)
            self.assertEqual(manifest.workshop_features, ("taste.content-addressed",))
            self.assertTrue(
                any("schema_version 4" in item for item in validate_contribution(manifest))
            )

    @unittest.skipIf(not hasattr(os, "symlink"), "symlink unavailable")
    def test_symlinked_contribution_target_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = _inventor(root)
            link = root / "linked-sample"
            os.symlink(folder, link)
            with self.assertRaises(ManifestError):
                manifests_for_target(link)


if __name__ == "__main__":
    unittest.main()
