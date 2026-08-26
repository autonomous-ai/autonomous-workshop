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


class ScaffoldTest(unittest.TestCase):
    def test_create_emits_valid_v8_open_ended_skill_bundles(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection = Path(temporary) / "inventors"
            collection.mkdir()
            descriptions = (
                "known games made personal",
                "kinetic desk toys",
                "cinematic miniature worlds",
                "physical explanations",
                "original tabletop games",
            )
            for index, description in enumerate(descriptions):
                inventor_id = "maker-%d" % index
                destination = create_inventor(
                    collection,
                    inventor_id,
                    "Maker %d" % index,
                    "%s; not generic objects." % description,
                )
                manifest = load_manifest(destination / "inventor.json")
                self.assertEqual(
                    {path.name for path in destination.iterdir()},
                    {"inventor.json", "TASTE.md", "skills"},
                )
                self.assertEqual(manifest.schema_version, 8)
                self.assertFalse(hasattr(manifest, "capabilities"))
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
            )
            taste = load_taste(destination)
            self.assertEqual(taste.name, "Mira")
            self.assertIn("## The product bar", taste.content)
            self.assertIn("Let the exact Wish and this Taste determine", taste.content)
            self.assertNotIn("Lane promise", taste.content)
            skill = (destination / "skills/mira-inventor/SKILL.md").read_text(
                encoding="utf-8"
            )
            self.assertIn(".codex/agents/mira.toml", skill)
            self.assertIn("identity and Taste embedded", skill)
            self.assertNotIn("catalog/inventors", skill)
            self.assertIn("root Workshop Manager", skill)
            self.assertIn("Do not invoke the stage finalizer", skill)
            document = json.loads((destination / "inventor.json").read_text())
            self.assertEqual(
                set(document),
                {
                    "schema_version",
                    "id",
                    "status",
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
        self.assertNotIn("lane", parameters)
        with tempfile.TemporaryDirectory() as temporary:
            collection = Path(temporary) / "inventors"
            collection.mkdir()
            with self.assertRaises(TypeError):
                create_inventor(
                    collection,
                    "mira",
                    "Mira",
                    "specific little worlds",
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
            )
            self.assertEqual(destination, collection / "ada")

    def test_rejects_invalid_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection = Path(temporary) / "inventors"
            collection.mkdir()
            cases = (
                ({"inventor_id": "Bad_ID"}, "id must match"),
                ({"inventor_id": "a" * 55}, "id must match"),
            )
            for overrides, message in cases:
                arguments = {
                    "root": collection,
                    "inventor_id": "valid",
                    "name": "Valid",
                    "description": "specific playthings; not generic objects",
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
            )
            with self.assertRaises(StateConflict):
                create_inventor(
                    collection,
                    "first",
                    "First",
                    "specific playthings; not generic objects",
                )
            (collection / "first" / "profile.py").write_text("raise RuntimeError\n")
            with self.assertRaisesRegex(ContractError, "Inventor folder"):
                create_inventor(
                    collection,
                    "second",
                    "Second",
                    "specific playthings; not generic objects",
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
                    taste_path=linked,
                )


if __name__ == "__main__":
    unittest.main()
