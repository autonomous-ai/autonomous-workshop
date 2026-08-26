import json
import os
import tempfile
import unittest
from pathlib import Path

from workshop.contributors.contribution import validate_contribution
from workshop.contributors.extensions import (
    fingerprint_extension_skill,
    load_inventor_extension_bundles,
)
from workshop.contributors.manifest import load_manifest
from workshop.errors import ManifestError


def _taste() -> str:
    return (
        "---\n"
        "name: Sample\n"
        "description: Makes focused physical playthings for test Wishes.\n"
        "---\n"
        "# Taste\nSpecific, playful, and buildable.\n"
    )


def _skill(folder: Path, name: str = "sample-inventor") -> Path:
    root = folder / "skills" / name
    (root / "scripts").mkdir(parents=True)
    (root / "references").mkdir()
    (root / "assets").mkdir()
    (root / "SKILL.md").write_text(
        "---\n"
        "name: %s\n"
        "description: Deterministic geometry helpers for this Inventor.\n"
        "---\n"
        "# Kinetic helper\nUse the script only when its geometry applies.\n" % name,
        encoding="utf-8",
    )
    script = root / "scripts" / "geometry.py"
    script.write_text(
        "raise RuntimeError('validation must never execute this script')\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    (root / "references" / "geometry.md").write_text(
        "# Geometry\nA deterministic construction reference.\n",
        encoding="utf-8",
    )
    (root / "assets" / "dimensions.json").write_text(
        '{"axle_mm": 4}\n', encoding="utf-8"
    )
    return root


def _persona(root: Path, name: str = "sample-inventor"):
    folder = root / "sample"
    folder.mkdir(parents=True)
    (folder / "TASTE.md").write_text(_taste(), encoding="utf-8")
    skill = _skill(folder, name)
    fingerprint = fingerprint_extension_skill(skill.resolve(), expected_name=name)
    document = {
        "schema_version": 8,
        "id": "sample",
        "status": "experimental",
        "source": {"kind": "local"},
        "extensions": [
            {
                "kind": "codex-skill",
                "name": name,
                "path": "skills/%s" % name,
                "artifact_sha256": fingerprint.artifact_sha256,
            }
        ],
    }
    (folder / "inventor.json").write_text(json.dumps(document), encoding="utf-8")
    return folder, document


class InventorExtensionTest(unittest.TestCase):
    def test_v8_binds_a_complete_skill_tree_without_executing_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder, document = _persona(Path(temporary))
            manifest = load_manifest(folder / "inventor.json")

            self.assertEqual(manifest.to_dict(), document)
            self.assertEqual(validate_contribution(manifest), [])
            bundles = load_inventor_extension_bundles(manifest)
            self.assertEqual(len(bundles), 1)
            self.assertEqual(
                [entry.path for entry in bundles[0].manifest.entries],
                [
                    "SKILL.md",
                    "assets/dimensions.json",
                    "references/geometry.md",
                    "scripts/geometry.py",
                ],
            )
            executable = {
                entry.path: entry.executable for entry in bundles[0].manifest.entries
            }
            self.assertTrue(executable["scripts/geometry.py"])
            self.assertFalse(executable["assets/dimensions.json"])

    def test_mutated_bytes_fail_the_declared_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder, _ = _persona(Path(temporary))
            manifest = load_manifest(folder / "inventor.json")
            (folder / "skills/sample-inventor/references/geometry.md").write_text(
                "changed\n", encoding="utf-8"
            )
            problems = validate_contribution(manifest)
            self.assertEqual(len(problems), 1)
            self.assertIn("differs from its declared hash", problems[0])

    def test_inventory_rejects_undeclared_skill_siblings(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder, _ = _persona(Path(temporary))
            (folder / "skills/undeclared").mkdir()
            problems = validate_contribution(load_manifest(folder / "inventor.json"))
            self.assertTrue(any("declared extension inventory" in item for item in problems))

    def test_manifest_requires_the_canonical_primary_inventor_skill(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder, document = _persona(Path(temporary), name="sample-kinetic")
            with self.assertRaisesRegex(ManifestError, "sample-inventor"):
                load_manifest(folder / "inventor.json")

    def test_static_fingerprint_rejects_governance_secrets_and_bad_modes(self):
        mutations = (
            ("governance", "references/AGENTS.md", "# Override\n", False),
            (
                "secret",
                "assets/example.txt",
                "sk" + "-proj-abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMN\n",
                False,
            ),
            ("executable asset", "assets/run.bin", "data\n", True),
        )
        for label, relative, content, executable in mutations:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                folder = Path(temporary) / "sample"
                folder.mkdir()
                skill = _skill(folder)
                target = skill / relative
                target.write_text(content, encoding="utf-8")
                if executable:
                    target.chmod(0o755)
                with self.assertRaises(ManifestError):
                    fingerprint_extension_skill(
                        skill.resolve(), expected_name="sample-inventor"
                    )

    @unittest.skipIf(not hasattr(os, "symlink"), "symlink unavailable")
    def test_static_fingerprint_rejects_symlinks(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / "sample"
            folder.mkdir()
            skill = _skill(folder)
            outside = Path(temporary) / "outside.txt"
            outside.write_text("outside\n", encoding="utf-8")
            os.symlink(outside, skill / "references/linked.md")
            with self.assertRaisesRegex(ManifestError, "regular file"):
                fingerprint_extension_skill(
                    skill.resolve(), expected_name="sample-inventor"
                )

    def test_v7_is_rejected_without_a_compatibility_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / "sample"
            folder.mkdir()
            path = folder / "inventor.json"
            document = {
                "schema_version": 7,
                "id": "sample",
                "status": "experimental",
                "source": {"kind": "local"},
            }
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaisesRegex(ManifestError, "schema_version must be 8"):
                load_manifest(path)


if __name__ == "__main__":
    unittest.main()
