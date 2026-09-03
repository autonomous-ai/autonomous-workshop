import copy
import unittest

from workshop.errors import ContractError
from workshop.invent.native import NativeInvented, validate_build_plan
from workshop.match.native import (
    MatchRankingEntry,
    NativeMatchAssignment,
    InventorRoster,
    InventorRosterEntry,
)
from workshop.product.blueprints import ToyBlueprint


def digest(character):
    return character * 64


def v4_concept():
    """One minimal concept that satisfies every schema-4 contract rule."""

    return {
        "title": "Moon Nook",
        "summary": "A tiny lunar observatory shaped by the Wish.",
        "interaction": (
            "Turn the dome by hand to sweep the telescope; the dome seats on the "
            "base ring and the lens cap parks in the base pocket."
        ),
        "envelope_mm": {"length_mm": 120.0, "width_mm": 120.0, "height_mm": 90.0},
        "mechanisms": ["rotating-dome"],
        "components": [
            {
                "key": "base",
                "name": "Base",
                "form": "120 mm round plinth with a raised 4 mm ring",
                "duty": "carries the dome and keeps it level",
                "dimensions_mm": {"length_mm": 120.0, "width_mm": 120.0, "height_mm": 20.0},
                "placement": "on the desk",
                "interfaces": "ring seats the dome with 0.4 mm clearance",
                "mates_with": ["dome"],
                "signature": False,
            },
            {
                "key": "dome",
                "name": "Dome",
                "form": "hemisphere with one telescope slot",
                "duty": "turns by hand to aim the telescope",
                "dimensions_mm": {"length_mm": 100.0, "width_mm": 100.0, "height_mm": 70.0},
                "placement": "on the base ring",
                "interfaces": "slides on the base ring",
                "mates_with": ["base"],
                "signature": True,
            },
            {
                "key": "lens_cap",
                "name": "Lens cap",
                "form": "12 mm disc with a lip",
                "duty": "covers the telescope between plays",
                "dimensions_mm": {"length_mm": 12.0, "width_mm": 12.0, "height_mm": 3.0},
                "placement": "in the base pocket",
                "interfaces": "press fit in the base pocket",
                "mates_with": [],
                "signature": False,
            },
        ],
    }


def v5_concept():
    """A schema-5 concept: the schema-4 contract plus a complete build plan."""

    concept = v4_concept()
    concept["build_plan"] = [
        {"group": "body", "parts": ["base", "dome"], "exit_criteria": "Dome turns freely on the base ring."},
        {"group": "cap", "parts": ["lens_cap"], "exit_criteria": "Cap press-fits the pocket."},
    ]
    return concept


def _plan(concept, value):
    concept["build_plan"] = value


BUILD_PLAN_VIOLATIONS = (
    ("plan-missing", lambda c: c.pop("build_plan"), "build_plan"),
    ("plan-not-list", lambda c: _plan(c, "body"), "build_plan"),
    ("plan-empty", lambda c: _plan(c, []), "build_plan"),
    ("plan-too-many", lambda c: _plan(c, [{"group": "g%d" % i, "parts": ["base"], "exit_criteria": "x"} for i in range(17)]), "exceeds 16 groups"),
    ("group-shape", lambda c: _plan(c, [{"group": "body"}]), "Invented build group"),
    ("group-bad-slug", lambda c: _plan(c, [{"group": "Body!", "parts": ["base", "dome", "lens_cap"], "exit_criteria": "x"}]), "unique slug"),
    ("group-duplicate", lambda c: _plan(c, [{"group": "a", "parts": ["base", "dome"], "exit_criteria": "x"}, {"group": "a", "parts": ["lens_cap"], "exit_criteria": "x"}]), "unique slug"),
    ("group-blank-criteria", lambda c: _plan(c, [{"group": "a", "parts": ["base", "dome", "lens_cap"], "exit_criteria": "  "}]), "exit_criteria"),
    ("group-empty-parts", lambda c: _plan(c, [{"group": "a", "parts": [], "exit_criteria": "x"}]), "parts"),
    ("unknown-part", lambda c: _plan(c, [{"group": "a", "parts": ["base", "dome", "lens_cap", "ghost"], "exit_criteria": "x"}]), "unknown component 'ghost' \\(build-plan\\)"),
    ("part-twice", lambda c: _plan(c, [{"group": "a", "parts": ["base", "dome"], "exit_criteria": "x"}, {"group": "b", "parts": ["dome", "lens_cap"], "exit_criteria": "x"}]), "more than one build group"),
    ("part-unplaced", lambda c: _plan(c, [{"group": "a", "parts": ["base", "dome"], "exit_criteria": "x"}]), "unplaced: lens_cap"),
)


def _component(concept, key):
    return next(item for item in concept["components"] if item["key"] == key)


def _drop(concept, field_name):
    del concept[field_name]


