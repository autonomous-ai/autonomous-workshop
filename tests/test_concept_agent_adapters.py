"""The three agent-backed Concept adapters, unit-tested and pipeline-tested.

No test here starts a real process or reaches the network. Unit tests use a
hand-written recording ``ModelDoor`` double, mirroring the ``RecordingTransport``
pattern the OpenRouter adapter tests already use. The pipeline-level tests use
the real ``AgentSessionDoor`` wired to ``tools/agent_door_fixture.py``'s
deterministic launcher, exactly as ``tests/test_concept_pipeline.py`` wires
the OpenRouter-shaped fixtures.
"""

import base64
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from inventor_workshop.agent_session import AgentRoleConfig, AgentSessionDoor
from inventor_workshop.concept import (
    ConceptImageRequest,
    DefaultConcept,
    WishResearchRequest,
)
from inventor_workshop.concept_agent_adapters import (
    AgentConceptArtist,
    AgentExplodeInspector,
    AgentWishResearcher,
    ENV_AGENT_DOOR_LAUNCH_COMMAND,
    ROLE_CONCEPT_IMAGES,
    ROLE_EXPLODED_VIEW_CHECK,
    ROLE_WISH_RESEARCH,
    concept_agent_session_door_from_env,
)
from inventor_workshop.errors import ConceptProviderError, ContractError
from inventor_workshop.jobs import CONCEPT_OVERALL_ROLES, ConceptBrief, ConceptComponent
from inventor_workshop.make import Wish
from inventor_workshop.runtime import Runtime
from inventor_workshop.taste import load_taste
from inventor_workshop.toys import ToyBlueprint
from inventor_workshop.workshop import Workshop, WorkshopTools
from tools.agent_door_fixture import FixtureAgentLauncher

PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8z8BQDwAEhQGA"
    "hKmMIQAAAABJRU5ErkJggg=="
)


class RecordingDoor:
    """A hand-written ``ModelDoor`` double: canned outcomes, recorded calls."""

    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def run(self, role, request, budget_micros):
        self.calls.append(
            {"role": role, "request": request, "budget_micros": budget_micros}
        )
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def _envelope(result):
    return {"result": result, "elapsed_seconds": 0.1, "spent_micros": 1}


def _brief() -> ConceptBrief:
    return ConceptBrief(
        "a toy",
        "little-worlds",
        (100.0, 80.0, 40.0),
        2.0,
        ("f1",),
        {"orientation": "flat", "supports": False},
        (
            ConceptComponent(
                "body", "Body", "purpose", "form", (10.0, 10.0, 10.0),
                "placement", "interfaces",
            ),
            ConceptComponent(
                "lid", "Lid", "purpose", "form", (10.0, 10.0, 10.0),
                "placement", "interfaces",
            ),
        ),
    )


_WISH_RESULT = {
    "object": "a spinning top",
    "category": "toys",
    "envelope_mm": [60.0, 60.0, 30.0],
    "wall_mm": 2.0,
    "features": ["a fluted waist"],
    "print": {"orientation": "flat on its largest face", "supports": False},
    "fits": None,
    "components": [
        {
            "key": "body",
            "name": "Body",
            "purpose": "purpose",
            "form": "form",
            "dimensions_mm": [10.0, 10.0, 10.0],
            "placement": "placement",
            "interfaces": "interfaces",
        }
    ],
    "findings": [
        {"claim": "It is a spinning top.", "field": "object", "decided_because": "reasoned from the wish"},
        {"claim": "It is a toy.", "field": "category", "decided_because": "reasoned from the wish"},
        {"claim": "Envelope is 60x60x30.", "field": "envelope_mm", "decided_because": "reasoned from the wish"},
        {"claim": "Wall is 2mm.", "field": "wall_mm", "decided_because": "reasoned from the wish"},
        {"claim": "It has a fluted waist.", "field": "features", "decided_because": "reasoned from the wish"},
        {"claim": "It prints flat.", "field": "print", "decided_because": "reasoned from the wish"},
        {"claim": "It has one body part.", "field": "components", "decided_because": "reasoned from the wish"},
    ],
    "sources": [],
}


class AgentWishResearcherUnitTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        inventor = Path(self.temporary.name) / "inventor"
        inventor.mkdir()
        (inventor / "TASTE.md").write_text(
            "---\nname: Test Inventor\ndescription: Architectural desk objects.\n---\n"
            "# Taste\n\nArchitectural desk objects.\n",
            encoding="utf-8",
        )
        self.wish = Wish.create("spinner", "A pocket spinning top")
        self.taste = load_taste(inventor)
        self.blueprint = ToyBlueprint.for_lane("moving-machines")
        self.request = WishResearchRequest(self.wish, self.taste, self.blueprint, 1)

    def test_construction_rejects_a_non_door_or_bad_budget(self):
        with self.assertRaises(ContractError):
            AgentWishResearcher(object(), 1_000)
        door = RecordingDoor([])
        with self.assertRaises(ContractError):
            AgentWishResearcher(door, 0)
        with self.assertRaises(ContractError):
            AgentWishResearcher(door, -5)

    def test_calls_the_door_with_the_wish_research_role(self):
        door = RecordingDoor([_envelope(_WISH_RESULT)])
        researcher = AgentWishResearcher(door, 5_000)
        researcher(self.request)
        self.assertEqual(door.calls[0]["role"], ROLE_WISH_RESEARCH)
        self.assertEqual(door.calls[0]["budget_micros"], 5_000)

    def test_well_formed_result_is_parsed_into_a_wish_research(self):
        door = RecordingDoor([_envelope(_WISH_RESULT)])
        researcher = AgentWishResearcher(door, 5_000)
        research = researcher(self.request)
        self.assertEqual(research.object, "a spinning top")
        self.assertEqual(research.components[0].key, "body")

    def test_missing_required_field_raises(self):
        result = dict(_WISH_RESULT)
        result["envelope_mm"] = []
        door = RecordingDoor([_envelope(result)])
        researcher = AgentWishResearcher(door, 5_000)
        with self.assertRaises(ConceptProviderError):
            researcher(self.request)

    def test_finding_with_neither_source_nor_decision_raises(self):
        result = dict(_WISH_RESULT)
        findings = [dict(item) for item in result["findings"]]
        findings[0] = {"claim": "It is a spinning top.", "field": "object"}
        result["findings"] = findings
        door = RecordingDoor([_envelope(result)])
        researcher = AgentWishResearcher(door, 5_000)
        with self.assertRaises(ConceptProviderError):
            researcher(self.request)

    def test_finding_citing_an_unknown_source_raises(self):
        result = dict(_WISH_RESULT)
        findings = [dict(item) for item in result["findings"]]
        findings[0] = {
            "claim": "It is a spinning top.",
            "field": "object",
            "sources": ["https://nowhere.example/never-returned"],
        }
        result["findings"] = findings
        door = RecordingDoor([_envelope(result)])
        researcher = AgentWishResearcher(door, 5_000)
        with self.assertRaises(ConceptProviderError):
            researcher(self.request)

    def test_finding_citing_a_reported_source_is_accepted(self):
        result = dict(_WISH_RESULT)
        result["sources"] = [
            {
                "origin": "https://example.com/spinning-tops",
                "title": "Spinning Tops",
                "excerpt": "Spinning tops are toys that spin on an axis.",
                "retrieved_at": "2026-08-20T00:00:00+00:00",
            }
        ]
        findings = [dict(item) for item in result["findings"]]
        findings[0] = {
            "claim": "It is a spinning top.",
            "field": "object",
            "sources": ["https://example.com/spinning-tops"],
        }
        result["findings"] = findings
        door = RecordingDoor([_envelope(result)])
        researcher = AgentWishResearcher(door, 5_000)
        research = researcher(self.request)
        self.assertEqual(len(research.sources), 1)
        self.assertEqual(research.findings[0].source_ids, ("s001",))

    def test_agent_door_returning_no_result_envelope_raises(self):
        door = RecordingDoor([{"not": "an envelope"}])
        researcher = AgentWishResearcher(door, 5_000)
        with self.assertRaises(ConceptProviderError):
            researcher(self.request)


class AgentConceptArtistUnitTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.workspace = Path(self.temporary.name)
        self.brief = _brief()

    def _request(self, references=()):
        return ConceptImageRequest(
            "front", "overall", "draw a toy", references, self.workspace,
            "images/front.png", self.brief, 1,
        )

    def test_construction_rejects_a_non_door_or_bad_budget(self):
        with self.assertRaises(ContractError):
            AgentConceptArtist(object(), 1_000)
        with self.assertRaises(ContractError):
            AgentConceptArtist(RecordingDoor([]), 0)

    def test_calls_the_door_with_the_concept_images_role(self):
        door = RecordingDoor(
            [_envelope({"image_base64": base64.b64encode(PNG_1X1).decode("ascii")})]
        )
        artist = AgentConceptArtist(door, 3_000)
        artist(self._request())
        self.assertEqual(door.calls[0]["role"], ROLE_CONCEPT_IMAGES)
        self.assertEqual(door.calls[0]["budget_micros"], 3_000)

    def test_one_request_produces_one_image_written_to_the_requested_path(self):
        door = RecordingDoor(
            [_envelope({"image_base64": base64.b64encode(PNG_1X1).decode("ascii")})]
        )
        artist = AgentConceptArtist(door, 3_000)
        filename = artist(self._request())
        self.assertEqual(filename, "images/front.png")
        self.assertEqual((self.workspace / filename).read_bytes(), PNG_1X1)

    def test_references_are_encoded_inline_not_by_path(self):
        (self.workspace / "ref.png").write_bytes(PNG_1X1)
        door = RecordingDoor(
            [_envelope({"image_base64": base64.b64encode(PNG_1X1).decode("ascii")})]
        )
        artist = AgentConceptArtist(door, 3_000)
        artist(self._request(references=(self.workspace / "ref.png",)))
        reference = door.calls[0]["request"]["references"][0]
        self.assertEqual(reference["media_type"], "image/png")
        self.assertEqual(base64.b64decode(reference["data_base64"]), PNG_1X1)

    def test_missing_image_in_result_raises(self):
        door = RecordingDoor([_envelope({})])
        artist = AgentConceptArtist(door, 3_000)
        with self.assertRaises(ConceptProviderError):
            artist(self._request())

    def test_malformed_base64_raises(self):
        door = RecordingDoor([_envelope({"image_base64": "not-base64!!"})])
        artist = AgentConceptArtist(door, 3_000)
        with self.assertRaises(ConceptProviderError):
            artist(self._request())


class AgentExplodeInspectorUnitTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.image = Path(self.temporary.name) / "exploded.png"
        self.image.write_bytes(PNG_1X1)
        self.brief = _brief()

    def test_construction_rejects_a_non_door_or_bad_budget(self):
        with self.assertRaises(ContractError):
            AgentExplodeInspector(object(), 1_000)
        with self.assertRaises(ContractError):
            AgentExplodeInspector(RecordingDoor([]), 0)

    def test_calls_the_door_with_the_exploded_view_check_role(self):
        door = RecordingDoor([_envelope({"components": ["body"]})])
        inspector = AgentExplodeInspector(door, 2_000)
        inspector(self.image, self.brief)
        self.assertEqual(door.calls[0]["role"], ROLE_EXPLODED_VIEW_CHECK)
        self.assertEqual(door.calls[0]["budget_micros"], 2_000)

    def test_offers_only_the_briefs_component_keys(self):
        door = RecordingDoor([_envelope({"components": ["body"]})])
        inspector = AgentExplodeInspector(door, 2_000)
        inspector(self.image, self.brief)
        offered = {item["key"] for item in door.calls[0]["request"]["components"]}
        self.assertEqual(offered, {"body", "lid"})

    def test_well_formed_subset_is_reported_exactly(self):
        door = RecordingDoor([_envelope({"components": ["body"]})])
        inspector = AgentExplodeInspector(door, 2_000)
        self.assertEqual(inspector(self.image, self.brief), ("body",))

    def test_unoffered_key_raises_rather_than_passing_through(self):
        door = RecordingDoor(
            [_envelope({"components": ["body", "not-a-real-component"]})]
        )
        inspector = AgentExplodeInspector(door, 2_000)
        with self.assertRaises(ConceptProviderError):
            inspector(self.image, self.brief)


