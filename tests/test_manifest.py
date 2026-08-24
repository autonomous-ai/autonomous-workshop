import json
import os
import re
import tempfile
import unittest
from pathlib import Path

from inventor_workshop.errors import ManifestError
from inventor_workshop.manifest import (
    discover_inventors,
    load_manifest,
    validate_entrypoints,
)


class RegistryTest(unittest.TestCase):
    def test_manifest_rejects_boolean_schema_versions(self):
        document = {
            "schema_version": True,
            "id": "sample",
            "name": "Sample",
            "niche": "test products",
            "summary": "A test inventor.",
            "autonomy": "reference",
            "status": "reference",
            "entrypoint": ["python3", "sample.py"],
            "capabilities": ["testing"],
            "core_features": [],
            "source": {"kind": "local"},
        }
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / "sample"
            folder.mkdir()
            (folder / "TASTE.md").write_text("# Taste\n", encoding="utf-8")
            path = folder / "inventor.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaisesRegex(ManifestError, "schema_version"):
                load_manifest(path)

    def test_repo_has_five_valid_inventors(self):
        root = Path(__file__).resolve().parents[1]
        manifests = discover_inventors(root)
        self.assertEqual(
            [item.inventor_id for item in manifests],
            ["alice", "bob", "eve", "ivy", "leo"],
        )
        self.assertEqual(validate_entrypoints(manifests), [])
        self.assertEqual(
            [item.inventor_id for item in discover_inventors(root / "inventors")],
            [item.inventor_id for item in manifests],
        )

    def test_registry_fails_closed_for_an_empty_collection(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection = Path(temporary) / "inventors"
            collection.mkdir()
            with self.assertRaises(ManifestError):
                discover_inventors(collection)

    def test_registry_requires_a_bounded_regular_taste_contract(self):
        manifest = {
            "schema_version": 1,
            "id": "sample",
            "name": "Sample",
            "niche": "test products",
            "summary": "A test inventor.",
            "autonomy": "reference",
            "status": "reference",
            "entrypoint": ["python3", "run.py"],
            "capabilities": ["testing"],
            "core_features": [],
            "source": {"kind": "local"},
        }
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / "sample"
            folder.mkdir()
            (folder / "inventor.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            with self.assertRaises(ManifestError):
                discover_inventors(Path(temporary))
            (folder / "TASTE.md").write_text("  \n", encoding="utf-8")
            with self.assertRaises(ManifestError):
                discover_inventors(Path(temporary))
            (folder / "TASTE.md").write_text("# Sample taste\n", encoding="utf-8")
            self.assertEqual(discover_inventors(Path(temporary))[0].inventor_id, "sample")

    def test_manifest_rejects_unknown_fields_and_unpinned_upstream(self):
        base = {
            "schema_version": 1,
            "id": "sample",
            "name": "Sample",
            "niche": "test products",
            "summary": "A test inventor.",
            "autonomy": "reference",
            "status": "reference",
            "entrypoint": ["python3", "sample.py"],
            "capabilities": ["testing"],
            "core_features": [],
            "source": {"kind": "local"},
        }
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / "sample"
            folder.mkdir()
            path = folder / "inventor.json"
            path.write_text(json.dumps(dict(base, surprise=True)), encoding="utf-8")
            with self.assertRaises(ManifestError):
                load_manifest(path)

            injected = dict(base)
            injected["summary"] = "safe\nforged registry row"
            path.write_text(json.dumps(injected), encoding="utf-8")
            with self.assertRaises(ManifestError):
                load_manifest(path)

            for unsafe_url in (
                "https://user:secret@example.test/repo",
                "https://example.test/repo?token=secret",
                "https://example.test/repo#mutable-ref",
                "https:///repo",
            ):
                with self.subTest(url=unsafe_url):
                    bad_url = dict(base)
                    bad_url["source"] = {
                        "kind": "upstream-snapshot",
                        "url": unsafe_url,
                        "commit": "a" * 40,
                        "imported_at": "2026-08-23",
                    }
                    path.write_text(json.dumps(bad_url), encoding="utf-8")
                    with self.assertRaises(ManifestError):
                        load_manifest(path)

            missing_source = dict(base)
            del missing_source["source"]
            path.write_text(json.dumps(missing_source), encoding="utf-8")
            with self.assertRaises(ManifestError):
                load_manifest(path)

            missing_core_features = dict(base)
            del missing_core_features["core_features"]
            path.write_text(json.dumps(missing_core_features), encoding="utf-8")
            with self.assertRaises(ManifestError):
                load_manifest(path)

            blank_name = dict(base)
            blank_name["name"] = "   "
            path.write_text(json.dumps(blank_name), encoding="utf-8")
            with self.assertRaises(ManifestError):
                load_manifest(path)

            bad = dict(base)
            bad["source"] = {
                "kind": "upstream-snapshot",
                "url": "http://example.test/repo",
                "commit": "short",
                "imported_at": "today",
            }
            path.write_text(json.dumps(bad), encoding="utf-8")
            with self.assertRaises(ManifestError):
                load_manifest(path)

    def test_manifest_schema_tracks_required_and_bounded_runtime_fields(self):
        schema_path = (
            Path(__file__).resolve().parents[1] / "schemas" / "inventor.schema.json"
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertEqual(
            set(schema["required"]),
            {
                "schema_version",
                "id",
                "name",
                "niche",
                "summary",
                "autonomy",
                "status",
                "entrypoint",
                "capabilities",
                "source",
            },
        )
        versions = {
            branch["properties"]["schema_version"]["const"]: set(
                branch["required"]
            )
            for branch in schema["oneOf"]
        }
        self.assertEqual(versions[1], {"core_features"})
        self.assertEqual(versions[2], {"foundation_features", "checks"})
        self.assertEqual(versions[3], {"workshop_features", "checks"})
        self.assertEqual(versions[4], {"checks"})
        for field in ("name", "niche", "summary"):
            pattern = schema["properties"][field]["pattern"]
            self.assertFalse(re.fullmatch(pattern, "   "))
            self.assertTrue(re.fullmatch(pattern, "A bounded value"))
        imported_at = schema["properties"]["source"]["properties"]["imported_at"]
        self.assertEqual(imported_at["format"], "date")

    def test_schema_v3_uses_workshop_vocabulary_and_declared_checks(self):
        document = {
            "schema_version": 3,
            "id": "sample",
            "name": "Sample",
            "niche": "test products",
            "summary": "A test inventor.",
            "autonomy": "autonomous",
            "status": "experimental",
            "entrypoint": ["python3", "sample.py"],
            "capabilities": ["testing"],
            "workshop_features": ["make.workbench"],
            "checks": [["python3", "-m", "unittest", "discover", "-s", "tests"]],
            "source": {"kind": "local"},
        }
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / "sample"
            folder.mkdir()
            path = folder / "inventor.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            manifest = load_manifest(path)
            self.assertEqual(manifest.workshop_features, ("make.workbench",))
            self.assertEqual(manifest.to_dict(), document)
            legacy = dict(document, core_features=[])
            path.write_text(json.dumps(legacy), encoding="utf-8")
            with self.assertRaisesRegex(ManifestError, "not.*core_features"):
                load_manifest(path)

    def test_schema_v2_foundation_manifest_is_read_only_compatibility(self):
        document = {
            "schema_version": 2,
            "id": "sample",
            "name": "Sample",
            "niche": "test products",
            "summary": "A test inventor.",
            "autonomy": "reference",
            "status": "reference",
            "entrypoint": ["python3", "sample.py"],
            "capabilities": ["testing"],
            "foundation_features": ["legacy.feature"],
            "checks": [],
            "source": {"kind": "local"},
        }
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / "sample"
            folder.mkdir()
            path = folder / "inventor.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            manifest = load_manifest(path)
            self.assertEqual(manifest.workshop_features, ("legacy.feature",))
            self.assertEqual(manifest.to_dict(), document)

    def test_schema_v3_rejects_unreviewed_feature_names(self):
        document = {
            "schema_version": 3,
            "id": "sample",
            "name": "Sample",
            "niche": "test products",
            "summary": "A test inventor.",
            "autonomy": "reference",
            "status": "reference",
            "entrypoint": ["python3", "sample.py"],
            "capabilities": ["testing"],
            "workshop_features": ["spark.magic"],
            "checks": [],
            "source": {"kind": "local"},
        }
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / "sample"
            folder.mkdir()
            path = folder / "inventor.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaisesRegex(ManifestError, "unknown workshop_features"):
                load_manifest(path)

    def test_schema_v4_needs_checks_and_has_no_feature_inventory(self):
        document = {
            "schema_version": 4,
            "id": "sample",
            "name": "Sample",
            "niche": "test products",
            "summary": "A test inventor.",
            "autonomy": "autonomous",
            "status": "experimental",
            "entrypoint": ["python3", "sample.py"],
            "capabilities": ["testing"],
            "checks": [["python3", "-m", "unittest"]],
            "source": {"kind": "local"},
        }
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / "sample"
            folder.mkdir()
            path = folder / "inventor.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            manifest = load_manifest(path)
            self.assertEqual(manifest.workshop_features, ())
            self.assertEqual(manifest.to_dict(), document)

            legacy_inventory = dict(document, workshop_features=[])
            path.write_text(json.dumps(legacy_inventory), encoding="utf-8")
            with self.assertRaisesRegex(ManifestError, "no feature inventory"):
                load_manifest(path)

            no_checks = dict(document)
            del no_checks["checks"]
            path.write_text(json.dumps(no_checks), encoding="utf-8")
            with self.assertRaisesRegex(ManifestError, "checks is required"):
                load_manifest(path)

    @unittest.skipIf(not hasattr(os, "symlink"), "symlink unavailable")
    def test_entrypoint_symlink_cannot_escape_inventor_folder(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            outside = root / "outside.py"
            outside.write_text("raise SystemExit(0)\n", encoding="utf-8")
            folder = root / "sample"
            folder.mkdir()
            os.symlink(outside, folder / "run.py")
            raw = {
                "schema_version": 1,
                "id": "sample",
                "name": "Sample",
                "niche": "test products",
                "summary": "A test inventor.",
                "autonomy": "reference",
                "status": "reference",
                "entrypoint": ["python3", "run.py"],
                "capabilities": ["testing"],
                "core_features": [],
                "source": {"kind": "local"},
            }
            manifest_path = folder / "inventor.json"
            manifest_path.write_text(json.dumps(raw), encoding="utf-8")
            problems = validate_entrypoints([load_manifest(manifest_path)])
            self.assertEqual(
                problems,
                ["sample: entrypoint target run.py is missing"],
            )

    @unittest.skipIf(not hasattr(os, "symlink"), "symlink unavailable")
    def test_registry_does_not_follow_an_external_inventor_folder(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "registry"
            root.mkdir()
            outside = Path(temporary) / "outside"
            outside.mkdir()
            (outside / "inventor.json").write_text("{}", encoding="utf-8")
            os.symlink(outside, root / "outside")
            with self.assertRaises(ManifestError):
                discover_inventors(root)

    @unittest.skipIf(not hasattr(os, "symlink"), "symlink unavailable")
    def test_registry_does_not_follow_an_external_inventors_collection(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repository"
            root.mkdir()
            outside = Path(temporary) / "outside"
            outside.mkdir()
            os.symlink(outside, root / "inventors")
            with self.assertRaises(ManifestError):
                discover_inventors(root)


if __name__ == "__main__":
    unittest.main()