def _set(path, value):
    def apply(concept):
        target = concept
        for part in path[:-1]:
            target = _component(target, part) if isinstance(part, str) and part in (
                "base",
                "dome",
                "lens_cap",
            ) else target[part]
        target[path[-1]] = value

    return apply


def _extra_component_field(concept):
    _component(concept, "base")["colour"] = "red"


def _duplicate_key(concept):
    concept["components"].append(dict(_component(concept, "dome")))


def _too_many_components(concept):
    dome = _component(concept, "dome")
    for index in range(64):
        concept["components"].append({**dome, "key": "extra_%d" % index, "signature": False})


def _no_signature(concept):
    _component(concept, "dome")["signature"] = False


def _two_signatures(concept):
    _component(concept, "base")["signature"] = True


def _decoration(concept):
    concept["interaction"] = "Turn the dome by hand to sweep the telescope."


# (name, mutation, message pattern) — shared by the host and finalizer suites.
CONCEPT_VIOLATIONS = (
    ("missing-field", lambda c: _drop(c, "interaction"), "lacks required contract fields: interaction"),
    ("envelope-keys", _set(("envelope_mm",), {"length_mm": 1.0}), "exactly length_mm, width_mm, and height_mm"),
    ("envelope-zero", _set(("envelope_mm", "height_mm"), 0), "finite millimetre value"),
    ("envelope-bool", _set(("envelope_mm", "height_mm"), True), "finite millimetre value"),
    ("envelope-nan", _set(("envelope_mm", "height_mm"), float("nan")), "finite"),
    ("envelope-text", _set(("envelope_mm", "height_mm"), "90"), "finite millimetre value"),
    ("mechanisms-not-list", _set(("mechanisms",), "rotating-dome"), "mechanisms"),
    ("mechanisms-bad-slug", _set(("mechanisms",), ["Rotating Dome"]), "unique slugs"),
    ("mechanisms-duplicate", _set(("mechanisms",), ["a", "a"]), "unique slugs"),
    ("mechanisms-too-many", _set(("mechanisms",), ["m%d" % i for i in range(17)]), "unique slugs"),
    ("components-empty", _set(("components",), []), "components"),
    ("components-too-many", _too_many_components, "exceed 64 entries"),
    ("component-extra-field", _extra_component_field, "Invented component"),
    ("component-bad-key", _set(("base", "key"), "Base!"), "unique slug"),
    ("component-duplicate-key", _duplicate_key, "unique slug"),
    ("unbound-numeric", _set(("base", "form"), "roughly 120 mm plinth"), "unbound"),
    ("unbound-tilde", _set(("base", "interfaces"), "~4 mm ring"), "unbound"),
    ("unbound-quantity", _set(("base", "duty"), "holds several pegs"), "unbound"),
    ("envelope-exceeded", _set(("dome", "dimensions_mm", "height_mm"), 95.0), r"\(envelope\)"),
    ("signature-not-bool", _set(("dome", "signature"), "yes"), "signature must be boolean"),
    ("mates-not-list", _set(("dome", "mates_with"), "base"), "mates_with"),
    ("mates-unknown", _set(("dome", "mates_with"), ["ghost"]), "component-orphan"),
    ("mates-self", _set(("dome", "mates_with"), ["dome"]), "component-orphan"),
    ("mates-duplicate", _set(("dome", "mates_with"), ["base", "base"]), "component-orphan"),
    ("signature-none", _no_signature, r"found 0 \(signature\)"),
    ("signature-two", _two_signatures, r"found 2 \(signature\)"),
    ("decoration", _decoration, r"lens_cap is decoration"),
)


