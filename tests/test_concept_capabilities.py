"""The wiring entry point that assembles Concept's three capabilities.

Construction never reaches the network or a subprocess: every adapter's own
``from_env`` only validates environment presence, so these tests exercise
that path directly, setting or omitting the environment each capability
requires. No launcher, transport, or override seam is needed to keep this
offline -- none of the three adapters does any I/O at construction time.
"""

import unittest
from unittest import mock

from inventor_workshop.concept import DefaultConcept
from inventor_workshop.concept_agent_adapters import AgentWishResearcher
from inventor_workshop.concept_artist_openrouter import OpenRouterConceptArtist
from inventor_workshop.concept_capabilities import (
    ENV_CONCEPT_WISH_RESEARCH_BUDGET_MICROS,
    concept_capabilities_from_env,
)
from inventor_workshop.concept_explode_inspector import OpenAICompatibleExplodeInspector
from inventor_workshop.errors import ContractError

_FULL_ENVIRONMENT = {
    "OPENROUTER_API_KEY": "or-key",
    "CONCEPT_EXPLODE_INSPECTOR_BASE_URL": "https://inspect.example/v1",
    "CONCEPT_EXPLODE_INSPECTOR_API_KEY": "inspect-key",
    "CONCEPT_EXPLODE_INSPECTOR_MODEL": "inspect-model",
    "AGENT_DOOR_LAUNCH_COMMAND": "agent-cli --headless",
    "AGENT_DOOR_WISH_RESEARCH_TOOLS": "web_search",
    "AGENT_DOOR_WISH_RESEARCH_ALLOWED_PATHS": "./",
    "AGENT_DOOR_WISH_RESEARCH_WALL_CLOCK_SECONDS": "120",
    ENV_CONCEPT_WISH_RESEARCH_BUDGET_MICROS: "1000000",
}

# Not a real path -- keeps a stray .env in the working directory from
# leaking into these tests without needing to mock load_dotenv everywhere.
_NO_SUCH_DOTENV = "/nonexistent/concept-capabilities-test.env"


class ConceptCapabilitiesFromEnvTest(unittest.TestCase):
    def test_a_full_environment_wires_the_expected_adapter_per_capability(self):
        with mock.patch.dict("os.environ", _FULL_ENVIRONMENT, clear=True):
            concept = concept_capabilities_from_env(dotenv_path=_NO_SUCH_DOTENV)
        self.assertIsInstance(concept, DefaultConcept)
        self.assertIsInstance(concept.concept_artist, OpenRouterConceptArtist)
        self.assertIsInstance(
            concept.explode_inspector, OpenAICompatibleExplodeInspector
        )
        self.assertIsNone(concept.brief_maker)
        self.assertIsInstance(concept.wish_researcher, AgentWishResearcher)

    def test_missing_concept_images_configuration_names_that_capability(self):
        environment = dict(_FULL_ENVIRONMENT)
        del environment["OPENROUTER_API_KEY"]
        with mock.patch.dict("os.environ", environment, clear=True), mock.patch(
            "inventor_workshop.concept_capabilities."
            "OpenAICompatibleExplodeInspector.from_env"
        ) as inspector_from_env, mock.patch(
            "inventor_workshop.concept_capabilities."
            "concept_agent_session_door_from_env"
        ) as door_from_env:
            with self.assertRaisesRegex(ContractError, "concept-images"):
                concept_capabilities_from_env(dotenv_path=_NO_SUCH_DOTENV)
        inspector_from_env.assert_not_called()
        door_from_env.assert_not_called()

    def test_missing_exploded_view_check_configuration_names_that_capability(self):
        environment = dict(_FULL_ENVIRONMENT)
        del environment["CONCEPT_EXPLODE_INSPECTOR_MODEL"]
        with mock.patch.dict("os.environ", environment, clear=True), mock.patch(
            "inventor_workshop.concept_capabilities."
            "concept_agent_session_door_from_env"
        ) as door_from_env:
            with self.assertRaisesRegex(ContractError, "exploded-view-check"):
                concept_capabilities_from_env(dotenv_path=_NO_SUCH_DOTENV)
        door_from_env.assert_not_called()

    def test_missing_wish_research_configuration_names_that_capability(self):
        environment = dict(_FULL_ENVIRONMENT)
        del environment["AGENT_DOOR_LAUNCH_COMMAND"]
        with mock.patch.dict("os.environ", environment, clear=True):
            with self.assertRaisesRegex(ContractError, "wish-research"):
                concept_capabilities_from_env(dotenv_path=_NO_SUCH_DOTENV)

    def test_missing_wish_research_budget_names_that_capability(self):
        environment = dict(_FULL_ENVIRONMENT)
        del environment[ENV_CONCEPT_WISH_RESEARCH_BUDGET_MICROS]
        with mock.patch.dict("os.environ", environment, clear=True):
            with self.assertRaisesRegex(ContractError, "wish-research"):
                concept_capabilities_from_env(dotenv_path=_NO_SUCH_DOTENV)


if __name__ == "__main__":
    unittest.main()
