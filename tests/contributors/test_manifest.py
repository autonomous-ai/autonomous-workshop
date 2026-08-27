import json
import os
import tempfile
import unittest
from pathlib import Path

from workshop.contributors.contribution import validate_contribution
from workshop.contributors.manifest import discover_inventors, load_manifest
from workshop.errors import ManifestError


def _taste(name: str = "Sample") -> str:
    return (
        "---\n"
        "name: %s\n"
        "description: Makes a distinct kind of Wish-shaped plaything.\n"
        "---\n"
        "# Taste\nA recognizable point of view.\n" % name
    )


def _manifest(inventor_id: str = "sample"):
    skill_name = "%s-inventor" % inventor_id
    return {
        "schema_version": 8,
        "id": inventor_id,
        "status": "experimental",
        "source": {"kind": "local"},
        "extensions": [
            {
                "kind": "codex-skill",
                "name": skill_name,
                "path": "skills/%s" % skill_name,
                "artifact_sha256": "0" * 64,
            }
        ],
    }


class RegistryTest(unittest.TestCase):
    def test_bundled_inventors_are_valid_v8_skill_bundles(self):
        root = Path(__file__).resolve().parents[2]
        manifests = discover_inventors(root)
        self.assertEqual(
            [item.inventor_id for item in manifests],
            [
                "abo",
                "alice",
                "bob",
                "eve",
                "ivy",
                "leo",
                "mira-fold",
                "pico-press",
                "tess-loop",
            ],
        )
        for manifest in manifests:
            with self.subTest(inventor_id=manifest.inventor_id):
                self.assertEqual(manifest.schema_version, 8)
                self.assertEqual(len(manifest.extensions), 1)
                self.assertEqual(validate_contribution(manifest), [])
                self.assertEqual(
                    {path.name for path in manifest.path.parent.iterdir()},
                    {"TASTE.md", "inventor.json", "skills"},
                )

    def test_manifest_round_trips_only_the_v8_contract(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / "sample"
            folder.mkdir()
            path = folder / "inventor.json"
            document = _manifest()
            path.write_text(json.dumps(document), encoding="utf-8")
            manifest = load_manifest(path)
            self.assertEqual(manifest.to_dict(), document)
            self.assertEqual(
                set(vars(manifest)),
                {
                    "schema_version",
                    "inventor_id",
                    "status",
                    "source",
                    "extensions",
                    "path",
                },
            )

    def test_every_pre_v8_manifest_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / "sample"
            folder.mkdir()
            path = folder / "inventor.json"
            for version in range(1, 8):
                document = _manifest()
                document["schema_version"] = version
                path.write_text(json.dumps(document), encoding="utf-8")
                with self.subTest(version=version), self.assertRaisesRegex(
                    ManifestError, "schema_version must be 8"
                ):
                    load_manifest(path)

    def test_removed_profile_and_identity_fields_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / "sample"
            folder.mkdir()
            path = folder / "inventor.json"
            for field, value in (
                ("entrypoint", ["python3", "profile.py"]),
                ("checks", [["python3", "-m", "unittest"]]),
                ("name", "Sample"),
                ("workshop_features", []),
                ("capabilities", ["invented-games"]),
                ("lane", "invented-games"),
            ):
                document = dict(_manifest(), **{field: value})
                path.write_text(json.dumps(document), encoding="utf-8")
                with self.subTest(field=field), self.assertRaisesRegex(
                    ManifestError, "unknown fields"
                ):
                    load_manifest(path)

    def test_manifest_rejects_booleans_missing_fields_and_unpinned_sources(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / "sample"
            folder.mkdir()
            path = folder / "inventor.json"
            missing = _manifest()
            missing.pop("extensions")
            documents = (
                dict(_manifest(), schema_version=True),
                missing,
                dict(
                    _manifest(),
                    source={
                        "kind": "upstream-snapshot",
                        "url": "https://user:secret@example.test/repo",
                        "commit": "short",
                        "imported_at": "today",
                    },
                ),
            )
            for document in documents:
                with self.subTest(document=document):
                    path.write_text(json.dumps(document), encoding="utf-8")
                    with self.assertRaises(ManifestError):
                        load_manifest(path)

    def test_schema_describes_only_the_v8_contract(self):
        schema_path = (
            Path(__file__).resolve().parents[2]
            / "src/workshop/contributors/schemas/inventor.schema.json"
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertEqual(schema["$id"].rsplit("/", 1)[-1], "v8.json")
        self.assertEqual(schema["properties"]["schema_version"], {"const": 8})
        self.assertNotIn("oneOf", schema)
        self.assertEqual(
            set(schema["properties"]),
            {"schema_version", "id", "status", "source", "extensions"},
        )
        self.assertEqual(set(schema["required"]), set(schema["properties"]))

    def test_registry_fails_closed_for_missing_taste(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection = Path(temporary) / "inventors"
            collection.mkdir()
            with self.assertRaises(ManifestError):
                discover_inventors(collection)
            folder = collection / "sample"
            folder.mkdir()
            (folder / "inventor.json").write_text(
                json.dumps(_manifest()), encoding="utf-8"
            )
            with self.assertRaises(ManifestError):
                discover_inventors(collection)
            (folder / "TASTE.md").write_text(_taste(), encoding="utf-8")
            self.assertEqual(discover_inventors(collection)[0].inventor_id, "sample")

    @unittest.skipIf(not hasattr(os, "symlink"), "symlink unavailable")
    def test_registry_does_not_follow_linked_collections(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection = Path(temporary) / "inventors"
            outside = Path(temporary) / "outside"
            outside.mkdir()
            os.symlink(outside, collection)
            with self.assertRaises(ManifestError):
                discover_inventors(collection)


if __name__ == "__main__":
    unittest.main()