class InventedContractTest(unittest.TestCase):
    def setUp(self):
        inventor = InventorRosterEntry(
            inventor_id="bob",
            agent_path=".codex/agents/bob.toml",
            agent_sha256=digest("a"),
            source_manifest_sha256=digest("b"),
            taste_sha256=digest("0"),
        )
        self.roster = InventorRoster((inventor,))
        self.assignment = NativeMatchAssignment(
            wish_sha256=digest("c"),
            inventor_roster_sha256=self.roster.roster_sha256,
            selected_inventor_id=inventor.inventor_id,
            selected_agent_path=inventor.agent_path,
            selected_agent_sha256=inventor.agent_sha256,
            selected_source_manifest_sha256=inventor.source_manifest_sha256,
            selected_taste_sha256=inventor.taste_sha256,
            blueprint_sha256=ToyBlueprint().sha256,
            ranking=(
                MatchRankingEntry(
                    inventor.inventor_id,
                    "The only materialized inventor is also an exact mechanical fit.",
                ),
            ),
        )

    def invented(self, **overrides):
        values = {
            "wish_sha256": self.assignment.wish_sha256,
            "assignment_sha256": self.assignment.assignment_sha256,
            "taste_sha256": self.assignment.selected_taste_sha256,
            "blueprint_sha256": self.assignment.blueprint_sha256,
            "concept": {
                "title": "Moonstep Orrery",
                "summary": "A hand-wound walker turns the Wish into a visible lunar gait.",
                "signature_decision": "The phase offset is both mechanism and story.",
            },
            "research": {
                "sources": [
                    {
                        "url": "https://example.test/kinematics",
                        "claim": "A crank can translate rotary input into periodic motion.",
                    }
                ],
                "open_questions": ["Verify torque and pinch clearance during Make."],
            },
        }
        values.update(overrides)
        return NativeInvented(**values)

    def test_schema_4_concept_contract_round_trips(self):
        invented = self.invented(schema_version=4, concept=v4_concept())
        invented.assert_context(self.assignment)
        payload = invented.to_dict()
        self.assertEqual(payload["schema_version"], 4)
        self.assertEqual(NativeInvented.from_mapping(payload), invented)
        self.assertEqual(
            [item["key"] for item in payload["concept"]["components"]],
            ["base", "dome", "lens_cap"],
        )

    def test_schema_4_accepts_a_concept_without_mechanisms(self):
        concept = v4_concept()
        concept["mechanisms"] = []
        self.invented(schema_version=4, concept=concept)

    def test_schema_4_rejects_every_contract_violation(self):
        for name, mutate, pattern in CONCEPT_VIOLATIONS:
            concept = v4_concept()
            mutate(concept)
            with self.subTest(violation=name):
                with self.assertRaisesRegex(ContractError, pattern):
                    self.invented(schema_version=4, concept=concept)

    def test_schema_5_requires_a_complete_build_plan(self):
        invented = self.invented(schema_version=5, concept=v5_concept())
        self.assertEqual(NativeInvented.from_mapping(invented.to_dict()), invented)
        self.assertEqual(
            [group["group"] for group in validate_build_plan(v5_concept())], ["body", "cap"]
        )
        for name, mutate, pattern in BUILD_PLAN_VIOLATIONS:
            concept = v5_concept()
            mutate(concept)
            with self.subTest(violation=name):
                with self.assertRaisesRegex(ContractError, pattern):
                    self.invented(schema_version=5, concept=concept)
        # schema 4 tolerates a missing plan and ignores a present one
        self.invented(schema_version=4, concept=v4_concept())
        broken = v5_concept()
        broken["build_plan"] = "not checked at schema 4"
        self.invented(schema_version=4, concept=broken)

    def test_schema_3_stays_readable_for_sealed_runs(self):
        legacy = self.invented(schema_version=3)
        self.assertEqual(legacy.to_dict()["schema_version"], 3)
        self.assertEqual(NativeInvented.from_mapping(legacy.to_dict()), legacy)
        with self.assertRaisesRegex(ContractError, "schema_version must be 3, 4, or 5"):
            self.invented(schema_version=6)

    def test_round_trip_binds_every_input_and_content_hash(self):
        invented = self.invented()
        invented.assert_context(self.assignment)
        self.assertEqual(NativeInvented.from_mapping(invented.to_dict()), invented)
        payload = invented.to_dict()
        self.assertEqual(payload["schema_version"], 3)
        self.assertEqual(payload["concept_sha256"], invented.concept_sha256)
        self.assertEqual(payload["research_sha256"], invented.research_sha256)
        self.assertEqual(
            payload["research"]["sources"][0]["url"],
            "https://example.test/kinematics",
        )
        self.assertNotIn("lane", payload)
        self.assertNotIn("score", payload)
        self.assertNotIn("passed", payload)
        self.assertNotIn("target_score", payload)

    def test_rejects_model_gate_fields_and_stale_content_hashes(self):
        scored = self.invented().to_dict()
        scored["score"] = 100
        with self.assertRaisesRegex(ContractError, "fields"):
            NativeInvented.from_mapping(scored)

        stale = copy.deepcopy(self.invented().to_dict())
        stale["research"]["open_questions"].append("A new unbound question.")
        with self.assertRaisesRegex(ContractError, "hashes"):
            NativeInvented.from_mapping(stale)

    def test_rejects_another_assignment_and_legacy_lane_field(self):
        other = NativeMatchAssignment(
            wish_sha256=digest("d"),
            inventor_roster_sha256=self.roster.roster_sha256,
            selected_inventor_id="bob",
            selected_agent_path=".codex/agents/bob.toml",
            selected_agent_sha256=digest("a"),
            selected_source_manifest_sha256=digest("b"),
            selected_taste_sha256=digest("0"),
            blueprint_sha256=ToyBlueprint().sha256,
            ranking=(MatchRankingEntry("bob", "Exact fit."),),
        )
        with self.assertRaisesRegex(ContractError, "different Workshop inputs"):
            self.invented().assert_context(other)

        legacy = self.invented().to_dict()
        legacy["lane"] = "moving-machines"
        with self.assertRaisesRegex(ContractError, "fields"):
            NativeInvented.from_mapping(legacy)


if __name__ == "__main__":
    unittest.main()
