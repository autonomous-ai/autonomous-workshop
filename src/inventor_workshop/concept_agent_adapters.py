"""Concept's wish-research port, satisfied by dispatching through a shared agent door.

``concept.py`` already owns the prompts, the generation order, and the
sealing; ``concept_artist_openrouter.py`` and ``concept_explode_inspector.py``
supply the ``concept-images`` and ``exploded-view-check`` capabilities over
HTTP. This module supplies the sole implementation of the third capability,
``wish-research``: :class:`AgentWishResearcher`, a thin adapter that satisfies
the ``WishResearcher`` port by dispatching through one shared ``ModelDoor``,
under that capability's own role name (``wish-research`` — the same string
Concept's own ``Need`` already carries).

Nothing here changes Concept, ``ConceptContext``, or ``ConceptImages``.
Wiring this adapter in is a caller's wiring decision, made once, outside
Concept.

The parsing here (missing fact raises, unattributed field raises, unknown
cited source raises) and the research task instructions
(:data:`RESEARCH_INSTRUCTIONS`) are the same ones the now-deleted HTTP wish
researcher established — moved here rather than duplicated or loosened.
"""

from __future__ import annotations

import os
import shlex
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from .agent_session import AgentRoleConfig, AgentSessionDoor
from .concept import WishResearchRequest
from .doors import ModelDoor
from .env import load_dotenv
from .errors import ConceptProviderError, ContractError
from .jobs import ConceptComponent, WishResearch, WishResearchFinding, WishResearchSource
from .models import utc_now

ROLE_WISH_RESEARCH = "wish-research"

# Environment variables read by concept_agent_session_door_from_env(). No
# vendor or binary is assumed -- AGENT_DOOR_LAUNCH_COMMAND is a caller-owned
# shell command line, split the same way a shell would.
ENV_AGENT_DOOR_LAUNCH_COMMAND = "AGENT_DOOR_LAUNCH_COMMAND"
_WISH_RESEARCH_ENV_PREFIX = "AGENT_DOOR_WISH_RESEARCH"

_REQUIRED_ANSWER_FIELDS = (
    "object",
    "category",
    "envelope_mm",
    "wall_mm",
    "features",
    "print",
    "components",
    "findings",
)
_COMPONENT_FIELDS = (
    "key",
    "name",
    "purpose",
    "form",
    "dimensions_mm",
    "placement",
    "interfaces",
)

RESEARCH_INSTRUCTIONS = (
    "You are breaking one wished-for object down into the physical facts a "
    "3D-printable design can be built from. Search the web for what the named "
    "object actually is, how big it really is, and what parts it is made of.\n\n"
    "Reply with ONLY one JSON object, and no other text, with exactly these "
    "keys:\n"
    '  "object": what the design is, in one phrase\n'
    '  "category": the kind of thing it is\n'
    '  "envelope_mm": [length, width, height] in millimetres\n'
    '  "wall_mm": wall thickness in millimetres\n'
    '  "features": a list of the distinctive features this object has, each '
    "specific to this wish; never restate the wish's own objective back as a "
    "feature\n"
    '  "print": {"orientation": how it sits on the bed, "supports": true or '
    "false}\n"
    '  "fits": null, or {"target": what it holds, "ref_mm": [l, w, h] of the '
    'held thing, "clearance_mm": clearance around it}\n'
    '  "components": the parts the object actually has, each with "key" (a '
    'lowercase hyphenated id), "name", "purpose", "form", "dimensions_mm" '
    '([l, w, h]), "placement", and "interfaces". These are part TYPES, not '
    "instances: how many of each there are belongs in that part's purpose and "
    "placement text. Name one component only if the design genuinely prints as "
    "one part.\n"
    '  "findings": one entry per stated fact, each with "claim" (what you '
    'decided) and "field" (one of object, category, envelope_mm, wall_mm, '
    "features, print, components, fits).\n\n"
    "ATTRIBUTION IS REQUIRED. Every finding must carry exactly one of:\n"
    '  "sources": [the exact URLs you read that state this fact], or\n'
    '  "decided_because": why you decided it yourself, when you found no '
    "source for it.\n"
    "Never carry both. Never carry neither. Never cite a URL you did not "
    "actually read in this search. Say plainly where you had no source rather "
    "than making a number look sourced.\n"
    "Every field listed above must have at least one finding, and 'fits' must "
    "have one whenever it is not null."
)


def _components(value: Any) -> Tuple[ConceptComponent, ...]:
    if isinstance(value, (str, bytes, Mapping)) or not isinstance(value, Sequence):
        raise ConceptProviderError(
            "wish researcher answer components must be a list of parts"
        )
    parts: List[ConceptComponent] = []
    for position, item in enumerate(value, start=1):
        if not isinstance(item, Mapping):
            raise ConceptProviderError(
                "wish researcher answer component %d is not an object" % position
            )
        missing = [name for name in _COMPONENT_FIELDS if name not in item]
        if missing:
            raise ConceptProviderError(
                "wish researcher answer component %s states no %s"
                % (item.get("key", position), ", ".join(missing))
            )
        try:
            parts.append(
                ConceptComponent(
                    item["key"],
                    item["name"],
                    item["purpose"],
                    item["form"],
                    item["dimensions_mm"],
                    item["placement"],
                    item["interfaces"],
                )
            )
        except ContractError as exc:
            raise ConceptProviderError(
                "wish researcher answer component %s is unusable: %s"
                % (item.get("key", position), exc)
            ) from exc
    return tuple(parts)


