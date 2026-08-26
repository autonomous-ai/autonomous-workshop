import json
import os
import tempfile
import unittest
from pathlib import Path

from workshop.contributors.contribution import (
    manifests_for_target,
    run_declared_checks,
    validate_contribution,
    validate_inventor_collection,
)
from workshop.contributors.manifest import load_manifest
from workshop.errors import ManifestError


def _inventor(root: Path) -> Path:
    folder = root / "sample"
    folder.mkdir(parents=True)
    (folder / "TASTE.md").write_text(
        "---\n"
        "name: Sample\n"
        "description: Makes specific physical playthings for test Wishes.\n"
        "---\n"
        "# Taste\nSpecific and useful.\n",
        encoding="utf-8",
    )
    (folder / "inventor.json").write_text(
        json.dumps(
            {
                "schema_version": 6,
                "id": "sample",
                "status": "experimental",
                "capabilities": ["invented-games"],
                "source": {"kind": "local"},
            }
        ),
        encoding="utf-8",
    )
    return folder


class ContributionTest(unittest.TestCase):
    def test_native_persona_validation_is_static(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = _inventor(Path(temporary))
            manifest = load_manifest(folder / "inventor.json")
            self.assertEqual(validate_contribution(manifest), [])
            self.assertEqual(run_declared_checks(manifest), [])
            self.assertEqual(manifests_for_target(folder), (manifest,))
            validated = validate_inventor_collection(folder.parent)
            self.assertEqual([item.inventor_id for item in validated], ["sample"])

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
            finally:
                os.chdir(previous)

    def test_native_persona_rejects_executable_and_generated_extras(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = _inventor(Path(temporary))
            for extra in ("profile.py", "run.py"):
                (folder / extra).write_text("raise RuntimeError('must not run')\n")
            (folder / "tests").mkdir()
            (folder / "toys").mkdir()
            problems = validate_contribution(load_manifest(folder / "inventor.json"))
            self.assertEqual(len(problems), 1)
            self.assertIn("native persona folder may contain only", problems[0])
            self.assertIn("profile.py", problems[0])
            self.assertEqual(run_declared_checks(load_manifest(folder / "inventor.json")), problems)

    def test_optional_readme_must_be_regular_concise_text(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = _inventor(Path(temporary))
            manifest = load_manifest(folder / "inventor.json")
            readme = folder / "README.md"
            readme.write_text("# Sample\n", encoding="utf-8")
            self.assertEqual(validate_contribution(manifest), [])
            readme.write_bytes(b"x" * (32 * 1024 + 1))
            self.assertTrue(
                any("1 to 32768 bytes" in item for item in validate_contribution(manifest))
            )

    def test_legacy_local_manifest_is_readable_but_not_contributable(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = _inventor(Path(temporary))
            path = folder / "inventor.json"
            document = json.loads(path.read_text(encoding="utf-8"))
            document.update(
                {
                    "schema_version": 5,
                    "entrypoint": ["python3", "profile.py"],
                    "checks": [],
                }
            )
            path.write_text(json.dumps(document), encoding="utf-8")
            manifest = load_manifest(path)
            self.assertTrue(
                any("schema_version 6" in item for item in validate_contribution(manifest))
            )

    def test_contribution_rejects_a_missing_taste_discovery_header(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = _inventor(Path(temporary))
            (folder / "TASTE.md").write_text(
                "# Taste\nNo discovery metadata.\n", encoding="utf-8"
            )
            problems = validate_contribution(load_manifest(folder / "inventor.json"))
            self.assertTrue(any("discovery header" in item for item in problems))

    def test_collection_rejects_half_personas_and_extra_runtime_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = _inventor(root)
            (folder / "profile.py").write_text("raise RuntimeError\n", encoding="utf-8")
            with self.assertRaisesRegex(ManifestError, "native persona folder"):
                validate_inventor_collection(root)
            (folder / "profile.py").unlink()
            (folder / "TASTE.md").unlink()
            with self.assertRaisesRegex(ManifestError, "missing"):
                validate_inventor_collection(root)

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
