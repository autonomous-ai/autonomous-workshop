import json
import shutil
import tempfile
import unittest
from pathlib import Path

from workshop.artifacts.schema_registry import discover_schemas
from workshop.contributors.extensions import fingerprint_extension_skill
from workshop.runtime.package_data import (
    BUNDLED_INVENTOR_IDS,
    PackageDataError,
    default_workshop_home,
    packaged_inventors_root,
    product_run_domain_skill_roots,
)


REPOSITORY = Path(__file__).resolve().parents[2]
SCHEMA_OWNERS = {
    "artifact-manifest.schema.json": "artifacts",
    "inventor.schema.json": "contributors",
    "cad-project.schema.json": "make",
    "validator-policy.schema.json": "make",
    "verification-receipt.schema.json": "make",
    "receipt.schema.json": "runtime",
    "concept-v1.schema.json": "concept",
    "concept-v2.schema.json": "concept",
}


class PackageDataTest(unittest.TestCase):
    def test_bundled_inventory_matches_every_source_inventor(self):
        source_ids = tuple(
            sorted(
                path.name
                for path in (REPOSITORY / "inventors").iterdir()
                if path.is_dir()
            )
        )

        self.assertEqual(BUNDLED_INVENTOR_IDS, source_ids)

    def test_product_run_domain_skills_resolve_from_owning_components(self):
        roots = product_run_domain_skill_roots()

        self.assertEqual(
            set(roots),
            {
                "cad",
                "design-reference",
                "electromechanical-integration",
                "image-to-cad",
                "manual-design",
                "step-parts",
            },
        )
        expected_owners = {
            "cad": "make",
            "design-reference": "make",
            "electromechanical-integration": "make",
            "image-to-cad": "make",
            "manual-design": "release",
            "step-parts": "make",
        }
        for name, root in roots.items():
            self.assertEqual(root.name, name)
            self.assertEqual(root.parent.name, "skills")
            self.assertEqual(root.parent.parent.name, expected_owners[name])
            self.assertTrue((root / "SKILL.md").is_file())

        manual_skill = (roots["manual-design"] / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("smallest complete physical format", manual_skill)
        self.assertIn("Default a simple one-piece Spark toy", manual_skill)
        self.assertIn("not fixed page-count gates", manual_skill)
        self.assertIn("keep customer text ASCII", manual_skill)
        self.assertIn("review-v1", manual_skill)
        self.assertIn("review-final", manual_skill)
        self.assertIn("Two complete render packets is the", manual_skill)
        manual_review = roots["manual-design"] / "scripts" / "review_manual"
        self.assertTrue(manual_review.is_file())
        self.assertTrue(manual_review.stat().st_mode & 0o111)
        visual_system = (
            roots["manual-design"]
            / "references"
            / "product-manual-visual-system.md"
        ).read_text(encoding="utf-8")
        self.assertIn("One emotional promise", visual_system)
        self.assertIn("default A4 report styling", visual_system)
        self.assertIn("Fast composition sequence", visual_system)

    def test_every_schema_is_owned_by_its_architecture_component(self):
        expected = {
            name: (
                REPOSITORY / "src" / "workshop" / owner / "schemas" / name
            ).resolve()
            for name, owner in SCHEMA_OWNERS.items()
        }
        actual = {path.name: path.resolve() for path in discover_schemas()}
        self.assertEqual(actual, expected)

    def _fake_installed_package(self, root: Path) -> tuple[Path, Path]:
        package = root / "site-packages" / "workshop"
        source = REPOSITORY / "inventors"
        packaged = package / "contributors" / "_inventors"
        for inventor_id in BUNDLED_INVENTOR_IDS:
            destination = packaged / inventor_id
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(
                source / inventor_id,
                destination,
                copy_function=shutil.copy2,
                symlinks=True,
            )
        return package / "runtime" / "package_data.py", packaged

    def test_packaged_inventors_are_validated_and_read_in_place(self):
        with tempfile.TemporaryDirectory() as temporary:
            package_file, packaged = self._fake_installed_package(Path(temporary))

            self.assertEqual(packaged_inventors_root(package_file), packaged.resolve())
            self.assertFalse((Path(temporary) / "bundled-inventors").exists())

    def test_packaged_inventors_reject_undeclared_code_without_executing_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package_file, packaged = self._fake_installed_package(root)
            marker = root / "profile-executed"
            (packaged / "alice" / "profile.py").write_text(
                "from pathlib import Path\nPath(%r).write_text('bad')\n" % str(marker),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(PackageDataError, "schema-v8 inventory"):
                packaged_inventors_root(package_file)
            self.assertFalse(marker.exists())

    def test_packaged_inventors_validate_declared_executable_skill_mode(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package_file, packaged = self._fake_installed_package(root)
            skill = packaged / "alice" / "skills" / "alice-inventor"
            script = skill / "scripts" / "shape"
            script.parent.mkdir()
            script.write_bytes(b"#!/bin/sh\nexit 0\n")
            script.chmod(0o755)
            fingerprint = fingerprint_extension_skill(
                skill.resolve(), expected_name="alice-inventor"
            )
            manifest_path = packaged / "alice" / "inventor.json"
            document = json.loads(manifest_path.read_text(encoding="utf-8"))
            document["extensions"][0]["artifact_sha256"] = (
                fingerprint.artifact_sha256
            )
            manifest_path.write_text(
                json.dumps(document, sort_keys=True) + "\n", encoding="utf-8"
            )

            self.assertEqual(packaged_inventors_root(package_file), packaged.resolve())

            script.chmod(0o644)
            with self.assertRaisesRegex(PackageDataError, "extension inventory"):
                packaged_inventors_root(package_file)

    def test_default_home_honors_only_absolute_overrides(self):
        with tempfile.TemporaryDirectory() as temporary:
            expected = Path(temporary).resolve()
            self.assertEqual(
                default_workshop_home({"WORKSHOP_HOME": str(expected)}), expected
            )
            with self.assertRaisesRegex(PackageDataError, "WORKSHOP_HOME"):
                default_workshop_home({"WORKSHOP_HOME": "relative"})


if __name__ == "__main__":
    unittest.main()
