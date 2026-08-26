import json
import os
import re
import tempfile
import unittest
from pathlib import Path

from workshop.contributors.contribution import validate_contribution
from workshop.contributors.manifest import (
    discover_inventors,
    load_manifest,
    validate_entrypoints,
)
from workshop.errors import ManifestError
from workshop.product import PLAYTHING_LANES


def _taste(name: str = "Sample") -> str:
    return (
        "---\n"
        "name: %s\n"
        "description: Makes a distinct kind of Wish-shaped plaything.\n"
        "---\n"
        "# Taste\nA recognizable point of view.\n" % name
    )


def _native_manifest(inventor_id: str = "sample", lane: str = "invented-games"):
    return {
        "schema_version": 6,
        "id": inventor_id,
        "status": "experimental",
        "capabilities": [lane],
        "source": {"kind": "local"},
    }


class RegistryTest(unittest.TestCase):
    def test_bundled_personas_are_lean_native_manifests(self):
        root = Path(__file__).resolve().parents[2]
        manifests = discover_inventors(root)
        self.assertEqual(
            [item.inventor_id for item in manifests],
            ["alice", "bob", "eve", "ivy", "leo"],
        )
        self.assertEqual(validate_entrypoints(manifests), [])
        self.assertTrue(all(item.native_persona for item in manifests))
        for manifest in manifests:
            with self.subTest(inventor_id=manifest.inventor_id):
                self.assertEqual(manifest.entrypoint, ())
                self.assertEqual(manifest.checks, ())
                self.assertEqual(validate_contribution(manifest), [])
                self.assertEqual(
                    {path.name for path in manifest.path.parent.iterdir()},
                    {"TASTE.md", "inventor.json"},
                )

    def test_native_manifest_round_trips_without_operational_fields(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / "sample"
            folder.mkdir()
            path = folder / "inventor.json"
            document = _native_manifest()
            path.write_text(json.dumps(document), encoding="utf-8")
            manifest = load_manifest(path)
            self.assertEqual(manifest.to_dict(), document)
            self.assertEqual(manifest.entrypoint, ())
            self.assertEqual(manifest.checks, ())
            self.assertTrue(manifest.native_persona)

            for forbidden, value in (
                ("entrypoint", ["python3", "profile.py"]),
                ("checks", [["python3", "-m", "unittest"]]),
                ("name", "Sample"),
                ("workshop_features", []),
            ):
                with self.subTest(forbidden=forbidden):
                    path.write_text(
                        json.dumps(dict(document, **{forbidden: value})),
                        encoding="utf-8",
                    )
                    with self.assertRaisesRegex(ManifestError, "schema_version 6"):
                        load_manifest(path)

    def test_native_manifest_requires_exactly_one_known_lane(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / "sample"
            folder.mkdir()
            path = folder / "inventor.json"
            for capabilities in ([], ["taste-only"], list(PLAYTHING_LANES[:2])):
                with self.subTest(capabilities=capabilities):
                    path.write_text(
                        json.dumps(dict(_native_manifest(), capabilities=capabilities)),
                        encoding="utf-8",
                    )
                    with self.assertRaises(ManifestError):
                        load_manifest(path)

    def test_registry_accepts_an_open_native_persona_collection(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection = Path(temporary) / "inventors"
            collection.mkdir()
            lanes = tuple(PLAYTHING_LANES)
            for index in range(8):
                inventor_id = "inventor-%d" % index
                folder = collection / inventor_id
                folder.mkdir()
                (folder / "TASTE.md").write_text(
                    _taste("Inventor %d" % index), encoding="utf-8"
                )
                (folder / "inventor.json").write_text(
                    json.dumps(_native_manifest(inventor_id, lanes[index % len(lanes)])),
                    encoding="utf-8",
                )
            manifests = discover_inventors(collection)
            self.assertEqual(len(manifests), 8)
            self.assertEqual(validate_entrypoints(manifests), [])

    def test_registry_fails_closed_for_missing_or_invalid_taste(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection = Path(temporary) / "inventors"
            collection.mkdir()
            with self.assertRaises(ManifestError):
                discover_inventors(collection)
            folder = collection / "sample"
            folder.mkdir()
            (folder / "inventor.json").write_text(
                json.dumps(_native_manifest()), encoding="utf-8"
            )
            with self.assertRaises(ManifestError):
                discover_inventors(collection)
            (folder / "TASTE.md").write_text("  \n", encoding="utf-8")
            with self.assertRaises(ManifestError):
                discover_inventors(collection)
            (folder / "TASTE.md").write_text(_taste(), encoding="utf-8")
            self.assertEqual(discover_inventors(collection)[0].inventor_id, "sample")

    def test_manifest_rejects_boolean_versions_unknown_fields_and_unpinned_sources(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / "sample"
            folder.mkdir()
            path = folder / "inventor.json"
            for document in (
                dict(_native_manifest(), schema_version=True),
                dict(_native_manifest(), surprise=True),
                dict(
                    _native_manifest(),
                    source={
                        "kind": "upstream-snapshot",
                        "url": "https://user:secret@example.test/repo",
                        "commit": "short",
                        "imported_at": "today",
                    },
                ),
            ):
                with self.subTest(document=document):
                    path.write_text(json.dumps(document), encoding="utf-8")
                    with self.assertRaises(ManifestError):
                        load_manifest(path)

    def test_schema_describes_native_personas_and_legacy_read_compatibility(self):
        schema_path = (
            Path(__file__).resolve().parents[2]
            / "src/workshop/contributors/schemas/inventor.schema.json"
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertEqual(schema["$id"].rsplit("/", 1)[-1], "v6.json")
        self.assertEqual(
            set(schema["required"]),
            {"schema_version", "id", "status", "capabilities", "source"},
        )
        versions = {
            branch["properties"]["schema_version"]["const"]: branch
            for branch in schema["oneOf"]
        }
        self.assertEqual(set(versions), {1, 2, 3, 4, 5, 6})
        forbidden_v6 = {
            condition["required"][0]
            for condition in versions[6]["not"]["anyOf"]
        }
        self.assertTrue({"entrypoint", "checks"}.issubset(forbidden_v6))
        lane_enum = versions[6]["properties"]["capabilities"]["items"]["enum"]
        self.assertEqual(set(lane_enum), set(PLAYTHING_LANES))
        for field in ("name", "niche", "summary"):
            pattern = schema["properties"][field]["pattern"]
            self.assertFalse(re.fullmatch(pattern, "   "))

    def test_schema_v5_remains_read_only_compatibility(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / "sample"
            folder.mkdir()
            (folder / "profile.py").write_text("# legacy\n", encoding="utf-8")
            path = folder / "inventor.json"
            document = {
                "schema_version": 5,
                "id": "sample",
                "status": "archived",
                "entrypoint": ["python3", "profile.py"],
                "capabilities": ["testing"],
                "checks": [],
                "source": {"kind": "local"},
            }
            path.write_text(json.dumps(document), encoding="utf-8")
            manifest = load_manifest(path)
            self.assertEqual(manifest.to_dict(), document)
            self.assertFalse(manifest.native_persona)
            self.assertEqual(validate_entrypoints((manifest,)), [])
            self.assertTrue(
                any("schema_version 6" in item for item in validate_contribution(manifest))
            )

    @unittest.skipIf(not hasattr(os, "symlink"), "symlink unavailable")
    def test_registry_does_not_follow_external_folders_or_collections(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "registry"
            root.mkdir()
            outside = Path(temporary) / "outside"
            outside.mkdir()
            (outside / "inventor.json").write_text("{}", encoding="utf-8")
            os.symlink(outside, root / "outside")
            with self.assertRaises(ManifestError):
                discover_inventors(root)

            repository = Path(temporary) / "repository"
            repository.mkdir()
            os.symlink(root, repository / "inventors")
            with self.assertRaises(ManifestError):
                discover_inventors(repository)


if __name__ == "__main__":
    unittest.main()