class ConceptAgentSessionDoorFromEnvTest(unittest.TestCase):
    def test_requires_the_launch_command(self):
        with mock.patch.dict("os.environ", {}, clear=True), mock.patch(
            "inventor_workshop.concept_agent_adapters.load_dotenv"
        ):
            with self.assertRaises(ContractError):
                concept_agent_session_door_from_env()

    def test_requires_every_roles_variables(self):
        environment = {ENV_AGENT_DOOR_LAUNCH_COMMAND: "agent-cli --headless"}
        with mock.patch.dict("os.environ", environment, clear=True), mock.patch(
            "inventor_workshop.concept_agent_adapters.load_dotenv"
        ):
            with self.assertRaises(ContractError):
                concept_agent_session_door_from_env()

    def test_reads_the_documented_variables(self):
        environment = {
            ENV_AGENT_DOOR_LAUNCH_COMMAND: "agent-cli --headless --json",
            "AGENT_DOOR_WISH_RESEARCH_TOOLS": "web_search",
            "AGENT_DOOR_WISH_RESEARCH_ALLOWED_PATHS": "./",
            "AGENT_DOOR_WISH_RESEARCH_WALL_CLOCK_SECONDS": "120",
            "AGENT_DOOR_CONCEPT_IMAGES_TOOLS": "image_generation",
            "AGENT_DOOR_CONCEPT_IMAGES_ALLOWED_PATHS": "./",
            "AGENT_DOOR_CONCEPT_IMAGES_WALL_CLOCK_SECONDS": "180",
            "AGENT_DOOR_CONCEPT_IMAGES_MAX_BUDGET_MICROS": "500000",
            "AGENT_DOOR_EXPLODED_VIEW_CHECK_TOOLS": "vision",
            "AGENT_DOOR_EXPLODED_VIEW_CHECK_ALLOWED_PATHS": "./",
            "AGENT_DOOR_EXPLODED_VIEW_CHECK_WALL_CLOCK_SECONDS": "60",
        }
        with mock.patch.dict("os.environ", environment, clear=True), mock.patch(
            "inventor_workshop.concept_agent_adapters.load_dotenv"
        ) as loader:
            door = concept_agent_session_door_from_env(
                launcher=lambda *args: None
            )
        loader.assert_called_once()
        self.assertEqual(door._launch_command, ("agent-cli", "--headless", "--json"))
        self.assertEqual(
            door._role_configs[ROLE_WISH_RESEARCH].wall_clock_seconds, 120
        )
        self.assertEqual(
            door._role_configs[ROLE_CONCEPT_IMAGES].max_budget_micros, 500_000
        )
        self.assertIsNone(
            door._role_configs[ROLE_EXPLODED_VIEW_CHECK].max_budget_micros
        )


