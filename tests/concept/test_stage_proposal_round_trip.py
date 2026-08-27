"""Round-trip guard: the finalizer and concept/native.py must never drift."""

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from workshop.concept.native import NativeConcept, seal_rendered_concept
from workshop.concept.native_gate import evaluate_concept_brief
from workshop.errors import ArtifactError
from workshop.invent.native import NativeInvented
from workshop.match.native import (
    InventorRoster,
    InventorRosterEntry,
    MatchRankingEntry,
    NativeMatchAssignment,
)
from workshop.product import ToyBlueprint
from workshop.wish import Wish
from workshop.workflow.proposals import AgentOutcomeProposal


REPOSITORY = Path(__file__).resolve().parents[2]
TOOL = (
    REPOSITORY
    / ".agents"
    / "product-run"
    / ".agents"
    / "skills"
    / "autonomous-workshop"
    / "scripts"
    / "stage_proposal.py"
)


def canonical_json(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sha256(content):
    return hashlib.sha256(content).hexdigest()


FAKE = "0" * 64


class ConceptStageProposalRoundTripTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.run_root = Path(self.temporary.name).resolve()
        self.blueprint = ToyBlueprint()
        self.wish = Wish.create(
            "run-local-toy",
            "a lamp shaped like a moon",
            context={"acceptance_mode": "exact-wish-binding"},
        )
        self.wish_bytes = canonical_json(self.wish.to_dict())
        (self.run_root / "WISH.json").write_bytes(self.wish_bytes)
        eve = InventorRosterEntry(
            "eve", ".codex/agents/eve.toml", "a" * 64, "1" * 64, "b" * 64
        )
        self.roster = InventorRoster((eve,))
        self.assignment = NativeMatchAssignment(
            wish_sha256=sha256(self.wish_bytes),
            inventor_roster_sha256=self.roster.roster_sha256,
            selected_inventor_id="eve",
            selected_agent_path=eve.agent_path,
            selected_agent_sha256=eve.agent_sha256,
            selected_source_manifest_sha256=eve.source_manifest_sha256,
            selected_taste_sha256=eve.taste_sha256,
            blueprint_sha256=self.blueprint.sha256,
            ranking=(
                MatchRankingEntry("eve", "The Wish asks for a tiny lunar object."),
            ),
        )
        self.invented = NativeInvented(
            wish_sha256=self.assignment.wish_sha256,
            assignment_sha256=self.assignment.assignment_sha256,
            taste_sha256=self.assignment.selected_taste_sha256,
            blueprint_sha256=self.assignment.blueprint_sha256,
            concept={"title": "Moon Nook", "summary": "A tiny lunar observatory."},
            research={
                "sources": [
                    {
                        "url": "https://example.test/moon",
                        "claim": "The visible phases follow relative geometry.",
                    }
                ]
            },
        )

    def write_json(self, relative, value):
        path = self.run_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(canonical_json(value))
        return path

    def write_stage(self, subject):
        document = {
            "schema_version": 1,
            "kind": "autonomous-workshop.stage-input",
            "product_id": "run-local-toy",
            "stage": "concept",
            "checkpoint_sha256": "1" * 64,
            "subject_sha256": subject,
            "next_transition": "make",
            "round": 1,
            "max_rounds": 4,
            "inputs": {
                "wish": {
                    "path": "WISH.json",
                    "sha256": sha256(self.wish_bytes),
                },
                "assignment": self.assignment.to_dict(),
                "invented": self.invented.to_dict(),
            },
        }
        path = self.run_root / "STAGE.json"
        path.write_bytes(canonical_json(document))
        path.chmod(0o400)
        return document

    def build_concept_tree(self):
        concept_root = self.run_root / "artifacts/concept/r0001/concept"
        concept_root.mkdir(parents=True)

        brief = {
            "object": "moon lamp",
            "category": "lighting",
            "envelope_mm": {"length_mm": 120.0, "width_mm": 120.0, "height_mm": 150.0},
            "wall_thickness_mm": 2.4,
            "print_stance": {
                "orientation": "vertical, dome up",
                "supports_required": False,
                "support_notes": "self-supporting dome geometry avoids overhangs",
            },
            "features": [
                {
                    "id": "cratered_surface",
                    "text": "cratered lunar surface texture across the dome",
                }
            ],
            "fit_target": None,
            "components": [
                {
                    "key": "dome",
                    "name": "Dome",
                    "purpose": "diffuses light and shows the lunar texture",
                    "form": "hollow hemisphere with textured exterior",
                    "dimensions_mm": {
                        "length_mm": 120.0,
                        "width_mm": 120.0,
                        "height_mm": 100.0,
                    },
                    "placement": "sits atop the base, centered",
                    "interfaces": "snap-fits onto the base's rim lip",
                },
                {
                    "key": "base",
                    "name": "Base",
                    "purpose": "houses the light source and stabilizes the lamp",
                    "form": "cylindrical disc with a rim lip",
                    "dimensions_mm": {
                        "length_mm": 120.0,
                        "width_mm": 120.0,
                        "height_mm": 50.0,
                    },
                    "placement": "sits on the work surface, below the dome",
                    "interfaces": "rim lip receives the dome's snap-fit",
                },
            ],
            "facts": [
                {
                    "field": "object",
                    "source_id": None,
                    "assumption_reason": "decided a moon-themed lamp fits the wish",
                },
                {
                    "field": "category",
                    "source_id": None,
                    "assumption_reason": "lighting is the natural category",
                },
                {"field": "envelope_mm", "source_id": "s1", "assumption_reason": None},
                {
                    "field": "wall_thickness_mm",
                    "source_id": "s2",
                    "assumption_reason": None,
                },
                {
                    "field": "print_stance",
                    "source_id": None,
                    "assumption_reason": "dome-up orientation avoids supports",
                },
                {
                    "field": "features.cratered_surface",
                    "source_id": "s1",
                    "assumption_reason": None,
                },
                {
                    "field": "components.dome",
                    "source_id": None,
                    "assumption_reason": "two-part design allows access to the bulb",
                },
                {
                    "field": "components.base",
                    "source_id": None,
                    "assumption_reason": "two-part design allows access to the bulb",
                },
            ],
        }
        research = {
            "sources": [
                {
                    "id": "s1",
                    "origin": "https://example.com/moon-lamp-dims",
                    "excerpt": "typical moon lamps range 100-150mm",
                    "excerpt_sha256": sha256(b"typical moon lamps range 100-150mm"),
                    "retrieved_at": "2026-08-26T00:00:00+00:00",
                },
                {
                    "id": "s2",
                    "origin": "https://example.com/fdm-wall-thickness",
                    "excerpt": "2-3mm walls are standard for FDM shades",
                    "excerpt_sha256": sha256(b"2-3mm walls are standard for FDM shades"),
                    "retrieved_at": "2026-08-26T00:00:00+00:00",
                },
            ],
            "findings": [
                {"finding": "moon lamps are commonly 100-150mm domes", "source_ids": ["s1"]},
                {"finding": "2-3mm walls are standard", "source_ids": ["s2"]},
            ],
        }
        drawing_instructions = {
            "front": {
                "instruction": "A moon-textured dome lamp on a cylindrical base, "
                "front view, neutral flat design-study presentation.",
                "references": [],
            },
            "top": {
                "instruction": "Same object as the reference, unchanged, from above.",
                "references": ["front"],
            },
            "bottom": {
                "instruction": "Same object as the reference, unchanged, from below.",
                "references": ["front"],
            },
            "exploded": {
                "instruction": "Show the Dome and the Base fully separated, each "
                "wholly visible, none hidden.",
                "references": ["front", "top", "bottom"],
            },
            "components": {
                "dome": {
                    "instruction": "The Dome alone: hollow hemisphere, cratered "
                    "texture, matching the reference's material and finish.",
                    "references": ["front"],
                },
                "base": {
                    "instruction": "The Base alone: cylindrical disc with rim lip, "
                    "matching the reference's material and finish.",
                    "references": ["front"],
                },
            },
        }
        descriptor = {
            "front": {"path": "images/front.png"},
            "top": {"path": "images/top.png"},
            "bottom": {"path": "images/bottom.png"},
            "exploded": {"path": "images/exploded.png"},
            "components": {
                "dome": {"path": "images/components/dome.png"},
                "base": {"path": "images/components/base.png"},
            },
        }
        derived_wish = {
            "schema_version": 1,
            "kind": "autonomous-workshop.concept-derived-wish",
            "wish_sha256": self.assignment.wish_sha256,
            "product_id": "run-local-toy",
            "objective": "a lamp shaped like a moon",
            "context": {"acceptance_mode": "exact-wish-binding"},
            "constraints": {
                "envelope_mm": brief["envelope_mm"],
                "wall_thickness_mm": brief["wall_thickness_mm"],
            },
        }
        derived_identity = {
            key: value for key, value in derived_wish.items()
        }
        derived_wish["derived_wish_sha256"] = sha256(canonical_json(derived_identity))

        self.write_json(concept_root / "brief.json", brief)
        self.write_json(concept_root / "research.json", research)
        self.write_json(concept_root / "prompts.json", drawing_instructions)
        self.write_json(concept_root / "descriptor.json", descriptor)
        self.write_json(concept_root / "derived_wish.json", derived_wish)
        return concept_root

    def run_tool(self, *arguments, expected=0):
        completed = subprocess.run(
            [sys.executable, "-I", "-B", str(TOOL), "--run-root", str(self.run_root), *arguments],
            cwd=self.run_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(
            completed.returncode,
            expected,
            "stdout:\n%s\nstderr:\n%s" % (completed.stdout, completed.stderr),
        )
        return completed

    def test_finalizer_and_native_agree_on_concept_identity(self):
        self.build_concept_tree()
        # The finalizer only checks that subject_sha256 is well-formed; the
        # host gate is what verifies it is the correctly derived value. This
        # test exercises contract-construction agreement, not gate binding.
        self.write_stage(FAKE)

        self.run_tool(
            "concept", "--concept-root", "artifacts/concept/r0001/concept"
        )

        contract_path = self.run_root / "artifacts/concept/r0001/concept.json"
        contract_bytes = contract_path.read_bytes()
        contract_document = json.loads(contract_bytes.decode("utf-8"))
        self.assertEqual(contract_bytes, canonical_json(contract_document))

        from_finalizer = NativeConcept.from_mapping(contract_document)
        self.assertFalse(from_finalizer.images_rendered)
        tree = from_finalizer.validate_concept_tree(self.run_root)
        self.assertEqual(tree.brief["object"], "moon lamp")
        self.assertFalse((tree.root / "images").exists())
        checks = evaluate_concept_brief(
            tree,
            wish=Wish.create("run-local-toy", "a lamp shaped like a moon"),
        )
        self.assertEqual(checks["object"], "moon lamp")

        for entry in (
            tree.descriptor["front"],
            tree.descriptor["top"],
            tree.descriptor["bottom"],
            tree.descriptor["exploded"],
            tree.descriptor["components"]["dome"],
            tree.descriptor["components"]["base"],
        ):
            image = tree.root / entry["path"]
            image.parent.mkdir(parents=True, exist_ok=True)
            image.write_bytes((entry["path"] + " pixels").encode("utf-8"))
        sealed = seal_rendered_concept(from_finalizer, self.run_root)
        self.assertTrue(sealed.images_rendered)
        sealed.validate_concept_tree(self.run_root)
        self.assertNotEqual(sealed.concept_sha256, from_finalizer.concept_sha256)

        recovered = from_finalizer.validate_concept_tree(self.run_root)
        self.assertEqual(recovered.descriptor, tree.descriptor)
        resealed = seal_rendered_concept(from_finalizer, self.run_root)
        self.assertEqual(resealed.to_dict(), sealed.to_dict())
        (tree.root / tree.descriptor["front"]["path"]).write_bytes(b"tampered")
        with self.assertRaisesRegex(ArtifactError, "partially sealed image changed"):
            from_finalizer.validate_concept_tree(self.run_root)

        outcome_document = json.loads(
            (self.run_root / "agent-outcome.json").read_bytes().decode("utf-8")
        )
        proposal = AgentOutcomeProposal.from_mapping(outcome_document)
        self.assertEqual(proposal.outcome.stage, "concept")
        self.assertEqual(proposal.outcome.proposed_transition, "make")
        self.assertEqual(
            proposal.outcome.artifacts[0].path,
            "artifacts/concept/r0001/concept.json",
        )
        self.assertEqual(
            proposal.outcome.artifacts[0].sha256, sha256(contract_bytes)
        )

    def test_finalizer_rejects_brief_the_host_gate_would_reject(self):
        concept_root = self.build_concept_tree()
        brief_path = concept_root / "brief.json"
        brief = json.loads(brief_path.read_bytes().decode("utf-8"))
        del brief["object"]
        brief_path.write_bytes(canonical_json(brief))
        self.write_stage(FAKE)

        completed = self.run_tool(
            "concept",
            "--concept-root",
            "artifacts/concept/r0001/concept",
            expected=2,
        )

        self.assertIn("Concept brief is missing its object", completed.stderr)
        self.assertFalse(
            (self.run_root / "artifacts/concept/r0001/concept.json").exists()
        )
        self.assertFalse((self.run_root / "agent-outcome.json").exists())

    def test_finalizer_rejects_derived_wish_that_rewrites_routed_wish(self):
        concept_root = self.build_concept_tree()
        derived_path = concept_root / "derived_wish.json"
        derived = json.loads(derived_path.read_bytes().decode("utf-8"))
        derived["objective"] = "a rewritten objective"
        identity = dict(derived)
        identity.pop("derived_wish_sha256")
        derived["derived_wish_sha256"] = sha256(canonical_json(identity))
        derived_path.write_bytes(canonical_json(derived))
        self.write_stage(FAKE)

        completed = self.run_tool(
            "concept",
            "--concept-root",
            "artifacts/concept/r0001/concept",
            expected=2,
        )

        self.assertIn("changed the routed Wish's own words", completed.stderr)
        self.assertFalse((self.run_root / "agent-outcome.json").exists())


if __name__ == "__main__":
    unittest.main()
