"""Compatibility-only schema-v1 Concept round trips and freshness cases."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from workshop.artifacts import build_artifact_manifest
from workshop.concept.native import DerivedWish, NativeConcept, seal_rendered_concept
from workshop.errors import ContractError
from workshop.invent.native import NativeInvented
from workshop.match.native import MatchRankingEntry, NativeMatchAssignment
from workshop.product import ToyBlueprint
from workshop.wish import Wish


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else canonical(value)).hexdigest()


class ConceptV1CompatibilityTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.wish = Wish.create("p1", "a moon lamp", context={"route": "exact"})
        wish_sha = sha(self.wish.to_dict())
        self.assignment = NativeMatchAssignment(
            wish_sha256=wish_sha,
            inventor_roster_sha256="1" * 64,
            selected_inventor_id="eve",
            selected_agent_path=".codex/agents/eve.toml",
            selected_agent_sha256="2" * 64,
            selected_source_manifest_sha256="3" * 64,
            selected_taste_sha256="4" * 64,
            blueprint_sha256=ToyBlueprint().sha256,
            ranking=(MatchRankingEntry("eve", "Exact physical design fit."),),
        )
        self.invented = NativeInvented(
            wish_sha256=wish_sha,
            assignment_sha256=self.assignment.assignment_sha256,
            taste_sha256=self.assignment.selected_taste_sha256,
            blueprint_sha256=self.assignment.blueprint_sha256,
            concept={"title": "Moon", "summary": "Lamp"},
            research={"basis": "source"},
        )

    def write(self, root, name, value):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(canonical(value))
        return path

    def concept(self):
        root = self.root / "artifacts/concept/r0001/concept"
        descriptor = {
            "front": {"path": "images/front.png"},
            "top": {"path": "images/top.png"},
            "bottom": {"path": "images/bottom.png"},
            "exploded": {"path": "images/exploded.png"},
            "components": {"dome": {"path": "images/components/dome.png"}},
        }
        derived = DerivedWish(
            wish_sha256=self.assignment.wish_sha256,
            product_id=self.wish.product_id,
            objective=self.wish.objective,
            context=dict(self.wish.context),
            constraints={"wall_thickness_mm": 2},
        )
        documents = {
            "brief.json": {"object": "lamp"},
            "research.json": {"sources": ["bounded"]},
            "prompts.json": {"front": "bounded"},
            "descriptor.json": descriptor,
            "derived_wish.json": derived.to_dict(),
        }
        paths = {name: self.write(root, name, value) for name, value in documents.items()}
        return NativeConcept(
            round=1,
            wish_sha256=self.assignment.wish_sha256,
            assignment_sha256=self.assignment.assignment_sha256,
            taste_sha256=self.assignment.selected_taste_sha256,
            blueprint_sha256=self.assignment.blueprint_sha256,
            invented_sha256=self.invented.invented_sha256,
            concept_root="artifacts/concept/r0001/concept",
            concept_manifest=build_artifact_manifest(root, created_at="content-addressed"),
            brief=documents["brief.json"], brief_path="brief.json",
            brief_sha256=sha(paths["brief.json"].read_bytes()),
            research=documents["research.json"], research_path="research.json",
            research_sha256=sha(paths["research.json"].read_bytes()),
            drawing_instructions=documents["prompts.json"],
            drawing_instructions_path="prompts.json",
            drawing_instructions_sha256=sha(paths["prompts.json"].read_bytes()),
            descriptor=descriptor, descriptor_path="descriptor.json",
            descriptor_sha256=sha(paths["descriptor.json"].read_bytes()),
            derived_wish=derived.to_dict(), derived_wish_path="derived_wish.json",
            derived_wish_sha256_field=sha(paths["derived_wish.json"].read_bytes()),
        )

    def test_pre_render_and_sealed_schema_v1_round_trip(self):
        concept = self.concept()
        self.assertEqual(NativeConcept.from_mapping(concept.to_dict()), concept)
        concept.assert_context(self.assignment, self.invented, self.wish, expected_round=1)
        tree = concept.validate_concept_tree(self.root)
        for item in (
            tree.descriptor["front"], tree.descriptor["top"],
            tree.descriptor["bottom"], tree.descriptor["exploded"],
            tree.descriptor["components"]["dome"],
        ):
            image = tree.root / item["path"]
            image.parent.mkdir(parents=True, exist_ok=True)
            image.write_bytes(item["path"].encode())
        sealed = seal_rendered_concept(concept, self.root)
        self.assertEqual(NativeConcept.from_mapping(sealed.to_dict()), sealed)
        sealed.validate_concept_tree(self.root)

    def test_948a34d_exact_routed_wish_rewrite_is_rejected(self):
        concept = self.concept()
        rewritten = Wish.create("p1", "rewritten objective", context={"route": "exact"})
        with self.assertRaisesRegex(ContractError, "different Workshop inputs|own words"):
            concept.assert_context(self.assignment, self.invented, rewritten)

    def test_ea34822_round_freshness_rejects_replay(self):
        concept = self.concept()
        with self.assertRaisesRegex(ContractError, "stale repair round"):
            concept.assert_context(
                self.assignment, self.invented, self.wish, expected_round=2
            )


if __name__ == "__main__":
    unittest.main()
