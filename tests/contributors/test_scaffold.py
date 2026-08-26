import json
import os
import tempfile
import unittest
from pathlib import Path

from workshop.contributors.contribution import (
    run_declared_checks,
    validate_contribution,
    validate_inventor_collection,
)
from workshop.contributors.manifest import load_manifest
from workshop.contributors.scaffold import (
    create_inventor,
    prepare_inventor_collection,
    scaffold_inventor,
)
from workshop.contributors.taste import load_taste
from workshop.errors import ContractError, StateConflict
from workshop.product import PLAYTHING_LANES


class ScaffoldTest(unittest.TestCase):
    def test_scaffold_emits_only_native_persona_inputs_for_every_lane(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection = Path(temporary) / "inventors"
            collection.mkdir()
            for index, lane in enumerate(PLAYTHING_LANES):
                inventor_id = "maker-%d" % index
                destination = scaffold_inventor(
                    collection,
                    inventor_id,
                    "Maker %d" % index,
                    "Wish-shaped %s playthings; not generic objects." % lane,
                    lane=lane,
                )
                manifest = load_manifest(destination / "inventor.json")
                self.assertEqual(
                    {path.name for path in destination.iterdir()},
                    {"inventor.json", "TASTE.md"},
                )
                self.assertEqual(manifest.schema_version, 6)
                self.assertEqual(manifest.capabilities, (lane,))
                self.assertEqual(manifest.entrypoint, ())
                self.assertEqual(manifest.checks, ())
                self.assertEqual(validate_contribution(manifest), [])
                self.assertEqual(run_declared_checks(manifest), [])
            self.assertEqual(len(validate_inventor_collection(collection)), 5)

    def test_generated_taste_is_the_only_creative_persona_input(self):
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
            self.assertEqual(
                taste.description,
                "kinetic desk toys with a precise selection boundary",
            )
            self.assertIn("A persona is data, not a Python worker", create_inventor.__doc__)
            self.assertIn("## The product bar", taste.content)
            self.assertIn("Make motion the magic", taste.content)
            document = json.loads((destination / "inventor.json").read_text())
            self.assertEqual(
                set(document),
                {"schema_version", "id", "status", "capabilities", "source"},
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
            self.assertEqual(
                {path.name for path in destination.iterdir()},
                {"inventor.json", "TASTE.md"},
            )

    def test_native_personas_reject_custom_python_levels(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection = Path(temporary) / "inventors"
            collection.mkdir()
            for level in ("custom-make", "custom-playtest"):
                with self.subTest(level=level), self.assertRaisesRegex(
                    ContractError, "customize only TASTE.md"
                ):
                    create_inventor(
                        collection,
                        "maker-%s" % level,
                        "Maker",
                        "specific playthings; not generic objects",
                        lane="moving-machines",
                        level=level,
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

    def test_legacy_template_maps_to_a_lane_without_generating_code(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection = Path(temporary) / "inventors"
            collection.mkdir()
            destination = scaffold_inventor(
                collection,
                "legacy",
                "Legacy",
                "new tabletop rules; not known classics",
                template="board-game",
            )
            manifest = load_manifest(destination / "inventor.json")
            self.assertEqual(manifest.capabilities, ("invented-games",))
            self.assertFalse(any(destination.rglob("*.py")))

    def test_rejects_invalid_identity_lane_text_and_run_checks_type(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection = Path(temporary) / "inventors"
            collection.mkdir()
            cases = (
                ({"inventor_id": "Bad_ID", "lane": "moving-machines"}, "id must match"),
                ({"inventor_id": "valid", "lane": "unknown"}, "lane must be one of"),
                (
                    {
                        "inventor_id": "valid",
                        "lane": "moving-machines",
                        "run_checks": 1,
                    },
                    "run_checks must be a boolean",
                ),
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
            with self.assertRaisesRegex(ContractError, "native persona folder"):
                create_inventor(
                    collection,
                    "second",
                    "Second",
                    "specific playthings; not generic objects",
                    lane="little-worlds",
                )
            self.assertFalse((collection / "second").exists())
            self.assertFalse(any(path.name.startswith(".second.") for path in collection.iterdir()))

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