def _findings(
    value: Any, by_origin: Mapping[str, str]
) -> Tuple[WishResearchFinding, ...]:
    if isinstance(value, (str, bytes, Mapping)) or not isinstance(value, Sequence):
        raise ConceptProviderError("wish researcher answer findings must be a list")
    findings: List[WishResearchFinding] = []
    for position, item in enumerate(value, start=1):
        if not isinstance(item, Mapping):
            raise ConceptProviderError(
                "wish researcher answer finding %d is not an object" % position
            )
        cited = item.get("sources") or item.get("source_urls") or ()
        if isinstance(cited, (str, bytes)) or not isinstance(cited, Sequence):
            raise ConceptProviderError(
                "wish researcher answer finding %d cites sources that are not "
                "a list" % position
            )
        identifiers = []
        for origin in cited:
            identifier = by_origin.get(origin) if isinstance(origin, str) else None
            if identifier is None:
                raise ConceptProviderError(
                    "wish researcher attributed a fact to %r, for which the "
                    "endpoint returned no origin or excerpt" % (origin,)
                )
            if identifier not in identifiers:
                identifiers.append(identifier)
        try:
            findings.append(
                WishResearchFinding(
                    item.get("claim"),
                    item.get("field"),
                    tuple(identifiers),
                    item.get("decided_because"),
                )
            )
        except ContractError as exc:
            raise ConceptProviderError(
                "wish researcher answer finding %d is unusable: %s"
                % (position, exc)
            ) from exc
    return tuple(findings)


def _require_door(door: Any, label: str) -> None:
    if not callable(getattr(door, "run", None)):
        raise ContractError("%s requires a ModelDoor" % label)


def _require_budget(budget_micros: Any, label: str) -> None:
    if (
        type(budget_micros) is not int
        or isinstance(budget_micros, bool)
        or budget_micros <= 0
    ):
        raise ContractError("%s budget_micros must be a positive integer" % label)


def _unwrap(outcome: Any, role: str) -> Mapping[str, Any]:
    if not isinstance(outcome, Mapping) or "result" not in outcome:
        raise ConceptProviderError(
            "agent door returned no result for role %r" % role
        )
    result = outcome["result"]
    if not isinstance(result, Mapping):
        raise ConceptProviderError(
            "agent door result for role %r is not a JSON object" % role
        )
    return result


class AgentWishResearcher:
    """Ask a shared agent door, running the ``wish-research`` role, what to build.

    Satisfies the ``WishResearcher`` callable contract. The door's result is
    parsed with the same strict rules the now-deleted HTTP wish researcher
    established: every field ``_REQUIRED_ANSWER_FIELDS`` names must be
    present and decided, every finding must cite a source or record a
    decision, and a finding that cites a source the result did not itself
    report is refused.
    """

    ROLE = ROLE_WISH_RESEARCH

    def __init__(
        self,
        door: ModelDoor,
        budget_micros: int,
        *,
        clock: Callable[[], str] = utc_now,
    ) -> None:
        _require_door(door, "AgentWishResearcher")
        _require_budget(budget_micros, "AgentWishResearcher")
        self._door = door
        self._budget_micros = budget_micros
        self._clock = clock

    def __call__(self, request: WishResearchRequest) -> WishResearch:
        if not isinstance(request, WishResearchRequest):
            raise ContractError(
                "AgentWishResearcher requires a WishResearchRequest"
            )
        door_request = {
            "wish": request.wish.to_dict(),
            "taste": {
                "name": request.taste.name,
                "description": request.taste.description,
            },
            "lane": request.blueprint.lane,
            "round": request.round,
            "instructions": RESEARCH_INSTRUCTIONS,
        }
        outcome = self._door.run(self.ROLE, door_request, self._budget_micros)
        return self._parse(_unwrap(outcome, self.ROLE))

    def _parse(self, parsed: Mapping[str, Any]) -> WishResearch:
        for name in _REQUIRED_ANSWER_FIELDS:
            if parsed.get(name) in (None, "", [], {}):
                raise ConceptProviderError(
                    "agent wish researcher result states no %s; the "
                    "breakdown must decide it and this adapter will not "
                    "fill it in" % name
                )
        sources, by_origin = self._sources(parsed.get("sources") or ())
        components = _components(parsed["components"])
        findings = _findings(parsed["findings"], by_origin)
        try:
            return WishResearch(
                parsed["object"],
                parsed["category"],
                parsed["envelope_mm"],
                parsed["wall_mm"],
                parsed["features"],
                parsed["print"],
                components,
                parsed.get("fits") or None,
                findings,
                sources,
            )
        except ContractError as exc:
            raise ConceptProviderError(
                "agent wish researcher result is not a usable breakdown: %s"
                % exc
            ) from exc

    def _sources(
        self, value: Any
    ) -> Tuple[Tuple[WishResearchSource, ...], Dict[str, str]]:
        if isinstance(value, (str, bytes, Mapping)) or not isinstance(
            value, Sequence
        ):
            raise ConceptProviderError(
                "agent wish researcher result sources must be a list"
            )
        records = []
        by_origin: Dict[str, str] = {}
        for index, item in enumerate(value, start=1):
            if not isinstance(item, Mapping):
                raise ConceptProviderError(
                    "agent wish researcher source %d is not an object" % index
                )
            origin = item.get("origin")
            excerpt = item.get("excerpt")
            if not isinstance(origin, str) or not origin.strip():
                raise ConceptProviderError(
                    "agent wish researcher source %d states no origin" % index
                )
            if not isinstance(excerpt, str) or not excerpt.strip():
                raise ConceptProviderError(
                    "agent wish researcher source %d states no excerpt" % index
                )
            title = item.get("title")
            if not isinstance(title, str) or not title.strip():
                title = origin
            retrieved_at = item.get("retrieved_at")
            if not isinstance(retrieved_at, str) or not retrieved_at.strip():
                retrieved_at = self._clock()
            identifier = "s%03d" % index
            records.append(
                WishResearchSource.create(
                    identifier, origin, title[:500], excerpt[:20_000], retrieved_at
                )
            )
            by_origin.setdefault(origin, identifier)
        return tuple(records), by_origin


