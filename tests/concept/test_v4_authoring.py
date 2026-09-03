import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from workshop.concept import (
    FIXED_OVERALL_ROLES,
    FIXED_PROMPT_PROTOCOL_VERSION,
    FIXED_VIEW_INSTRUCTIONS_KIND,
    MAX_FIXED_COMPONENTS,
    PreRenderConceptV4,
    SealedConceptV4,
    derive_fixed_roles,
    normalize_fixed_view_concept,
    normalized_concept_view,
    seal_pre_render_concept_v4,
    validate_fixed_view_instructions,
    validate_sealed_concept_v4_tree,
)
from workshop.errors import ContractError
from workshop.invent.native import NativeInvented
from workshop.integrations.concept_images import ConceptImageRequest
from workshop.match.native import MatchRankingEntry, NativeMatchAssignment
from workshop.product import ToyBlueprint
from workshop.wish import Wish
from workshop.workflow.native_run import _concept_role_plan


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value):
    return hashlib.sha256(value if isinstance(value, bytes) else canonical(value)).hexdigest()


def component(key):
    return {
        "key": key,
        "name": key.title(),
        "purpose": "Provides the %s function" % key,
        "form": "A crisp bounded %s volume" % key,
        "measurements": {"description": "%s envelope" % key, "values_mm": {"length": 40, "width": 30, "height": 20}},
        "placement": "Placed in the complete assembly",
        "interfaces": "Keyed mating face and capture ledge",
        "assembly_relationship": "Slides into the neighboring component",
        "signature_contribution": "Supports the visible transformation",
    }


