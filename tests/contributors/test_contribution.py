import json
import os
import tempfile
import unittest
from pathlib import Path

from workshop.contributors.contribution import (
    check_target,
    manifests_for_target,
    validate_contribution,
    validate_inventor_collection,
)
from workshop.contributors.extensions import fingerprint_extension_skill
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
    skill_name = "sample-inventor"
    skill = folder / "skills" / skill_name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\n"
        "name: sample-inventor\n"
        "description: Apply Sample's specialist judgment inside one Workshop run.\n"
        "---\n"
        "# Sample Inventor\nRead the exact Taste and obey the Manager.\n",
        encoding="utf-8",
    )
    fingerprint = fingerprint_extension_skill(
        skill.resolve(), expected_name=skill_name
    )
    (folder / "inventor.json").write_text(
        json.dumps(
            {
                "schema_version": 8,
                "id": "sample",
                "status": "experimental",
                "source": {"kind": "local"},
                "extensions": [
                    {
                        "kind": "codex-skill",
                        "name": skill_name,
                        "path": "skills/%s" % skill_name,
                        "artifact_sha256": fingerprint.artifact_sha256,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return folder


class ContributionTest(unittest.TestCase):
    def test_validation_is_static_and_has_no_run_mode(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = _inventor(Path(temporary))
            manifest = load_manifest(folder / "inventor.json")
            self.assertEqual(validate_contribution(manifest), [])
            self.assertEqual(check_target(folder), [])
            self.assertEqual(manifests_for_target(folder), (manifest,))
            validated = validate_inventor_collection(folder.parent)
            self.assertEqual([item.inventor_id for item in validated], ["sample"])
            with self.assertRaises(TypeError):
                check_target(folder, run=True)

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

    def test_inventor_rejects_generated_or_profile_extras(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = _inventor(Path(temporary))
            (folder / "profile.py").write_text("raise RuntimeError('must not run')\n")
            (folder / "toys").mkdir()
            problems = validate_contribution(load_manifest(folder / "inventor.json"))
            self.assertEqual(len(problems), 1)
            self.assertIn("Inventor folder may contain only", problems[0])
            self.assertIn("profile.py", problems[0])

    def test_optional_readme_must_be_regular_and_concise(self):
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

    def test_contribution_rejects_a_missing_taste_discovery_header(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = _inventor(Path(temporary))
            (folder / "TASTE.md").write_text(
                "# Taste\nNo discovery metadata.\n", encoding="utf-8"
            )
            problems = validate_contribution(load_manifest(folder / "inventor.json"))
            self.assertTrue(any("discovery header" in item for item in problems))

    def test_collection_rejects_half_inventors_and_extra_runtime_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = _inventor(root)
            (folder / "profile.py").write_text("raise RuntimeError\n", encoding="utf-8")
            with self.assertRaisesRegex(ManifestError, "Inventor folder"):
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
