import argparse
import hashlib
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

import inventor_workshop.manager as manager_module
from inventor_workshop.cli import main, parser
from inventor_workshop.contribution import run_declared_checks, validate_contribution
from inventor_workshop.make import Wish
from inventor_workshop.manager import (
    TasteFit,
    WorkshopManager,
    create_shortlist,
    discover_inventor_catalog,
)
from inventor_workshop.manifest import load_manifest
from inventor_workshop.scaffold import scaffold_inventor
from inventor_workshop.taste import load_taste, load_taste_header


CREATE_RECEIPT_FIELDS = {
    "schema_version",
    "status",
    "id",
    "name",
    "description",
    "lane",
    "level",
    "path",
    "taste_sha256",
    "manifest_sha256",
    "catalog_sha256",
    "catalog_size",
    "validation",
}

JUDGE_PROVENANCE = {
    "judge_identity": "create-inventor-test-judge",
    "judge_version": "judge-and-policy-2026.08.23",
    "judge_config_sha256": hashlib.sha256(
        b"create-inventor-test-judge configuration"
    ).hexdigest(),
}


class CreateInventorTest(unittest.TestCase):
    @staticmethod
    def invoke(*arguments):
        output = StringIO()
        error = StringIO()
        with redirect_stdout(output), redirect_stderr(error):
            result = main(arguments)
        return result, output.getvalue(), error.getvalue()

    def test_create_bootstraps_catalog_validates_profile_and_returns_json_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary) / "new-workshop"
            repository.mkdir()
            description = (
                "Choose Mechanist for Wish-shaped hand-cranked desk creatures; "
                "not static miniatures, known games, or science teaching models."
            )

            result, output, error = self.invoke(
                "create",
                "inventor",
                "mechanist",
                "--description",
                description,
                "--lane",
                "moving-machines",
                "--root",
                str(repository),
                "--json",
            )

            self.assertEqual(result, 0, error)
            receipt = json.loads(output)
            self.assertTrue(CREATE_RECEIPT_FIELDS.issubset(receipt))
            self.assertEqual(receipt["schema_version"], 1)
            self.assertEqual(receipt["status"], "experimental")
            self.assertEqual(receipt["id"], "mechanist")
            self.assertEqual(receipt["name"], "Mechanist")
            self.assertEqual(receipt["description"], description)
            self.assertEqual(receipt["lane"], "moving-machines")
            self.assertEqual(receipt["level"], "taste-only")
            self.assertEqual(
                receipt["validation"], {"layout": "passed", "checks": "passed"}
            )

            destination = repository / "inventors" / "mechanist"
            self.assertTrue(destination.is_dir())
            self.assertEqual(Path(receipt["path"]), destination.resolve())
            self.assertTrue((destination / "TASTE.md").is_file())
            self.assertTrue((destination / "inventor.json").is_file())

            header = load_taste_header(destination)
            manifest = load_manifest(destination / "inventor.json")
            self.assertEqual(header.name, "Mechanist")
            self.assertEqual(header.description, description)
            self.assertEqual(manifest.schema_version, 5)
            self.assertEqual(manifest.status, "experimental")
            self.assertIn("moving-machines", manifest.capabilities)
            self.assertIn("taste-only", manifest.capabilities)
            self.assertEqual(validate_contribution(manifest), [])
            self.assertEqual(run_declared_checks(manifest), [])

            taste_sha256 = hashlib.sha256(
                (destination / "TASTE.md").read_bytes()
            ).hexdigest()
            manifest_sha256 = hashlib.sha256(
                (destination / "inventor.json").read_bytes()
            ).hexdigest()
            catalog = discover_inventor_catalog(repository)
            self.assertEqual(receipt["taste_sha256"], taste_sha256)
            self.assertEqual(receipt["manifest_sha256"], manifest_sha256)
            self.assertEqual(receipt["catalog_sha256"], catalog.catalog_sha256)
            self.assertEqual(receipt["catalog_size"], 1)
            self.assertEqual(catalog.card("mechanist").description, description)

    def test_created_inventor_is_discovered_by_header_then_routed_by_full_taste(self):
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary) / "workshop"
            repository.mkdir()
            description = (
                "Choose Ada for expressive hand-cranked creatures and compact mechanisms; "
                "not static dioramas, tabletop rules, or pure scientific demonstrations."
            )
            result, output, error = self.invoke(
                "create",
                "inventor",
                "ada",
                "--name",
                "Ada",
                "--description",
                description,
                "--lane",
                "moving-machines",
                "--level",
                "custom-make",
                "--root",
                str(repository),
                "--json",
            )
            self.assertEqual(result, 0, error)
            creation = json.loads(output)

            collection = repository / "inventors"
            scaffold_inventor(
                collection,
                "diorama-maker",
                "Diorama Maker",
                (
                    "Choose Diorama Maker for personalized static characters and tiny "
                    "worlds; not moving mechanisms, tabletop rules, or science models."
                ),
                lane="little-worlds",
                level="taste-only",
            )
            wish = Wish.create(
                "climbing-creature",
                "I wish my bicycle became a hand-cranked creature that climbs my desk.",
            )
            observed = {}

            with mock.patch.object(
                manager_module, "load_taste", wraps=load_taste
            ) as full_taste_loader:

                def loaded_taste_roots():
                    return {
                        Path(call.args[0]).name
                        for call in full_taste_loader.call_args_list
                    }

                def retriever(context):
                    self.assertEqual(loaded_taste_roots(), set())
                    self.assertEqual(len(context.catalog.cards), 2)
                    card = context.catalog.card("ada")
                    self.assertEqual(card.name, "Ada")
                    self.assertEqual(card.description, description)
                    self.assertFalse(hasattr(card, "content"))
                    observed["catalog_sha256"] = context.catalog.catalog_sha256
                    return create_shortlist(
                        context,
                        ("ada", "diorama-maker"),
                        retriever="create-inventor-test-index",
                        retriever_version="catalog-index-2026.08.23",
                        rationale=(
                            "The moving-machine card is the strongest match, while the "
                            "little-worlds card remains a plausible character-led alternative."
                        ),
                    )

                def judge(context):
                    self.assertEqual(
                        loaded_taste_roots(), {"ada", "diorama-maker"}
                    )
                    finalists = {item.inventor_id: item for item in context.finalists}
                    self.assertEqual(set(finalists), {"ada", "diorama-maker"})
                    self.assertIn("# Ada's Taste", finalists["ada"].taste.content)
                    self.assertIn("## The product bar", finalists["ada"].taste.content)
                    observed["ada_taste_sha256"] = finalists["ada"].taste.sha256
                    return (
                        TasteFit(
                            inventor_id="diorama-maker",
                            taste_sha256=finalists["diorama-maker"].taste.sha256,
                            score=31,
                            accepted=True,
                            explanation=(
                                "The character framing fits, but its static craft misses "
                                "the Wish's defining hand-cranked motion."
                            ),
                        ),
                        TasteFit(
                            inventor_id="ada",
                            taste_sha256=finalists["ada"].taste.sha256,
                            score=97,
                            accepted=True,
                            explanation=(
                                "Ada's complete Taste makes expressive hand-cranked motion "
                                "the central physical interaction requested by this Wish."
                            ),
                        ),
                    )

                manager = WorkshopManager(
                    repository,
                    retriever=retriever,
                    judge=judge,
                    **JUDGE_PROVENANCE,
                )
                assignment = manager.assign(wish, playtest_rounds=3)

            self.assertEqual(assignment.inventor_id, "ada")
            self.assertEqual(assignment.playtest_rounds, 3)
            self.assertEqual(loaded_taste_roots(), {"ada", "diorama-maker"})
            self.assertEqual(assignment.taste_sha256, creation["taste_sha256"])
            self.assertEqual(assignment.taste_sha256, observed["ada_taste_sha256"])
            self.assertNotEqual(observed["catalog_sha256"], creation["catalog_sha256"])

            audit = assignment.audit_receipt()
            decision = audit["decision"]
            self.assertEqual(decision["catalog_sha256"], observed["catalog_sha256"])
            self.assertEqual(
                decision["shortlist"]["retriever"], "create-inventor-test-index"
            )
            self.assertEqual(
                decision["shortlist"]["retriever_version"],
                "catalog-index-2026.08.23",
            )
            self.assertEqual(
                decision["judge"],
                {
                    "identity": JUDGE_PROVENANCE["judge_identity"],
                    "version": JUDGE_PROVENANCE["judge_version"],
                    "config_sha256": JUDGE_PROVENANCE["judge_config_sha256"],
                },
            )
            self.assertEqual(decision["selected"]["inventor_id"], "ada")
            self.assertEqual(
                decision["selected"]["taste_sha256"], creation["taste_sha256"]
            )

    def test_malformed_creation_leaves_no_inventor_or_staging_folder(self):
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary) / "workshop"
            repository.mkdir()
            result, output, error = self.invoke(
                "create",
                "inventor",
                "broken-maker",
                "--name",
                "Broken Maker",
                "--description",
                "This description contains\na forbidden second line.",
                "--lane",
                "moving-machines",
                "--root",
                str(repository),
                "--json",
            )

            self.assertEqual(result, 2)
            self.assertEqual(output, "")
            self.assertTrue(error)
            collection = repository / "inventors"
            self.assertFalse((collection / "broken-maker").exists())
            if collection.exists():
                self.assertEqual(list(collection.glob(".broken-maker.*")), [])

    def test_create_is_public_and_new_is_hidden_compatibility(self):
        command = parser()
        subcommands = next(
            action
            for action in command._actions
            if isinstance(action, argparse._SubParsersAction)
        )
        self.assertIn("create", subcommands.choices)
        self.assertIn("new", subcommands.choices)
        help_lines = command.format_help().splitlines()
        self.assertTrue(any(line.strip().startswith("create ") for line in help_lines))
        self.assertFalse(any(line.strip().startswith("new ") for line in help_lines))


if __name__ == "__main__":
    unittest.main()
