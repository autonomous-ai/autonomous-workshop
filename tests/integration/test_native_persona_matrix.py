import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from workshop.contributors import (
    discover_inventors,
    load_taste,
    validate_contribution,
)
from workshop.match.native import (
    MatchRankingEntry,
    NativeMatchAssignment,
    PersonaCatalog,
    PersonaCatalogEntry,
)
from workshop.product import ToyBlueprint
from workshop.workflow import AgentRun


REPOSITORY = Path(__file__).resolve().parents[2]
INVENTORS = REPOSITORY / "inventors"
EXPECTED_LANES = {
    "alice": "classics-made-yours",
    "bob": "moving-machines",
    "eve": "little-worlds",
    "ivy": "holdable-science",
    "leo": "invented-games",
}


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _catalog():
    entries = []
    for manifest in discover_inventors(INVENTORS):
        entries.append(
            PersonaCatalogEntry(
                inventor_id=manifest.inventor_id,
                lane=manifest.capabilities[0],
                manifest_sha256=_sha256(manifest.path),
                taste_sha256=_sha256(manifest.path.parent / "TASTE.md"),
            )
        )
    return PersonaCatalog(tuple(entries))


class NativePersonaMatrixTest(unittest.TestCase):
    def test_all_five_inventors_are_data_only_native_personas(self):
        manifests = discover_inventors(INVENTORS)
        self.assertEqual(
            {item.inventor_id for item in manifests},
            set(EXPECTED_LANES),
        )
        for manifest in manifests:
            with self.subTest(inventor_id=manifest.inventor_id):
                self.assertTrue(manifest.native_persona)
                self.assertEqual(manifest.entrypoint, ())
                self.assertEqual(manifest.checks, ())
                self.assertEqual(
                    manifest.capabilities,
                    (EXPECTED_LANES[manifest.inventor_id],),
                )
                self.assertEqual(validate_contribution(manifest), [])
                taste = load_taste(manifest.path.parent)
                self.assertTrue(taste.content.strip())
                self.assertEqual(taste.path, manifest.path.parent / "TASTE.md")

    def test_each_persona_can_be_exactly_selected_by_the_common_match_contract(self):
        catalog = _catalog()
        wish_sha256 = "f" * 64
        self.assertEqual(
            tuple(item.inventor_id for item in catalog.personas),
            tuple(sorted(EXPECTED_LANES)),
        )
        for selected in catalog.personas:
            with self.subTest(inventor_id=selected.inventor_id):
                ordered = (selected,) + tuple(
                    item for item in catalog.personas if item != selected
                )
                assignment = NativeMatchAssignment(
                    wish_sha256=wish_sha256,
                    persona_catalog_sha256=catalog.catalog_sha256,
                    selected_inventor_id=selected.inventor_id,
                    selected_lane=selected.lane,
                    selected_manifest_sha256=selected.manifest_sha256,
                    selected_taste_sha256=selected.taste_sha256,
                    blueprint_sha256=ToyBlueprint.for_lane(selected.lane).sha256,
                    ranking=tuple(
                        MatchRankingEntry(
                            item.inventor_id,
                            (
                                "%s is the selected exact Taste fit."
                                if item == selected
                                else "%s remains a bounded alternate."
                            )
                            % item.inventor_id,
                        )
                        for item in ordered
                    ),
                )
                assignment.assert_context(
                    wish_sha256=wish_sha256,
                    catalog=catalog,
                )
                self.assertEqual(
                    NativeMatchAssignment.from_mapping(assignment.to_dict()),
                    assignment,
                )

    def test_one_common_native_run_materializes_every_persona_without_code(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            product_id = "native-persona-matrix"
            catalog_root = root / "catalog"
            for inventor_id in EXPECTED_LANES:
                source = INVENTORS / inventor_id
                destination = catalog_root / inventor_id
                destination.mkdir(parents=True)
                for name in ("inventor.json", "TASTE.md"):
                    (destination / name).write_bytes((source / name).read_bytes())
            wish = json.dumps(
                {
                    "schema_version": 1,
                    "product_id": product_id,
                    "objective": "Make one exact Wish through the shared host.",
                    "constraints": {},
                    "context": {"source": "native-persona-matrix"},
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            run = AgentRun.create(
                root / "run",
                host_state_root=root / "state",
                product_id=product_id,
                wish_bytes=wish,
                product_run_constitution_source=(
                    REPOSITORY / ".agents" / "product-run" / "AGENTS.md"
                ),
                skill_root=(
                    REPOSITORY
                    / ".agents"
                    / "skills"
                    / "autonomous-workshop"
                ),
                inventor_catalog_root=catalog_root,
            )
            checkpoint = run.snapshot()
            for inventor_id in EXPECTED_LANES:
                prefix = "catalog/inventors/%s/" % inventor_id
                self.assertIn(prefix + "inventor.json", checkpoint.input_sha256s)
                self.assertIn(prefix + "TASTE.md", checkpoint.input_sha256s)
                self.assertFalse((run.run_root / prefix / "profile.py").exists())
                self.assertFalse((run.run_root / prefix / "hook.py").exists())


if __name__ == "__main__":
    unittest.main()
