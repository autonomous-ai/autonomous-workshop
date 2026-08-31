"""Route-aware dormant Concept contract and exact-byte failure paths."""

import copy
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

from workshop.concept import (
    ConceptExpectedContext,
    ConceptProvenance,
    PreRenderConcept,
    SealedConcept,
    evaluate_concept_brief,
    load_pre_render_concept,
    seal_pre_render_concept,
)
from workshop.errors import ArtifactError, ContractError
from workshop.invent.native import NativeInvented
from workshop.match.native import MatchRankingEntry, NativeMatchAssignment
from workshop.product import ToyBlueprint
from workshop.wish import Wish


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def digest(value):
    return hashlib.sha256(value if isinstance(value, bytes) else canonical(value)).hexdigest()


class DormantConceptV2Test(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.run_root = Path(temporary.name).resolve()
        self.wish = Wish.create(
            "moon-lamp", "a tactile moon lamp", context={"audience": "adult"}
        )
        self.wish_sha256 = digest(self.wish.to_dict())
        blueprint = ToyBlueprint()
        self.assignment = NativeMatchAssignment(
            wish_sha256=self.wish_sha256,
            inventor_roster_sha256="1" * 64,
            selected_inventor_id="eve",
            selected_agent_path=".codex/agents/eve.toml",
            selected_agent_sha256="2" * 64,
            selected_source_manifest_sha256="3" * 64,
            selected_taste_sha256="4" * 64,
            blueprint_sha256=blueprint.sha256,
            ranking=(MatchRankingEntry("eve", "Owns the physical lighting problem."),),
        )
        self.invented = NativeInvented(
            wish_sha256=self.wish_sha256,
            assignment_sha256=self.assignment.assignment_sha256,
            taste_sha256=self.assignment.selected_taste_sha256,
            blueprint_sha256=self.assignment.blueprint_sha256,
            concept={"title": "Moon Nook", "summary": "A tactile cratered moon lamp."},
            research={"basis": "Bound source research."},
        )
        self.source = {
            "selected_inventor_id": "eve",
            "ranking": [item.to_dict() for item in self.assignment.ranking],
            "concept": self.invented.to_dict()["concept"],
            "research": self.invented.to_dict()["research"],
        }

    def write_json(self, relative, value):
        path = self.run_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(canonical(value))
        return path

    def source_documents(self, round_index=1):
        brief = {
            "object": "moon lamp",
            "category": "lighting",
            "envelope_mm": {"length_mm": 120, "width_mm": 120, "height_mm": 150},
            "wall_thickness_mm": 2.4,
            "print_stance": {
                "orientation": "dome up",
                "supports_required": False,
                "support_notes": "self supporting",
            },
            "features": [{"id": "craters", "text": "tactile crater relief"}],
            "fit_target": {
                "target": "LED puck",
                "dimensions_mm": {"length_mm": 50, "width_mm": 50, "height_mm": 15},
                "clearance_mm": 0.4,
            },
            "components": [
                {
                    "key": "dome",
                    "name": "Dome",
                    "purpose": "diffuses light",
                    "form": "hollow hemisphere",
                    "dimensions_mm": {"length_mm": 120, "width_mm": 120, "height_mm": 100},
                    "placement": "above the base",
                    "interfaces": "twist-lock rim",
                }
            ],
            "facts": [],
        }
        required = (
            "object", "category", "envelope_mm", "wall_thickness_mm", "print_stance",
            "fit_target", "features.craters", "components.dome",
        )
        brief["facts"] = [
            {"field": field, "source_id": "s1", "assumption_reason": None}
            for field in required
        ]
        excerpt = "A bounded physical reference."
        research = {
            "sources": [
                {
                    "id": "s1",
                    "origin": "https://example.test/reference",
                    "excerpt": excerpt,
                    "excerpt_sha256": digest(excerpt),
                    "retrieved_at": "2026-08-30T00:00:00+00:00",
                }
            ],
            "findings": [{"finding": "The reference bounds the envelope.", "source_ids": ["s1"]}],
        }
        prompts = {
            "presentation": "Neutral warm-gray studio treatment with consistent scale.",
            "front": {"instruction": "Front view with crater relief.", "references": []},
            "top": {"instruction": "Top view of the same dome.", "references": ["front"]},
            "bottom": {"instruction": "Bottom interface view.", "references": ["front"]},
            "exploded": {
                "instruction": "Show the Dome separated from its light source.",
                "references": ["front", "top", "bottom"],
            },
            "components": {
                "dome": {"instruction": "Dome alone with matching finish.", "references": ["front"]}
            },
        }
        descriptor = {
            "front": {"path": "images/front.png"},
            "top": {"path": "images/top.png"},
            "bottom": {"path": "images/bottom.png"},
            "exploded": {"path": "images/exploded.png"},
            "components": {"dome": {"path": "images/components/dome.png"}},
        }
        derived = {
            "schema_version": 1,
            "kind": "autonomous-workshop.concept-derived-wish",
            "wish_sha256": self.wish_sha256,
            "product_id": self.wish.product_id,
            "objective": self.wish.objective,
            "context": dict(self.wish.context),
            "constraints": {"envelope_mm": brief["envelope_mm"]},
        }
        derived["derived_wish_sha256"] = digest(derived)
        root = Path("artifacts/concept/r%04d/concept" % round_index)
        for name, value in (
            ("brief.json", brief),
            ("research.json", research),
            ("prompts.json", prompts),
            ("descriptor.json", descriptor),
            ("derived_wish.json", derived),
        ):
            self.write_json(root / name, value)
        return root, descriptor

    def provenance(self, origin="invent", round_index=1, **overrides):
        source_path = (
            "artifacts/invent/source.json"
            if origin == "invent"
            else "artifacts/make/r0001/creative-source.json"
        )
        source_bytes = canonical(self.source)
        self.write_json(source_path, self.source)
        values = {
            "origin": origin,
            "wish_sha256": self.wish_sha256,
            "product_id": self.wish.product_id,
            "objective": self.wish.objective,
            "context": dict(self.wish.context),
            "assignment_sha256": self.assignment.assignment_sha256,
            "taste_sha256": self.assignment.selected_taste_sha256,
            "blueprint_sha256": self.assignment.blueprint_sha256,
            "invented_sha256": self.invented.invented_sha256,
            "creative_source_path": source_path,
            "creative_source_sha256": digest(source_bytes),
            "round": round_index,
            "standing_concept_sha256": None if round_index == 1 else "5" * 64,
            "revision_input_sha256": None if round_index == 1 else "6" * 64,
        }
        values.update(overrides)
        return ConceptProvenance(**values)

    def expected(self, provenance):
        return ConceptExpectedContext(
            origin=provenance.origin,
            wish=self.wish,
            wish_sha256=self.wish_sha256,
            assignment=self.assignment,
            invented=self.invented,
            creative_source_path=provenance.creative_source_path,
            creative_source_sha256=provenance.creative_source_sha256,
            round=provenance.round,
            standing_concept_sha256=provenance.standing_concept_sha256,
            revision_input_sha256=provenance.revision_input_sha256,
        )

    def test_both_origins_bind_exact_source_and_upstream_contracts(self):
        for origin in ("invent", "spark-make"):
            with self.subTest(origin=origin):
                self.source_documents()
                provenance = self.provenance(origin)
                concept = load_pre_render_concept(self.run_root, provenance)
                concept.assert_context(self.expected(provenance), self.run_root)
                self.assertEqual(
                    PreRenderConcept.from_mapping(concept.to_dict(), root=concept.root).to_dict(),
                    concept.to_dict(),
                )
                evidence = evaluate_concept_brief(concept, wish=self.wish)
                self.assertEqual(evidence["checks_kind"], "concept-structure-v1")

    def test_each_substituted_provenance_field_fails_by_name(self):
        self.source_documents()
        base = self.provenance()
        substitutions = {
            "origin": "spark-make",
            "wish_sha256": "a" * 64,
            "product_id": "other",
            "objective": "other objective",
            "context": {"other": True},
            "assignment_sha256": "a" * 64,
            "taste_sha256": "a" * 64,
            "blueprint_sha256": "a" * 64,
            "invented_sha256": "a" * 64,
            "creative_source_path": "other/source.json",
            "creative_source_sha256": "a" * 64,
        }
        values = base._identity_dict()
        values.pop("schema_version")
        values.pop("kind")
        for field, replacement in substitutions.items():
            with self.subTest(field=field):
                changed = ConceptProvenance(**{**values, field: replacement})
                with self.assertRaisesRegex((ContractError, ArtifactError), field.replace("_", "[-_ ]")):
                    self.expected(base).assert_provenance(changed, self.run_root)

    def test_round_and_revision_freshness_fail_closed(self):
        with self.assertRaisesRegex(ContractError, "revision inputs"):
            self.provenance(round_index=1, standing_concept_sha256="5" * 64)
        with self.assertRaisesRegex(ContractError, "requires standing Concept"):
            self.provenance(
                round_index=2,
                standing_concept_sha256=None,
                revision_input_sha256=None,
            )
        self.source_documents(round_index=2)
        provenance = self.provenance(round_index=2)
        stale = ConceptExpectedContext(
            **{**self.expected(provenance).__dict__, "round": 3}
        )
        with self.assertRaisesRegex(ContractError, "round"):
            stale.assert_provenance(provenance, self.run_root)

    def test_sealing_is_no_write_stable_and_detects_drift(self):
        root, descriptor = self.source_documents()
        provenance = self.provenance()
        source = load_pre_render_concept(self.run_root, provenance)
        descriptor_path = self.run_root / root / "descriptor.json"
        before = descriptor_path.read_bytes()
        for entry in (
            descriptor["front"], descriptor["top"], descriptor["bottom"],
            descriptor["exploded"], descriptor["components"]["dome"],
        ):
            image = self.run_root / root / entry["path"]
            image.parent.mkdir(parents=True, exist_ok=True)
            image.write_bytes((entry["path"] + " bytes").encode())
        sealed = seal_pre_render_concept(source)
        self.assertIsInstance(sealed, SealedConcept)
        self.assertEqual(descriptor_path.read_bytes(), before)
        self.assertEqual(seal_pre_render_concept(source).to_dict(), sealed.to_dict())
        self.assertEqual(
            SealedConcept.from_mapping(sealed.to_dict(), root=source.root).to_dict(),
            sealed.to_dict(),
        )
        sealed.validate_tree()
        (self.run_root / root / descriptor["front"]["path"]).write_bytes(b"drift")
        with self.assertRaisesRegex(ArtifactError, "sealed Concept tree"):
            sealed.validate_tree()

    def test_rendered_images_have_a_separate_bounded_size_budget(self):
        root, descriptor = self.source_documents()
        source = load_pre_render_concept(self.run_root, self.provenance())
        entries = (
            descriptor["front"], descriptor["top"], descriptor["bottom"],
            descriptor["exploded"], descriptor["components"]["dome"],
        )
        for index, entry in enumerate(entries):
            image = self.run_root / root / entry["path"]
            image.parent.mkdir(parents=True, exist_ok=True)
            image.write_bytes(
                b"image" if index else b"x" * (2 * 1024 * 1024 + 1)
            )
        sealed = seal_pre_render_concept(source)
        self.assertGreater(
            next(
                item.bytes
                for item in sealed.image_manifest.entries
                if item.path == descriptor["front"]["path"]
            ),
            2 * 1024 * 1024,
        )

    def test_incomplete_mixed_duplicate_and_unsafe_descriptors_are_rejected(self):
        root, descriptor = self.source_documents()
        cases = []
        missing = copy.deepcopy(descriptor)
        missing.pop("top")
        cases.append((missing, "roles"))
        duplicate = copy.deepcopy(descriptor)
        duplicate["top"]["path"] = duplicate["front"]["path"]
        cases.append((duplicate, "distinct"))
        mixed = copy.deepcopy(descriptor)
        mixed["front"]["sha256"] = "0" * 64
        cases.append((mixed, "leaf fields"))
        unsafe = copy.deepcopy(descriptor)
        unsafe["front"]["path"] = "../front.png"
        cases.append((unsafe, "safe relative"))
        for value, message in cases:
            with self.subTest(message=message):
                self.write_json(root / "descriptor.json", value)
                with self.assertRaisesRegex(ContractError, message):
                    load_pre_render_concept(self.run_root, self.provenance())

    def test_source_parser_rejects_duplicate_keys_nonfinite_and_links(self):
        root, _ = self.source_documents()
        brief = self.run_root / root / "brief.json"
        brief.write_bytes(b'{"object":"one","object":"two"}')
        with self.assertRaisesRegex(ContractError, "strict finite"):
            load_pre_render_concept(self.run_root, self.provenance())
        brief.write_bytes(b'{"value":NaN}')
        with self.assertRaisesRegex(ContractError, "strict finite"):
            load_pre_render_concept(self.run_root, self.provenance())
        brief.unlink()
        brief.symlink_to(self.run_root / root / "research.json")
        with self.assertRaisesRegex(ArtifactError, "regular file"):
            load_pre_render_concept(self.run_root, self.provenance())

    def test_source_parser_rejects_over_limit_and_special_nodes(self):
        root, _ = self.source_documents()
        brief = self.run_root / root / "brief.json"
        brief.write_bytes(b"{" + b" " * (2 * 1024 * 1024) + b"}")
        with self.assertRaisesRegex(ArtifactError, "byte limit"):
            load_pre_render_concept(self.run_root, self.provenance())
        brief.unlink()
        os.mkfifo(brief)
        with self.assertRaisesRegex(ArtifactError, "regular file"):
            load_pre_render_concept(self.run_root, self.provenance())

    def test_required_brief_rules_reject_missing_nonpositive_and_placeholders(self):
        root, _ = self.source_documents()
        brief_path = self.run_root / root / "brief.json"
        original = json.loads(brief_path.read_bytes())
        cases = []
        for field in ("object", "category", "envelope_mm", "wall_thickness_mm", "print_stance", "features", "fit_target", "components"):
            changed = copy.deepcopy(original)
            changed.pop(field)
            cases.append((field.rstrip("s"), changed))
        changed = copy.deepcopy(original)
        changed["wall_thickness_mm"] = 0
        cases.append(("positive", changed))
        changed = copy.deepcopy(original)
        changed["components"][0]["dimensions_mm"]["height_mm"] = -1
        cases.append(("positive", changed))
        changed = copy.deepcopy(original)
        changed["features"][0]["text"] = "TBD"
        cases.append(("placeholder", changed))
        for message, brief in cases:
            with self.subTest(message=message):
                brief_path.write_bytes(canonical(brief))
                with self.assertRaisesRegex(ContractError, message):
                    concept = load_pre_render_concept(self.run_root, self.provenance())
                    evaluate_concept_brief(concept, wish=self.wish)


if __name__ == "__main__":
    unittest.main()
