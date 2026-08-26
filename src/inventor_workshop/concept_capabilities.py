"""The one committed entry point that wires Concept's three capabilities.

``concept-images`` and ``exploded-view-check`` are satisfied by their
existing HTTP adapters (``OpenRouterConceptArtist``,
``OpenAICompatibleExplodeInspector``); ``wish-research`` is satisfied by the
agent-door adapter (``AgentWishResearcher``), the one implementation this
capability is settled on. Every real Concept run needs this exact mix, and
nothing before this module has assembled it as a reusable, committed unit --
every prior run hand-constructed it in a one-off script.

Construction fails closed: each of the three steps is attempted in order,
and any missing configuration is reported by capability name
(``concept-images``, ``exploded-view-check``, ``wish-research``) rather than
by the underlying adapter's own class name, before any of the three is
exercised over the network or a subprocess.
"""

from __future__ import annotations

import os
from typing import Optional

from .concept import DefaultConcept
from .concept_agent_adapters import AgentWishResearcher, concept_agent_session_door_from_env
from .concept_artist_openrouter import OpenRouterConceptArtist
from .concept_explode_inspector import OpenAICompatibleExplodeInspector
from .env import load_dotenv
from .errors import ContractError

ENV_CONCEPT_WISH_RESEARCH_BUDGET_MICROS = "CONCEPT_WISH_RESEARCH_BUDGET_MICROS"


def concept_capabilities_from_env(
    *, dotenv_path: Optional[str] = None
) -> DefaultConcept:
    """Build a fully-configured Concept capability from the environment.

    Wires ``concept-images`` to :meth:`OpenRouterConceptArtist.from_env`,
    ``exploded-view-check`` to
    :meth:`OpenAICompatibleExplodeInspector.from_env`, and ``wish-research``
    to :class:`AgentWishResearcher`, built on the shared agent door from
    :func:`concept_agent_session_door_from_env` and a budget read from
    ``CONCEPT_WISH_RESEARCH_BUDGET_MICROS`` (required). If any step's
    configuration is missing, construction fails, naming that capability,
    before any other step runs.
    """

    load_dotenv(dotenv_path)

    try:
        concept_artist = OpenRouterConceptArtist.from_env(dotenv_path=dotenv_path)
    except ContractError as exc:
        raise ContractError(
            "concept_capabilities_from_env: concept-images is not configured: %s"
            % exc
        ) from exc

    try:
        explode_inspector = OpenAICompatibleExplodeInspector.from_env(
            dotenv_path=dotenv_path
        )
    except ContractError as exc:
        raise ContractError(
            "concept_capabilities_from_env: exploded-view-check is not "
            "configured: %s" % exc
        ) from exc

    try:
        door = concept_agent_session_door_from_env(dotenv_path=dotenv_path)
        budget = os.environ.get(ENV_CONCEPT_WISH_RESEARCH_BUDGET_MICROS, "")
        if not budget.strip():
            raise ContractError(
                "concept_capabilities_from_env requires %s to be set"
                % ENV_CONCEPT_WISH_RESEARCH_BUDGET_MICROS
            )
        try:
            budget_micros = int(budget)
        except ValueError as exc:
            raise ContractError(
                "%s must be an integer" % ENV_CONCEPT_WISH_RESEARCH_BUDGET_MICROS
            ) from exc
        wish_researcher = AgentWishResearcher(door, budget_micros)
    except ContractError as exc:
        raise ContractError(
            "concept_capabilities_from_env: wish-research is not configured: %s"
            % exc
        ) from exc

    return DefaultConcept(concept_artist, explode_inspector, None, wish_researcher)


__all__ = [
    "ENV_CONCEPT_WISH_RESEARCH_BUDGET_MICROS",
    "concept_capabilities_from_env",
]
