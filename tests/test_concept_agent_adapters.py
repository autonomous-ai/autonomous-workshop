"""The agent-backed Concept wish-research adapter, unit-tested.

No test here starts a real process or reaches the network. Tests use a
hand-written recording ``ModelDoor`` double, mirroring the
``RecordingTransport`` pattern the OpenRouter adapter tests already use.
"""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from inventor_workshop.concept import WishResearchRequest
from inventor_workshop.concept_agent_adapters import (
    AgentWishResearcher,
    ENV_AGENT_DOOR_LAUNCH_COMMAND,
    RESEARCH_INSTRUCTIONS,
    ROLE_WISH_RESEARCH,
    concept_agent_session_door_from_env,
)
from inventor_workshop.errors import ConceptProviderError, ContractError
from inventor_workshop.make import Wish
from inventor_workshop.taste import load_taste
from inventor_workshop.toys import ToyBlueprint


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

    def test_the_door_request_carries_the_research_instructions(self):
        door = RecordingDoor([_envelope(_WISH_RESULT)])
        researcher = AgentWishResearcher(door, 5_000)
        researcher(self.request)
        self.assertEqual(
            door.calls[0]["request"]["instructions"], RESEARCH_INSTRUCTIONS
        )

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

    def test_an_underspecified_component_fails(self):
        result = dict(_WISH_RESULT)
        components = [dict(item) for item in result["components"]]
        del components[0]["interfaces"]
        result["components"] = components
        door = RecordingDoor([_envelope(result)])
        researcher = AgentWishResearcher(door, 5_000)
        with self.assertRaisesRegex(ConceptProviderError, "states no interfaces"):
            researcher(self.request)

    def test_a_finding_with_both_a_source_and_a_decision_fails(self):
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
            "decided_because": "reasoned from the wish",
            "sources": ["https://example.com/spinning-tops"],
        }
        result["findings"] = findings
        door = RecordingDoor([_envelope(result)])
        researcher = AgentWishResearcher(door, 5_000)
        with self.assertRaisesRegex(ConceptProviderError, "is unusable"):
            researcher(self.request)


class ConceptAgentSessionDoorFromEnvTest(unittest.TestCase):
    def test_requires_the_launch_command(self):
        with mock.patch.dict("os.environ", {}, clear=True), mock.patch(
            "inventor_workshop.concept_agent_adapters.load_dotenv"
        ):
            with self.assertRaises(ContractError):
                concept_agent_session_door_from_env()

    def test_requires_the_wish_research_roles_variables(self):
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
            "AGENT_DOOR_WISH_RESEARCH_MAX_BUDGET_MICROS": "500000",
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
            door._role_configs[ROLE_WISH_RESEARCH].max_budget_micros, 500_000
        )

    def test_building_the_door_requires_no_image_or_inspection_configuration(self):
        environment = {
            ENV_AGENT_DOOR_LAUNCH_COMMAND: "agent-cli --headless --json",
            "AGENT_DOOR_WISH_RESEARCH_TOOLS": "web_search",
            "AGENT_DOOR_WISH_RESEARCH_ALLOWED_PATHS": "./",
            "AGENT_DOOR_WISH_RESEARCH_WALL_CLOCK_SECONDS": "120",
        }
        with mock.patch.dict("os.environ", environment, clear=True), mock.patch(
            "inventor_workshop.concept_agent_adapters.load_dotenv"
        ):
            door = concept_agent_session_door_from_env(
                launcher=lambda *args: None
            )
        self.assertEqual(set(door._role_configs), {ROLE_WISH_RESEARCH})


if __name__ == "__main__":
    unittest.main()
