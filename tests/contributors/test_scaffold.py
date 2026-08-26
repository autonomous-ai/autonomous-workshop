import inspect
import json
import os
import tempfile
import unittest
from pathlib import Path

import workshop.contributors.scaffold as scaffold_module
from workshop.contributors.contribution import (
    validate_contribution,
    validate_inventor_collection,
)
from workshop.contributors.extensions import fingerprint_extension_skill
from workshop.contributors.manifest import load_manifest
from workshop.contributors.scaffold import create_inventor, prepare_inventor_collection
from workshop.contributors.taste import load_taste
from workshop.errors import ContractError, StateConflict
from workshop.product import PLAYTHING_LANES


class ScaffoldTest(unittest.TestCase):
    def test_create_emits_a_valid_v7_skill_bundle_for_every_lane(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection = Path(temporary) / "inventors"
            collection.mkdir()
            for index, lane in enumerate(PLAYTHING_LANES):
                inventor_id = "maker-%d" % index
                destination = create_inventor(
                    collection,
                    inventor_id,
                    "Maker %d" % index,
                    "Wish-shaped %s playthings; not generic objects." % lane,
                    lane=lane,
                )
                manifest = load_manifest(destination / "inventor.json")
                self.assertEqual(
                    {path.name for path in destination.iterdir()},
                    {"inventor.json", "TASTE.md", "skills"},
                )
                self.assertEqual(manifest.schema_version, 7)
                self.assertEqual(manifest.capabilities, (lane,))
                self.assertEqual(len(manifest.extensions), 1)
                extension = manifest.extensions[0]
                self.assertEqual(extension.name, "%s-inventor" % inventor_id)
                fingerprint = fingerprint_extension_skill(
                    destination / extension.path, expected_name=extension.name
                )
                self.assertEqual(
                    fingerprint.artifact_sha256, extension.artifact_sha256
                )
                self.assertEqual(validate_contribution(manifest), [])
            self.assertEqual(len(validate_inventor_collection(collection)), 5)

    def test_generated_taste_and_skill_are_the_only_creative_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection = Path(temporary) / "inventors"
            collection.mkdir()
            destination = create_inventor(
                collection,
                "mira",
                "Mira",
                "kinetic desk toys with a precise selection boundary",
                lane="moving-machines",
            )
            taste = load_taste(destination)
            self.assertEqual(taste.name, "Mira")
            self.assertIn("## The product bar", taste.content)
            self.assertIn("Make motion the magic", taste.content)
            skill = (destination / "skills/mira-inventor/SKILL.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("catalog/inventors/mira/TASTE.md", skill)
            self.assertIn("root Workshop Manager", skill)
            self.assertIn("Do not invoke the stage finalizer", skill)
            document = json.loads((destination / "inventor.json").read_text())
            self.assertEqual(
                set(document),
                {
                    "schema_version",
                    "id",
                    "status",
                    "capabilities",
                    "source",
                    "extensions",
                },
            )

    def test_existing_taste_is_preserved_byte_for_byte(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            exact = (
                b"---\nname: Nori\n"
                b"description: Makes tiny exact worlds; not generic miniatures.\n"
                b"---\n# Nori's Taste\n\nKeep this exact trailing space. \n"
            )
            taste_path = source / "TASTE.md"
            taste_path.write_bytes(exact)
            collection = root / "inventors"
            collection.mkdir()
            destination = create_inventor(
                collection,
                "nori",
                lane="little-worlds",
                taste_path=taste_path,
            )
            self.assertEqual((destination / "TASTE.md").read_bytes(), exact)
            self.assertTrue((destination / "skills/nori-inventor/SKILL.md").is_file())

    def test_legacy_scaffold_and_options_are_not_part_of_the_api(self):
        self.assertFalse(hasattr(scaffold_module, "scaffold_inventor"))
        parameters = inspect.signature(create_inventor).parameters
        self.assertNotIn("level", parameters)
        self.assertNotIn("template", parameters)
        self.assertNotIn("run_checks", parameters)
        with tempfile.TemporaryDirectory() as temporary:
            collection = Path(temporary) / "inventors"
            collection.mkdir()
            with self.assertRaises(TypeError):
                create_inventor(
                    collection,
                    "mira",
                    "Mira",
                    "specific little worlds",
                    lane="little-worlds",
                    run_checks=False,
                )

    def test_creation_bootstraps_a_repository_collection(self):
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary) / "workshop"
            repository.mkdir()
            collection = prepare_inventor_collection(repository)
            self.assertEqual(collection, (repository / "inventors").resolve())
            destination = create_inventor(
                collection,
                "ada",
                "Ada",
                "hand-cranked creatures; not static models",
                lane="moving-machines",
            )
            self.assertEqual(destination, collection / "ada")

    def test_rejects_invalid_identity_and_lane(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection = Path(temporary) / "inventors"
            collection.mkdir()
            cases = (
                ({"inventor_id": "Bad_ID", "lane": "moving-machines"}, "id must match"),
                ({"inventor_id": "a" * 55, "lane": "moving-machines"}, "id must match"),
                ({"inventor_id": "valid", "lane": "unknown"}, "lane must be one of"),
            )
            for overrides, message in cases:
                arguments = {
                    "root": collection,
                    "inventor_id": "valid",
                    "name": "Valid",
                    "description": "specific playthings; not generic objects",
                    "lane": "moving-machines",
                }
                arguments.update(overrides)
                with self.subTest(overrides=overrides), self.assertRaisesRegex(
                    ContractError, message
                ):
                    create_inventor(**arguments)

    def test_existing_destination_and_malformed_catalog_fail_before_publication(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection = Path(temporary) / "inventors"
            collection.mkdir()
            create_inventor(
                collection,
                "first",
                "First",
                "specific playthings; not generic objects",
                lane="invented-games",
            )
            with self.assertRaises(StateConflict):
                create_inventor(
                    collection,
                    "first",
                    "First",
                    "specific playthings; not generic objects",
                    lane="invented-games",
                )
            (collection / "first" / "profile.py").write_text("raise RuntimeError\n")
            with self.assertRaisesRegex(ContractError, "Inventor folder"):
                create_inventor(
                    collection,
                    "second",
                    "Second",
                    "specific playthings; not generic objects",
                    lane="little-worlds",
                )
            self.assertFalse((collection / "second").exists())
            self.assertFalse(
                any(path.name.startswith(".second.") for path in collection.iterdir())
            )

    @unittest.skipIf(not hasattr(os, "symlink"), "symlink unavailable")
    def test_symlinked_roots_and_taste_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            collection = root / "inventors"
            collection.mkdir()
            alias = root / "alias"
            os.symlink(collection, alias)
            with self.assertRaises(ContractError):
                prepare_inventor_collection(alias)

            source = root / "source"
            source.mkdir()
            taste = source / "TASTE.md"
            taste.write_text(
                "---\nname: Mira\ndescription: Makes mechanisms; not static toys.\n"
                "---\n# Taste\n",
                encoding="utf-8",
            )
            linked = root / "TASTE.md"
            os.symlink(taste, linked)
            with self.assertRaisesRegex(ContractError, "regular file named TASTE.md"):
                create_inventor(
                    collection,
                    "mira",
                    lane="moving-machines",
                    taste_path=linked,
                )


if __name__ == "__main__":
    unittest.main()
