import tempfile
import unittest
from pathlib import Path

from workshop.runtime.package_data import (
    BUNDLED_INVENTOR_FILES,
    BUNDLED_INVENTOR_IDS,
    PackageDataError,
    bundled_inventors_sha256,
    default_workshop_home,
    existing_bundled_catalog_roots,
    materialize_bundled_inventors,
    packaged_inventor_catalog_root,
    packaged_inventors_root,
    product_run_domain_skill_roots,
    retained_bundled_catalog_roots,
)
from workshop.contributors.manifest import discover_inventors
from workshop.artifacts.schema_registry import discover_schemas


REPOSITORY = Path(__file__).resolve().parents[2]
SCHEMA_OWNERS = {
    "artifact-manifest.schema.json": "artifacts",
    "inventor.schema.json": "contributors",
    "cad-project.schema.json": "make",
    "maker-mark.schema.json": "make",
    "validator-policy.schema.json": "make",
    "verification-receipt.schema.json": "make",
    "gate-result.schema.json": "playtest",
    "inspection-result.schema.json": "playtest",
    "playtest-result.schema.json": "playtest",
    "receipt.schema.json": "runtime",
    "stamp.schema.json": "runtime",
}


class PackageDataTest(unittest.TestCase):
    def test_product_run_domain_skills_resolve_from_make_component(self):
        roots = product_run_domain_skill_roots()

        self.assertEqual(set(roots), {"cad", "product-to-cad", "step-parts"})
        for name, root in roots.items():
            self.assertEqual(root.name, name)
            self.assertEqual(root.parent.name, "skills")
            self.assertTrue((root / "SKILL.md").is_file())

    def test_every_schema_is_owned_by_its_architecture_component(self):
        expected = {
            name: (
                REPOSITORY
                / "src"
                / "workshop"
                / owner
                / "schemas"
                / name
            ).resolve()
            for name, owner in SCHEMA_OWNERS.items()
        }
        actual = {path.name: path.resolve() for path in discover_schemas()}
        self.assertEqual(actual, expected)

    def _fake_installed_package(self, root: Path) -> tuple[Path, Path]:
        package = root / "site-packages" / "workshop"
        source = Path(__file__).resolve().parents[2] / "inventors"
        catalog = package / "contributors" / "_catalog" / "inventors"
        for inventor_id in BUNDLED_INVENTOR_IDS:
            destination = catalog / inventor_id
            destination.mkdir(parents=True)
            for filename in BUNDLED_INVENTOR_FILES:
                (destination / filename).write_bytes(
                    (source / inventor_id / filename).read_bytes()
                )
        return package / "runtime" / "package_data.py", catalog

    def test_packaged_catalog_is_validated_without_executing_profiles(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package_file, catalog = self._fake_installed_package(root)
            marker = root / "profile-executed"
            (catalog / "alice" / "profile.py").write_text(
                "from pathlib import Path\nPath(%r).write_text('bad')\n" % str(marker),
                encoding="utf-8",
            )
            self.assertEqual(packaged_inventors_root(package_file), catalog.resolve())
            self.assertEqual(
                packaged_inventor_catalog_root(package_file), catalog.resolve().parent
            )
            self.assertFalse(marker.exists())

    def test_read_only_catalog_lookup_never_creates_workshop_home(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package_file, catalog = self._fake_installed_package(root)
            home = root / "never-created" / "bundled-catalogs"
            self.assertEqual(
                retained_bundled_catalog_roots(
                    home,
                    package_file=package_file,
                    materialize_current=False,
                ),
                (),
            )
            self.assertEqual(
                existing_bundled_catalog_roots(
                    home, package_file=package_file
                ),
                (),
            )
            self.assertFalse(home.exists())
            self.assertEqual(
                packaged_inventor_catalog_root(package_file), catalog.parent.resolve()
            )

    def test_materialized_catalog_preserves_exact_identity_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package_file, catalog = self._fake_installed_package(root)
            destination = root / "state" / "catalogs"
            materialized = materialize_bundled_inventors(
                destination, package_file=package_file
            )
            self.assertNotEqual(materialized, catalog)
            self.assertEqual(materialized.parent, destination)
            self.assertEqual(materialized.name, bundled_inventors_sha256(catalog))
            manifests = discover_inventors(materialized)
            self.assertEqual(
                [manifest.inventor_id for manifest in manifests],
                list(BUNDLED_INVENTOR_IDS),
            )
            for inventor_id in BUNDLED_INVENTOR_IDS:
                for filename in BUNDLED_INVENTOR_FILES:
                    self.assertEqual(
                        (materialized / "inventors" / inventor_id / filename).read_bytes(),
                        (catalog / inventor_id / filename).read_bytes(),
                    )
            self.assertEqual(
                materialize_bundled_inventors(destination, package_file=package_file),
                materialized,
            )

    def test_materialized_catalog_fails_closed_after_identity_change(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package_file, _ = self._fake_installed_package(root)
            destination = root / "catalogs"
            materialized = materialize_bundled_inventors(
                destination, package_file=package_file
            )
            changed = materialized / "inventors" / "alice" / "TASTE.md"
            changed.chmod(0o644)
            changed.write_bytes(changed.read_bytes() + b"\nchanged\n")
            with self.assertRaisesRegex(PackageDataError, "differs"):
                materialize_bundled_inventors(destination, package_file=package_file)

    def test_upgrade_retains_exact_old_catalog_and_runtime_for_resume(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package_file, packaged = self._fake_installed_package(root)
            destination = root / "catalogs"
            old = materialize_bundled_inventors(
                destination, package_file=package_file
            )
            old_runtime = old / "inventors" / "alice" / ".workshop"
            old_runtime.mkdir()
            (old_runtime / "in-flight-wish").write_text("old-bound-state\n")

            upgraded_taste = packaged / "alice" / "TASTE.md"
            upgraded_taste.write_bytes(upgraded_taste.read_bytes() + b"\n")
            current = materialize_bundled_inventors(
                destination, package_file=package_file
            )
            self.assertNotEqual(current, old)
            self.assertFalse(
                (current / "inventors" / "alice" / ".workshop").exists()
            )
            self.assertEqual(
                (old_runtime / "in-flight-wish").read_text(), "old-bound-state\n"
            )
            self.assertEqual(
                retained_bundled_catalog_roots(
                    destination, package_file=package_file
                ),
                (current, old),
            )
            self.assertEqual(
                existing_bundled_catalog_roots(
                    destination, package_file=package_file
                ),
                (current, old),
            )

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