class ConceptAgentAdaptersPipelineTest(unittest.TestCase):
    """Fixture-driven, mirroring tests/test_concept_pipeline.py's cases."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.inventor = self.root / "inventor"
        self.inventor.mkdir()
        (self.inventor / "TASTE.md").write_text(
            "---\nname: Test Inventor\ndescription: Architectural desk objects.\n---\n"
            "# Taste\n\nArchitectural desk objects.\n",
            encoding="utf-8",
        )
        self.runtime = self.root / "runtime"

    def _door(self, **role_kwargs):
        config = AgentRoleConfig(
            tools=("web_search",), allowed_paths=("./",), wall_clock_seconds=30
        )
        return AgentSessionDoor(
            ["not-a-real-binary"],
            {
                ROLE_WISH_RESEARCH: config,
                ROLE_CONCEPT_IMAGES: config,
                ROLE_EXPLODED_VIEW_CHECK: config,
            },
            launcher=FixtureAgentLauncher(**role_kwargs),
            workspace_root=self.root / "agent-door-workspaces",
        )

    def concept_job(self, door):
        return DefaultConcept(
            AgentConceptArtist(door, 10_000),
            AgentExplodeInspector(door, 10_000),
            wish_researcher=AgentWishResearcher(door, 10_000),
        )

    def wish(self, product_id="rhythm-top"):
        return Wish.create(
            product_id,
            "A delightful desk spinner that reveals a changing beat",
            constraints={
                "envelope_mm": [60.0, 60.0, 30.0],
                "wall_mm": 2.0,
                "components": [
                    {
                        "key": "body",
                        "name": "Body",
                        "purpose": "Holds the mechanism.",
                        "form": "a rounded shell with one flat base",
                        "dimensions_mm": [60.0, 60.0, 18.0],
                        "placement": "the base of the assembly",
                        "interfaces": "receives the cap on its upper rim",
                    },
                    {
                        "key": "cap",
                        "name": "Cap",
                        "purpose": "Closes the body.",
                        "form": "a shallow dome with a knurled rim",
                        "dimensions_mm": [58.0, 58.0, 9.0],
                        "placement": "on top of the body",
                        "interfaces": "snaps onto the body rim",
                    },
                ],
            },
        )

    def make_job(self, context):
        artifact = context.workspace / "artifact"
        artifact.mkdir(parents=True)
        (artifact / "toy.step").write_text("round %d\n" % context.round, encoding="utf-8")
        from inventor_workshop.jobs import Made

        return Made.from_root(
            artifact,
            {
                "title": "Rhythm Top",
                "summary": "A pocket top that reveals a changing beat.",
                "lane": context.blueprint.lane,
                "instructions": "Spin, listen, repeat.",
                "components": [
                    item.name for item in context.concept_images.brief.components
                ],
                "limitations": ["Fixture evidence is not a physical print."],
            },
        )

    def passing_playtest(self, context):
        from inventor_workshop.artifacts import build_artifact_manifest
        from inventor_workshop.jobs import Playtested
        from inventor_workshop.models import PlaytestResult
        from inventor_workshop.playtest import Playtest
        import hashlib

        context.workspace.mkdir(parents=True)
        results = []
        for capability in context.blueprint.required_capabilities("playtest"):
            evidence_path = context.workspace / (capability + ".json")
            evidence_path.write_text('{"capability":"%s"}\n' % capability, encoding="utf-8")
            results.append(
                PlaytestResult.create(
                    capability,
                    True,
                    context.made.artifact_sha256,
                    {
                        "evidence_class": "ai-simulation",
                        "agent_roles": ["optimizing-player", "adversarial-breaker"],
                        "claims": ["Synthetic contract evidence."],
                    },
                    "workshop-contract-fixture",
                    "1.0.0",
                    "c" * 64,
                    evidence_path.name,
                    hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
                )
            )
        return Playtested(
            Playtest(
                context.made.artifact_manifest,
                tuple(results),
                evidence_manifest=build_artifact_manifest(
                    context.workspace, created_at="content-addressed"
                ),
            ),
            (),
        )

    # -- 2.6 --------------------------------------------------------------

    def test_default_concept_behaves_the_same_as_the_openrouter_shaped_fixtures(self):
        door = self._door()
        result = Workshop(
            self.inventor,
            "moving-machines",
            tools=WorkshopTools(
                concept=self.concept_job(door),
                make=self.make_job,
                playtest=self.passing_playtest,
            ),
            runtime_root=self.runtime,
        ).run(self.wish(), playtest_rounds=1)
        # Concept must have sealed a full design before Make ran at all.
        self.assertIn(result.status, ("delivered", "waiting"))
        self.assertNotEqual(result.job, "concept")
        self.assertIsNotNone(result.concept_sha256)
        state = Runtime(self.runtime / "workshop.sqlite3")
        self.assertTrue(state.verify_event_chain(self.wish().product_id))

    def test_concept_seals_the_researched_components_and_overall_views(self):
        door = self._door()
        seen = []

        def make(context):
            seen.append(context)
            return self.make_job(context)

        Workshop(
            self.inventor,
            "moving-machines",
            tools=WorkshopTools(
                concept=self.concept_job(door),
                make=make,
                playtest=self.passing_playtest,
            ),
            runtime_root=self.runtime,
        ).run(self.wish(), playtest_rounds=1)
        self.assertEqual(len(seen), 1)
        concept = seen[0].concept_images
        self.assertEqual(set(concept.overall), set(CONCEPT_OVERALL_ROLES))
        self.assertEqual(set(concept.components), {"body", "cap"})

    def test_no_concept_provider_parks_before_make_exactly_as_before(self):
        called = []

        def forbidden_make(context):
            called.append(context)
            raise AssertionError("Make ran without a decided design")

        result = Workshop(
            self.inventor,
            "moving-machines",
            tools=WorkshopTools(make=forbidden_make, playtest=self.passing_playtest),
            runtime_root=self.runtime,
        ).run(self.wish("undrawn"), playtest_rounds=1)
        self.assertEqual((result.status, result.job), ("waiting", "concept"))
        self.assertIn("concept-images", [need.capability for need in result.needs])
        self.assertEqual(called, [])

    # -- 2.7 --------------------------------------------------------------

    def test_workshop_still_parks_at_make_with_only_concept_wired(self):
        door = self._door()
        result = Workshop(
            self.inventor,
            "moving-machines",
            tools=WorkshopTools(concept=self.concept_job(door)),
            runtime_root=self.runtime,
        ).run(self.wish("boundary-check"), playtest_rounds=1)
        self.assertEqual(result.status, "waiting")
        self.assertEqual(result.job, "make")
        self.assertEqual(
            [need.capability for need in result.needs], ["model-and-cad-maker"]
        )


if __name__ == "__main__":
    unittest.main()
