"""Simplified Invent authoring, adaptive-role, and normalization contracts."""

import copy
import hashlib
import json
import unittest

from workshop.concept import (
    VISUAL_PLAN_KIND,
    PreRenderConceptV3,
    SealedConceptV3,
    normalize_authored_concept,
    normalized_concept_view,
    validate_authored_source,
    validate_visual_plan,
)
from workshop.errors import ContractError
from workshop.invent.native import NativeInvented
from workshop.match.native import MatchRankingEntry, NativeMatchAssignment
from workshop.product import ToyBlueprint
from workshop.wish import Wish


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value):
    return hashlib.sha256(value if isinstance(value, bytes) else canonical(value)).hexdigest()


class SimplifiedConceptAuthoringTest(unittest.TestCase):
    def setUp(self):
        self.source = {
            "selected_inventor_id": "alice",
            "ranking": [{"inventor_id": "alice", "rationale": "Owns the transformation."}],
            "concept": {
                "title": "Turning Seed",
                "summary": "One held seed opens to show a second tactile state.",
                "object": "held transforming seed",
                "category": "tactile desk toy",
                "signature_interaction": "A thumb roll opens the shell and exposes a star core.",
                "anti_generic_signature": "The continuous seed seam becomes a five-point aperture.",
                "intended_experience": "A quiet form gives one crisp surprising reveal.",
                "non_negotiable_constraints": ["The core remains captive."],
                "envelope_mm": {"length": 72, "width": 48, "height": 45},
                "print_stance": {"orientation": "seam up", "supports_required": False, "support_notes": ""},
                "components": [{
                    "key": "shell", "name": "Shell", "purpose": "Forms both states",
                    "form": "Rounded seed split by a helical seam",
                    "measurements": {"description": "Held envelope", "values_mm": {"length": 72, "width": 48, "height": 45}},
                    "placement": "Around the captive core", "interfaces": "Helical tracks engage the core",
                    "assembly_relationship": "The two shell halves capture the core",
                    "signature_contribution": "Rotation changes the seam into the star aperture",
                }],
                "interaction_trace": [{"step": 1, "component_keys": ["shell"], "cause": "Thumb rotates the shell", "effect": "The aperture opens"}],
                "make_proof_target": {"claim": "The seam produces two distinct states", "method": "Generate and render both exact end states", "success_condition": "Closed seed and open star are distinct", "failure_condition": "The opening reads as a camera change"},
                "constraints": [{"id": "held-envelope", "description": "Held size", "value": "72 x 48 x 45 mm", "basis": {"kind": "decision", "id": "held-size"}}],
                "decisions": [{"id": "held-size", "decision": "Use a 72 mm long envelope", "reason": "It leaves room for a deliberate one-hand roll."}],
                "assumptions": [], "unresolved_risks": ["Track friction remains Make work"],
            },
            "research": {"sources": [], "findings": []},
        }
        self.plan = {
            "schema_version": 2, "kind": VISUAL_PLAN_KIND,
            "presentation": "Warm neutral studio light, matte mineral palette, consistent scale.",
            "roles": [
                {"id": "held-form", "kind": "primary-form", "purpose": "Establishes the rounded held seed volume", "instruction": "Show the closed seed held between thumb and forefinger.", "appearance_references": [], "subject_components": ["shell"]},
                {"id": "star-reveal", "kind": "signature-experience", "purpose": "Shows the causal closed-to-open star transformation", "instruction": "Show closed, thumb action, and open aperture states at one scale.", "appearance_references": ["held-form"], "subject_components": ["shell"]},
            ],
        }
        self.wish = Wish.create("turning-seed", "A held seed that opens into a star")
        self.wish_sha = digest(self.wish.to_dict())
        blueprint = ToyBlueprint()
        self.assignment = NativeMatchAssignment(
            wish_sha256=self.wish_sha, inventor_roster_sha256="1" * 64,
            selected_inventor_id="alice", selected_agent_path=".codex/agents/alice.toml",
            selected_agent_sha256="2" * 64, selected_source_manifest_sha256="3" * 64,
            selected_taste_sha256="4" * 64, blueprint_sha256=blueprint.sha256,
            ranking=(MatchRankingEntry("alice", "Owns the transformation."),),
        )
        self.invented = NativeInvented(
            wish_sha256=self.wish_sha, assignment_sha256=self.assignment.assignment_sha256,
            taste_sha256=self.assignment.selected_taste_sha256,
            blueprint_sha256=self.assignment.blueprint_sha256,
            concept=self.source["concept"], research=self.source["research"],
        )

    def normalize(self, source=None, plan=None):
        source = self.source if source is None else source
        plan = self.plan if plan is None else plan
        return normalize_authored_concept(
            source, plan, source_path="work/invent-source.json", source_bytes=canonical(source),
            visual_plan_path="work/visual-plan.json", visual_plan_bytes=canonical(plan),
            wish=self.wish, wish_sha256=self.wish_sha, assignment=self.assignment,
            invented=self.invented, round=1,
        )

    def test_minimal_two_inputs_normalize_deterministically(self):
        first = self.normalize()
        second = self.normalize()
        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(list(first.descriptor), ["held-form", "star-reveal"])
        self.assertEqual(first.descriptor["star-reveal"]["path"], "images/star-reveal.png")
        self.assertEqual(PreRenderConceptV3.from_mapping(first.to_dict()), first)
        self.assertNotIn("excerpt_sha256", self.source["research"])
        self.assertNotIn("descriptor", self.plan)

    def test_research_may_be_jointly_empty_but_attribution_cannot_be_fabricated(self):
        validate_authored_source(self.source)
        changed = copy.deepcopy(self.source)
        changed["research"]["findings"] = [{"id": "fit", "finding": "Fits", "source_ids": ["missing"]}]
        with self.assertRaisesRegex(ContractError, "jointly empty"):
            validate_authored_source(changed)
        changed["research"]["sources"] = [{"id": "source", "origin": "https://example.test", "excerpt": "Bounded support", "retrieved_at": "2026-09-01T00:00:00Z"}]
        with self.assertRaisesRegex(ContractError, "fabricated"):
            validate_authored_source(changed)

    def test_constraint_requires_supported_finding_or_reasoned_decision(self):
        changed = copy.deepcopy(self.source)
        changed["concept"]["constraints"][0]["basis"]["id"] = "missing"
        with self.assertRaisesRegex(ContractError, "reasoned decision"):
            validate_authored_source(changed)

    def test_adaptive_role_boundaries_and_dependencies(self):
        validate_visual_plan(self.plan, component_keys=["shell"])
        twenty = copy.deepcopy(self.plan)
        for index in range(2, 20):
            twenty["roles"].append({"id": "detail-%d" % index, "kind": "alternate-view", "purpose": "Communicates unique hidden interface number %d" % index, "instruction": "Show unique interface number %d." % index, "appearance_references": ["held-form"], "subject_components": ["shell"]})
        self.assertEqual(len(validate_visual_plan(twenty, component_keys=["shell"])["roles"]), 20)
        over = copy.deepcopy(twenty)
        over["roles"].append({**over["roles"][-1], "id": "detail-20", "purpose": "Communicates unique hidden interface number 20"})
        with self.assertRaisesRegex(ContractError, "2 through 20"):
            validate_visual_plan(over, component_keys=["shell"])
        for mutation, pattern in (
            ((1, "appearance_references", ["future"]), "earlier"),
            ((1, "subject_components", ["unknown"]), "unknown"),
            ((1, "id", "held-form"), "unique"),
            ((1, "purpose", "same"), "distinct useful"),
        ):
            changed = copy.deepcopy(self.plan)
            changed["roles"][mutation[0]][mutation[1]] = mutation[2]
            with self.subTest(pattern=pattern), self.assertRaisesRegex(ContractError, pattern):
                validate_visual_plan(changed, component_keys=["shell"])
        for removed_kind in ("primary-form", "signature-experience"):
            changed = copy.deepcopy(self.plan)
            changed["roles"] = [role for role in changed["roles"] if role["kind"] != removed_kind]
            if len(changed["roles"]) < 2:
                changed["roles"].append({**self.plan["roles"][0], "id": "extra-form", "kind": "alternate-view", "purpose": "Communicates another distinct hidden interface"})
            with self.subTest(removed_kind=removed_kind), self.assertRaises(ContractError):
                validate_visual_plan(changed, component_keys=["shell"])

    def test_sealed_contract_requires_exact_declared_role_set(self):
        source = self.normalize()
        images = tuple({"id": role_id, **source.descriptor[role_id], "sha256": str(index + 1) * 64} for index, role_id in enumerate(source.descriptor))
        sealed = SealedConceptV3(source=source, images=images)
        self.assertEqual(SealedConceptV3.from_mapping(sealed.to_dict()), sealed)
        view = normalized_concept_view(sealed.to_dict())
        self.assertEqual(view.component_keys, ("shell",))
        self.assertEqual([role["id"] for role in view.visual_roles], ["held-form", "star-reveal"])
        with self.assertRaisesRegex(ContractError, "role order"):
            SealedConceptV3(source=source, images=images[:-1])


if __name__ == "__main__":
    unittest.main()