class FixedConceptAuthoringTest(unittest.TestCase):
    def setUp(self):
        self.source = {
            "selected_inventor_id": "alice",
            "ranking": [{"inventor_id": "alice", "rationale": "Owns the transformation."}],
            "concept": {
                "title": "Turning Seed",
                "summary": "A held seed opens to reveal a tactile core.",
                "object": "held transforming seed",
                "category": "tactile desk toy",
                "signature_interaction": "A thumb roll opens the shell and exposes the core.",
                "anti_generic_signature": "The continuous seed seam becomes a five-point aperture.",
                "intended_experience": "A quiet form gives one crisp surprising reveal.",
                "non_negotiable_constraints": ["The core remains captive."],
                "envelope_mm": {"length": 72, "width": 48, "height": 45},
                "print_stance": {"orientation": "seam up", "supports_required": False, "support_notes": ""},
                "components": [component("shell"), component("core")],
                "interaction_trace": [{"step": 1, "component_keys": ["shell", "core"], "cause": "Thumb rotates the shell", "effect": "The aperture opens"}],
                "make_proof_target": {"claim": "The seam produces two states", "method": "Render both end states", "success_condition": "States are distinct", "failure_condition": "Only the camera changes"},
                "constraints": [{"id": "held-envelope", "description": "Held size", "value": "72 x 48 x 45 mm", "basis": {"kind": "decision", "id": "held-size"}}],
                "decisions": [{"id": "held-size", "decision": "Use a 72 mm envelope", "reason": "Supports a one-hand roll"}],
                "assumptions": [],
                "unresolved_risks": ["Track friction remains Make work"],
            },
            "research": {"sources": [], "findings": []},
        }
        self.instructions = {
            "schema_version": 3,
            "kind": FIXED_VIEW_INSTRUCTIONS_KIND,
            "appearance": "Matte warm-white shell with a muted blue core and crisp boundaries.",
            "views": {
                "front": "Expose the defining front seam.",
                "top": "Expose the top aperture.",
                "bottom": "Expose the flat underside.",
                "exploded": "Separate shell and core; show every mating face.",
            },
            "components": {
                "shell": "Show the complete shell with its capture ledge.",
                "core": "Show the complete core with its keyed interface.",
            },
        }
        self.wish = Wish.create("turning-seed", "A held seed that opens into a star")
        self.wish_sha = digest(self.wish.to_dict())
        blueprint = ToyBlueprint()
        self.assignment = NativeMatchAssignment(
            wish_sha256=self.wish_sha,
            inventor_roster_sha256="1" * 64,
            selected_inventor_id="alice",
            selected_agent_path=".codex/agents/alice.toml",
            selected_agent_sha256="2" * 64,
            selected_source_manifest_sha256="3" * 64,
            selected_taste_sha256="4" * 64,
            blueprint_sha256=blueprint.sha256,
            ranking=(MatchRankingEntry("alice", "Owns the transformation."),),
        )
        self.invented = NativeInvented(
            wish_sha256=self.wish_sha,
            assignment_sha256=self.assignment.assignment_sha256,
            taste_sha256=self.assignment.selected_taste_sha256,
            blueprint_sha256=self.assignment.blueprint_sha256,
            concept=self.source["concept"],
            research=self.source["research"],
        )

    def normalize(self, source=None, instructions=None):
        source = self.source if source is None else source
        instructions = self.instructions if instructions is None else instructions
        return normalize_fixed_view_concept(
            source,
            instructions,
            source_path="artifacts/invent/source.json",
            source_bytes=canonical(source),
            visual_instructions_path="artifacts/invent/visual-instructions.json",
            visual_instructions_bytes=canonical(instructions),
            wish=self.wish,
            wish_sha256=self.wish_sha,
            assignment=self.assignment,
            invented=self.invented,
            round=1,
        )

    def test_fixed_input_and_roles_normalize_deterministically(self):
        first = self.normalize()
        second = self.normalize()
        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(PreRenderConceptV4.from_mapping(first.to_dict()), first)
        expected = [*FIXED_OVERALL_ROLES, "component:shell", "component:core"]
        self.assertEqual([item["id"] for item in first.drawing_instructions], expected)
        self.assertEqual(first.descriptor["component:core"]["path"], "images/components/core.png")
        self.assertEqual(first.drawing_instructions[0]["prompt_protocol_version"], FIXED_PROMPT_PROTOCOL_VERSION)

    def test_fixed_reference_graph_and_prompt_context(self):
        roles = _concept_role_plan(self.normalize())
        self.assertEqual([item[0] for item in roles], ["front", "top", "bottom", "exploded", "component:shell", "component:core"])
        self.assertEqual(roles[0][3], ())
        self.assertEqual(roles[1][3], ("front",))
        self.assertEqual(roles[2][3], ("front",))
        self.assertEqual(roles[3][3], ("front", "top", "bottom"))
        self.assertEqual(roles[4][3], ("exploded",))
        self.assertEqual(roles[4][4]["normalized_facts"]["interfaces"], self.source["concept"]["components"][0]["interfaces"])
        prompt = roles[1][1]
        for clause in ("SAME complete product", "directly from above", "No perspective drama", "no text"):
            self.assertIn(clause.casefold(), prompt.casefold())
        request = ConceptImageRequest(
            role=roles[1][0], instruction=roles[1][1], output_path=roles[1][2],
            idempotency_key="request-1", context=roles[1][4],
        )
        provider_prompt = request.provider_prompt
        self.assertIn(self.instructions["appearance"], provider_prompt)
        self.assertIn(self.instructions["views"]["top"], provider_prompt)
        self.assertIn('"length":72', provider_prompt)
        self.assertIn(FIXED_PROMPT_PROTOCOL_VERSION, provider_prompt)

    def test_authored_or_protocol_input_changes_pre_render_identity(self):
        original = self.normalize()
        changed = copy.deepcopy(self.instructions)
        changed["views"]["front"] = "Expose the defining front seam and aperture."
        self.assertNotEqual(original.concept_sha256, self.normalize(instructions=changed).concept_sha256)
        changed = copy.deepcopy(self.instructions)
        changed["appearance"] = "Matte charcoal shell with a muted blue core."
        self.assertNotEqual(original.concept_sha256, self.normalize(instructions=changed).concept_sha256)

    def test_typed_contract_rejects_adaptive_undeclared_and_colliding_roles(self):
        original = self.normalize().to_dict()
        mutations = []
        changed = copy.deepcopy(original)
        changed["drawing_instructions"][0]["kind"] = "primary-form"
        mutations.append(changed)
        changed = copy.deepcopy(original)
        changed["descriptor"]["top"]["path"] = "images/front.png"
        mutations.append(changed)
        changed = copy.deepcopy(original)
        changed["descriptor"]["undeclared"] = copy.deepcopy(changed["descriptor"]["front"])
        mutations.append(changed)
        for value in mutations:
            with self.assertRaisesRegex(ContractError, "fixed"):
                PreRenderConceptV4.from_mapping(value)
        image_bytes = {
            item["id"]: item["id"].encode()
            for item in self.normalize().drawing_instructions
        }
        sealed = seal_pre_render_concept_v4(self.normalize(), image_bytes).to_dict()
        sealed["images"][0], sealed["images"][1] = sealed["images"][1], sealed["images"][0]
        with self.assertRaisesRegex(ContractError, "fixed role order"):
            SealedConceptV4.from_mapping(sealed)

    def test_input_is_exact_and_rejects_adaptive_or_incomplete_forms(self):
        validate_fixed_view_instructions(self.instructions, component_keys=["shell", "core"])
        mutations = []
        changed = copy.deepcopy(self.instructions)
        changed["views"]["side"] = "Show side."
        mutations.append((changed, "fields"))
        changed = copy.deepcopy(self.instructions)
        del changed["views"]["bottom"]
        mutations.append((changed, "fields"))
        changed = copy.deepcopy(self.instructions)
        del changed["components"]["core"]
        mutations.append((changed, "exactly match source components"))
        changed = copy.deepcopy(self.instructions)
        changed["components"]["extra"] = "Show extra."
        mutations.append((changed, "exactly match source components"))
        changed = copy.deepcopy(self.instructions)
        changed["components"]["shell"] = ""
        mutations.append((changed, "bounded, non-empty text"))
        changed = copy.deepcopy(self.instructions)
        changed["views"]["exploded"] = "Separate shell only."
        mutations.append((changed, "name every component"))
        changed = {"schema_version": 2, "kind": "autonomous-workshop.concept-visual-plan", "presentation": "plain", "roles": []}
        mutations.append((changed, "fields"))
        for value, pattern in mutations:
            with self.subTest(pattern=pattern), self.assertRaisesRegex(ContractError, pattern):
                validate_fixed_view_instructions(value, component_keys=["shell", "core"])
        with self.assertRaisesRegex(ContractError, "safe component key"):
            validate_fixed_view_instructions(
                self.instructions, component_keys=["../shell", "core"]
            )

    def test_component_boundaries_are_fixed_before_effects(self):
        sixteen = ["part-%d" % index for index in range(MAX_FIXED_COMPONENTS)]
        value = copy.deepcopy(self.instructions)
        value["views"]["exploded"] = "Separate " + ", ".join(sixteen)
        value["components"] = {key: "Show complete %s." % key for key in sixteen}
        validated = validate_fixed_view_instructions(value, component_keys=sixteen)
        concept = copy.deepcopy(self.source["concept"])
        concept["components"] = [component(key) for key in sixteen]
        self.assertEqual(len(derive_fixed_roles(concept, validated)), 20)
        seventeen = [*sixteen, "part-16"]
        value["components"]["part-16"] = "Show complete part-16."
        value["views"]["exploded"] += ", part-16"
        with self.assertRaisesRegex(ContractError, "1 through 16"):
            validate_fixed_view_instructions(value, component_keys=seventeen)

    def test_sealing_and_tree_validation_require_exact_fixed_set(self):
        source = self.normalize()
        image_bytes = {item["id"]: (item["id"] + " image").encode() for item in source.drawing_instructions}
        sealed = seal_pre_render_concept_v4(source, image_bytes)
        self.assertEqual(SealedConceptV4.from_mapping(sealed.to_dict()), sealed)
        view = normalized_concept_view(sealed.to_dict())
        self.assertEqual(view.schema_version, 4)
        self.assertEqual(tuple(view.component_visuals), ("shell", "core"))
        with self.assertRaisesRegex(ContractError, "fixed role order"):
            seal_pre_render_concept_v4(source, dict(list(image_bytes.items())[:-1]))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for role_id, descriptor in source.descriptor.items():
                path = root / descriptor["path"]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(image_bytes[role_id])
            validate_sealed_concept_v4_tree(sealed, root)
            (root / "images" / "extra.png").write_bytes(b"extra")
            with self.assertRaisesRegex(ContractError, "unexpected"):
                validate_sealed_concept_v4_tree(sealed, root)
            (root / "images" / "extra.png").unlink()
            front = root / source.descriptor["front"]["path"]
            front.write_bytes(b"changed")
            with self.assertRaisesRegex(ContractError, "differs"):
                validate_sealed_concept_v4_tree(sealed, root)
            front.write_bytes(image_bytes["front"])
            component_path = root / source.descriptor["component:core"]["path"]
            component_path.unlink()
            with self.assertRaisesRegex(ContractError, "incomplete"):
                validate_sealed_concept_v4_tree(sealed, root)
            component_path.symlink_to(front)
            with self.assertRaisesRegex(ContractError, "unsafe"):
                validate_sealed_concept_v4_tree(sealed, root)


if __name__ == "__main__":
    unittest.main()
