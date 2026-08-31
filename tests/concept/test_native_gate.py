"""Failure-path tests for the deterministic Concept brief rules."""

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from workshop.artifacts import build_artifact_manifest
from workshop.concept.native import NativeConcept
from workshop.concept.native_gate import evaluate_concept_brief
from workshop.errors import ContractError
from workshop.wish import Wish


FAKE = "0" * 64


def _sha(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


class ConceptNativeGateTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.wish = Wish(
            schema_version=1,
            product_id="p1",
            objective="a lamp shaped like a moon",
            constraints={},
            context={},
        )
        self.brief = {
            "object": "moon lamp",
            "category": "lighting",
            "envelope_mm": {"length_mm": 120.0, "width_mm": 120.0, "height_mm": 150.0},
            "wall_thickness_mm": 2.4,
            "print_stance": {
                "orientation": "vertical, dome up",
                "supports_required": False,
                "support_notes": "self-supporting dome geometry",
            },
            "features": [
                {"id": "cratered_surface", "text": "cratered lunar surface texture"}
            ],
            "fit_target": None,
            "components": [
                {
                    "key": "dome",
                    "name": "Dome",
                    "purpose": "diffuses light",
                    "form": "hollow hemisphere",
                    "dimensions_mm": {
                        "length_mm": 120.0,
                        "width_mm": 120.0,
                        "height_mm": 100.0,
                    },
                    "placement": "sits atop the base",
                    "interfaces": "snap-fits onto the base",
                },
            ],
            "facts": [
                {"field": "object", "source_id": None, "assumption_reason": "decided"},
                {"field": "category", "source_id": None, "assumption_reason": "decided"},
                {"field": "envelope_mm", "source_id": "s1", "assumption_reason": None},
                {
                    "field": "wall_thickness_mm",
                    "source_id": "s1",
                    "assumption_reason": None,
                },
                {
                    "field": "print_stance",
                    "source_id": None,
                    "assumption_reason": "decided",
                },
                {
                    "field": "features.cratered_surface",
                    "source_id": "s1",
                    "assumption_reason": None,
                },
                {
                    "field": "components.dome",
                    "source_id": None,
                    "assumption_reason": "single printed part",
                },
            ],
        }
        self.research = {
            "sources": [
                {
                    "id": "s1",
                    "origin": "https://example.com/moon-lamp",
                    "excerpt": "moon lamps are commonly domed",
                    "excerpt_sha256": _sha("moon lamps are commonly domed"),
                    "retrieved_at": "2026-08-26T00:00:00+00:00",
                }
            ],
            "findings": [
                {"finding": "moon lamps are commonly domed", "source_ids": ["s1"]}
            ],
        }
        self.drawing_instructions = {
            "front": {"instruction": "The moon lamp, front view.", "references": []},
            "top": {"instruction": "Same object, from above.", "references": ["front"]},
            "bottom": {
                "instruction": "Same object, from below.",
                "references": ["front"],
            },
            "exploded": {
                "instruction": "Show the Dome fully separated and wholly visible.",
                "references": ["front", "top", "bottom"],
            },
            "components": {
                "dome": {
                    "instruction": "The Dome alone, matching the reference finish.",
                    "references": ["front"],
                },
            },
        }
        self.descriptor = {
            "front": {"path": "images/front.png", "sha256": FAKE},
            "top": {"path": "images/top.png", "sha256": FAKE},
            "bottom": {"path": "images/bottom.png", "sha256": FAKE},
            "exploded": {"path": "images/exploded.png", "sha256": FAKE},
            "components": {"dome": {"path": "images/components/dome.png", "sha256": FAKE}},
        }

    def _tree(self, *, brief=None, research=None, drawing_instructions=None, descriptor=None):
        concept_root = self.root / "artifacts/concept/r0001/concept"
        if concept_root.exists():
            import shutil

            shutil.rmtree(concept_root)
        (concept_root / "images/components").mkdir(parents=True)
        for name in ("front.png", "top.png", "bottom.png", "exploded.png"):
            (concept_root / "images" / name).write_bytes(name.encode())
        (concept_root / "images/components/dome.png").write_bytes(b"dome")

        brief = brief if brief is not None else self.brief
        research = research if research is not None else self.research
        drawing_instructions = (
            drawing_instructions if drawing_instructions is not None else self.drawing_instructions
        )
        descriptor = descriptor if descriptor is not None else self.descriptor
        descriptor = copy.deepcopy(descriptor)

        def _real_sha(path):
            return hashlib.sha256((concept_root / path).read_bytes()).hexdigest()

        for role in ("front", "top", "bottom", "exploded"):
            if role in descriptor:
                descriptor[role]["sha256"] = _real_sha("images/%s.png" % role)
        if "dome" in descriptor.get("components", {}):
            descriptor["components"]["dome"]["sha256"] = _real_sha(
                "images/components/dome.png"
            )

        derived_wish = {
            "schema_version": 1,
            "kind": "autonomous-workshop.concept-derived-wish",
            "wish_sha256": FAKE,
            "product_id": "p1",
            "objective": self.wish.objective,
            "context": {},
            "constraints": {"envelope_mm": brief.get("envelope_mm", {})},
        }
        derived_identity = dict(derived_wish)
        derived_wish["derived_wish_sha256"] = _sha(derived_identity)

        files = {
            "brief.json": brief,
            "research.json": research,
            "prompts.json": drawing_instructions,
            "descriptor.json": descriptor,
            "derived_wish.json": derived_wish,
        }
        for name, value in files.items():
            (concept_root / name).write_text(
                json.dumps(value, sort_keys=True, separators=(",", ":"))
            )

        manifest = build_artifact_manifest(concept_root, created_at="content-addressed")
        native_concept = NativeConcept(
            round=1,
            wish_sha256=FAKE,
            assignment_sha256=FAKE,
            taste_sha256=FAKE,
            blueprint_sha256=FAKE,
            invented_sha256=FAKE,
            concept_root="artifacts/concept/r0001/concept",
            concept_manifest=manifest,
            brief=brief,
            brief_path="brief.json",
            brief_sha256=hashlib.sha256((concept_root / "brief.json").read_bytes()).hexdigest(),
            research=research,
            research_path="research.json",
            research_sha256=hashlib.sha256(
                (concept_root / "research.json").read_bytes()
            ).hexdigest(),
            drawing_instructions=drawing_instructions,
            drawing_instructions_path="prompts.json",
            drawing_instructions_sha256=hashlib.sha256(
                (concept_root / "prompts.json").read_bytes()
            ).hexdigest(),
            descriptor=descriptor,
            descriptor_path="descriptor.json",
            descriptor_sha256=hashlib.sha256(
                (concept_root / "descriptor.json").read_bytes()
            ).hexdigest(),
            derived_wish=derived_wish,
            derived_wish_path="derived_wish.json",
            derived_wish_sha256_field=hashlib.sha256(
                (concept_root / "derived_wish.json").read_bytes()
            ).hexdigest(),
        )
        return native_concept.validate_concept_tree(self.root)

    def test_valid_brief_passes(self):
        tree = self._tree()
        checks = evaluate_concept_brief(tree, wish=self.wish)
        self.assertEqual(checks["object"], "moon lamp")

    def test_missing_wall_thickness_is_refused(self):
        brief = copy.deepcopy(self.brief)
        del brief["wall_thickness_mm"]
        tree = self._tree(brief=brief)
        with self.assertRaisesRegex(ContractError, "wall_thickness_mm"):
            evaluate_concept_brief(tree, wish=self.wish)

    def test_component_missing_form_is_refused(self):
        brief = copy.deepcopy(self.brief)
        del brief["components"][0]["form"]
        tree = self._tree(brief=brief)
        with self.assertRaisesRegex(ContractError, "form"):
            evaluate_concept_brief(tree, wish=self.wish)

    def test_unattributed_fact_is_refused(self):
        brief = copy.deepcopy(self.brief)
        brief["facts"] = [f for f in brief["facts"] if f["field"] != "wall_thickness_mm"]
        tree = self._tree(brief=brief)
        with self.assertRaisesRegex(ContractError, "unattributed"):
            evaluate_concept_brief(tree, wish=self.wish)

    def test_fact_with_both_attributions_is_refused(self):
        brief = copy.deepcopy(self.brief)
        for fact in brief["facts"]:
            if fact["field"] == "envelope_mm":
                fact["assumption_reason"] = "also a decision"
        tree = self._tree(brief=brief)
        with self.assertRaisesRegex(ContractError, "exactly one"):
            evaluate_concept_brief(tree, wish=self.wish)

    def test_restated_objective_only_feature_is_refused(self):
        brief = copy.deepcopy(self.brief)
        brief["features"] = [{"id": "restated", "text": self.wish.objective}]
        brief["facts"] = [
            f for f in brief["facts"] if not f["field"].startswith("features.")
        ]
        brief["facts"].append(
            {"field": "features.restated", "source_id": "s1", "assumption_reason": None}
        )
        tree = self._tree(brief=brief)
        with self.assertRaisesRegex(ContractError, "restates the Wish objective"):
            evaluate_concept_brief(tree, wish=self.wish)

    def test_missing_drawing_instruction_role_is_refused(self):
        instructions = copy.deepcopy(self.drawing_instructions)
        del instructions["top"]
        tree = self._tree(drawing_instructions=instructions)
        with self.assertRaisesRegex(ContractError, "front, top, bottom"):
            evaluate_concept_brief(tree, wish=self.wish)

    def test_component_reference_to_exploded_is_refused(self):
        instructions = copy.deepcopy(self.drawing_instructions)
        instructions["components"]["dome"]["references"] = ["front", "exploded"]
        tree = self._tree(drawing_instructions=instructions)
        with self.assertRaisesRegex(ContractError, "never exploded"):
            evaluate_concept_brief(tree, wish=self.wish)

    def test_exploded_instruction_missing_a_component_name_is_refused(self):
        instructions = copy.deepcopy(self.drawing_instructions)
        instructions["exploded"]["instruction"] = "Show the whole lamp separated."
        tree = self._tree(drawing_instructions=instructions)
        with self.assertRaisesRegex(ContractError, "must name every component"):
            evaluate_concept_brief(tree, wish=self.wish)

    def test_descriptor_missing_a_component_image_is_refused(self):
        descriptor = copy.deepcopy(self.descriptor)
        del descriptor["components"]["dome"]
        tree = self._tree(descriptor=descriptor)
        with self.assertRaisesRegex(ContractError, "one image per brief component"):
            evaluate_concept_brief(tree, wish=self.wish)


if __name__ == "__main__":
    unittest.main()