def concept_agent_session_door_from_env(
    *, dotenv_path: Optional[str] = None, **overrides: Any
) -> AgentSessionDoor:
    """Build the shared agent door for the ``wish-research`` role from the environment.

    Reads ``AGENT_DOOR_LAUNCH_COMMAND`` -- a shell-style command line for the
    caller's own agent process, split with :func:`shlex.split` -- and the
    ``wish-research`` role's ``AGENT_DOOR_WISH_RESEARCH_TOOLS``
    (comma-separated), ``AGENT_DOOR_WISH_RESEARCH_ALLOWED_PATHS``
    (comma-separated), and ``AGENT_DOOR_WISH_RESEARCH_WALL_CLOCK_SECONDS``,
    plus an optional ``AGENT_DOOR_WISH_RESEARCH_MAX_BUDGET_MICROS``. All three
    required variables must be set; no default tool access, path access, or
    vendor is assumed. A real environment variable always wins over one
    loaded from a ``.env`` file. Any keyword also accepted by
    :class:`AgentSessionDoor` may be passed to override what the environment
    supplies (for example ``launcher`` in tests).
    """

    load_dotenv(dotenv_path)
    command = os.environ.get(ENV_AGENT_DOOR_LAUNCH_COMMAND, "")
    if not command.strip():
        raise ContractError(
            "concept_agent_session_door_from_env requires %s to be set"
            % ENV_AGENT_DOOR_LAUNCH_COMMAND
        )
    prefix = _WISH_RESEARCH_ENV_PREFIX
    tools = os.environ.get(prefix + "_TOOLS", "")
    allowed_paths = os.environ.get(prefix + "_ALLOWED_PATHS", "")
    wall_clock = os.environ.get(prefix + "_WALL_CLOCK_SECONDS", "")
    missing = [
        name
        for name, value in (
            (prefix + "_TOOLS", tools),
            (prefix + "_ALLOWED_PATHS", allowed_paths),
            (prefix + "_WALL_CLOCK_SECONDS", wall_clock),
        )
        if not value.strip()
    ]
    if missing:
        raise ContractError(
            "concept_agent_session_door_from_env requires %s to be set"
            % ", ".join(missing)
        )
    try:
        wall_clock_seconds = int(wall_clock)
    except ValueError as exc:
        raise ContractError(
            "%s_WALL_CLOCK_SECONDS must be an integer" % prefix
        ) from exc
    kwargs: Dict[str, Any] = {
        "tools": tuple(item.strip() for item in tools.split(",") if item.strip()),
        "allowed_paths": tuple(
            item.strip() for item in allowed_paths.split(",") if item.strip()
        ),
        "wall_clock_seconds": wall_clock_seconds,
    }
    max_budget = os.environ.get(prefix + "_MAX_BUDGET_MICROS", "")
    if max_budget.strip():
        try:
            kwargs["max_budget_micros"] = int(max_budget)
        except ValueError as exc:
            raise ContractError(
                "%s_MAX_BUDGET_MICROS must be an integer" % prefix
            ) from exc
    role_configs: Dict[str, AgentRoleConfig] = {
        ROLE_WISH_RESEARCH: AgentRoleConfig(**kwargs)
    }
    return AgentSessionDoor(shlex.split(command), role_configs, **overrides)


__all__ = [
    "AgentWishResearcher",
    "ENV_AGENT_DOOR_LAUNCH_COMMAND",
    "RESEARCH_INSTRUCTIONS",
    "ROLE_WISH_RESEARCH",
    "concept_agent_session_door_from_env",
]
