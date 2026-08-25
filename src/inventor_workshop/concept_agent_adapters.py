"""Concept's three ports, satisfied by dispatching through a shared agent door.

``concept.py`` already owns the prompts, the generation order, and the
sealing; ``wish_researcher_openrouter.py``, ``concept_artist_openrouter.py``,
and ``concept_explode_inspector.py`` already supply one real implementation
of each of Concept's ports, each independently configured with its own base
URL, API key, and model. This module supplies an alternative: three thin
adapters — :class:`AgentWishResearcher`, :class:`AgentConceptArtist`,
:class:`AgentExplodeInspector` — that satisfy the exact same port contracts
by dispatching through one shared ``ModelDoor``, under that capability's own
name (``wish-research``, ``concept-images``, ``exploded-view-check`` — the
same strings Concept's own ``Need``s already carry).

Nothing here changes Concept, ``ConceptContext``, or ``ConceptImages``.
Wiring an agent-backed adapter in place of the existing single-shot one is a
caller's wiring decision, made once, outside Concept — and the existing
OpenRouter-specific adapters remain a valid, cheaper alternative for callers
who do not need agentic depth for these three roles.

The wish-research adapter reuses the strict parsing
``wish_researcher_openrouter.py`` already established (missing fact raises,
unattributed field raises, unknown cited source raises) rather than
duplicating or loosening it — the same posture ``concept_explode_inspector.py``
already takes reusing ``concept_artist_openrouter.py``'s image-format
sniffing.
"""

from __future__ import annotations

import base64
import os
import shlex
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, Sequence, Tuple

from .agent_session import AgentRoleConfig, AgentSessionDoor
from .concept import ConceptImageRequest, WishResearchRequest
from .concept_artist_openrouter import _sniff_image_media_type
from .doors import ModelDoor
from .env import load_dotenv
from .errors import ConceptProviderError, ContractError
from .jobs import ConceptBrief, WishResearch, WishResearchSource
from .models import utc_now
from .wish_researcher_openrouter import (
    _REQUIRED_ANSWER_FIELDS,
    OpenAICompatibleWishResearcher,
)

ROLE_WISH_RESEARCH = "wish-research"
ROLE_CONCEPT_IMAGES = "concept-images"
ROLE_EXPLODED_VIEW_CHECK = "exploded-view-check"

# Environment variables read by concept_agent_session_door_from_env(). No
# vendor or binary is assumed -- AGENT_DOOR_LAUNCH_COMMAND is a caller-owned
# shell command line, split the same way a shell would.
ENV_AGENT_DOOR_LAUNCH_COMMAND = "AGENT_DOOR_LAUNCH_COMMAND"
_ROLE_ENV_PREFIXES = (
    (ROLE_WISH_RESEARCH, "AGENT_DOOR_WISH_RESEARCH"),
    (ROLE_CONCEPT_IMAGES, "AGENT_DOOR_CONCEPT_IMAGES"),
    (ROLE_EXPLODED_VIEW_CHECK, "AGENT_DOOR_EXPLODED_VIEW_CHECK"),
)


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
    parsed with the same strict rules ``OpenAICompatibleWishResearcher``
    already applies: every field ``_REQUIRED_ANSWER_FIELDS`` names must be
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
        components = OpenAICompatibleWishResearcher._components(
            parsed["components"]
        )
        findings = OpenAICompatibleWishResearcher._findings(
            parsed["findings"], by_origin
        )
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


class AgentConceptArtist:
    """Draw one image per :class:`ConceptImageRequest` through a shared agent door.

    Satisfies the ``ConceptArtist`` callable contract: requests and returns
    exactly one image per call, written into the request's own workspace
    location, matching the OpenRouter artist's one-request-one-image
    contract.
    """

    ROLE = ROLE_CONCEPT_IMAGES

    def __init__(self, door: ModelDoor, budget_micros: int) -> None:
        _require_door(door, "AgentConceptArtist")
        _require_budget(budget_micros, "AgentConceptArtist")
        self._door = door
        self._budget_micros = budget_micros

    def __call__(self, request: ConceptImageRequest) -> str:
        if not isinstance(request, ConceptImageRequest):
            raise ContractError(
                "AgentConceptArtist requires a ConceptImageRequest"
            )
        door_request = {
            "role": request.role,
            "kind": request.kind,
            "prompt": request.prompt,
            "round": request.round,
            "brief": request.brief.to_dict(),
            "references": [
                self._encode_reference(path) for path in request.references
            ],
        }
        outcome = self._door.run(self.ROLE, door_request, self._budget_micros)
        result = _unwrap(outcome, self.ROLE)
        image_bytes = self._decode_image(result, request.role)
        target = request.workspace / request.filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(image_bytes)
        return request.filename

    @staticmethod
    def _encode_reference(path: Path) -> Mapping[str, Any]:
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise ConceptProviderError(
                "could not read concept reference %s: %s" % (path, exc)
            ) from exc
        media_type = _sniff_image_media_type(data)
        if media_type is None:
            raise ConceptProviderError(
                "concept reference %s is not a recognized image format" % path
            )
        return {
            "media_type": media_type,
            "data_base64": base64.b64encode(data).decode("ascii"),
        }

    @staticmethod
    def _decode_image(result: Mapping[str, Any], role: str) -> bytes:
        encoded = result.get("image_base64")
        if not isinstance(encoded, str) or not encoded.strip():
            raise ConceptProviderError(
                "agent door returned no image for %r" % role
            )
        try:
            return base64.b64decode(encoded, validate=True)
        except (ValueError, TypeError) as exc:
            raise ConceptProviderError(
                "agent door returned malformed base64 image data for %r: %s"
                % (role, exc)
            ) from exc


class AgentExplodeInspector:
    """Ask a shared agent door which components an exploded view shows.

    Satisfies the ``ExplodeInspector`` callable contract: given the exploded
    image path and the brief, returns only component keys the brief actually
    offered, refusing an answer that names anything else.
    """

    ROLE = ROLE_EXPLODED_VIEW_CHECK

    def __init__(self, door: ModelDoor, budget_micros: int) -> None:
        _require_door(door, "AgentExplodeInspector")
        _require_budget(budget_micros, "AgentExplodeInspector")
        self._door = door
        self._budget_micros = budget_micros

    def __call__(self, image: Path, brief: ConceptBrief) -> Sequence[str]:
        if not isinstance(brief, ConceptBrief):
            raise ContractError(
                "AgentExplodeInspector requires a ConceptBrief"
            )
        image_path = Path(image)
        try:
            data = image_path.read_bytes()
        except OSError as exc:
            raise ConceptProviderError(
                "could not read exploded-view image %s: %s" % (image_path, exc)
            ) from exc
        media_type = _sniff_image_media_type(data)
        if media_type is None:
            raise ConceptProviderError(
                "exploded-view image %s is not a recognized image format"
                % image_path
            )
        door_request = {
            "object": brief.object,
            "components": [
                {"key": component.key, "name": component.name}
                for component in brief.components
            ],
            "image": {
                "media_type": media_type,
                "data_base64": base64.b64encode(data).decode("ascii"),
            },
        }
        outcome = self._door.run(self.ROLE, door_request, self._budget_micros)
        result = _unwrap(outcome, self.ROLE)
        return self._offered_keys(result.get("components"), brief)

    @staticmethod
    def _offered_keys(value: Any, brief: ConceptBrief) -> Tuple[str, ...]:
        if isinstance(value, (str, bytes, Mapping)) or not isinstance(
            value, Sequence
        ):
            raise ConceptProviderError(
                "agent door exploded-view result must be a list of "
                "component keys"
            )
        offered = set(brief.component_keys)
        seen = set()
        ordered = []
        for key in value:
            if not isinstance(key, str) or not key.strip():
                raise ConceptProviderError(
                    "agent door exploded-view result contains a non-string "
                    "component key"
                )
            if key not in offered:
                raise ConceptProviderError(
                    "agent door named components that were never offered: %s"
                    % key
                )
            if key not in seen:
                seen.add(key)
                ordered.append(key)
        return tuple(ordered)


def concept_agent_session_door_from_env(
    *, dotenv_path: Optional[str] = None, **overrides: Any
) -> AgentSessionDoor:
    """Build the shared agent door for Concept's three roles from the environment.

    Reads ``AGENT_DOOR_LAUNCH_COMMAND`` -- a shell-style command line for the
    caller's own agent process, split with :func:`shlex.split` -- and, for
    each of ``wish-research``, ``concept-images``, and ``exploded-view-check``,
    that role's ``_TOOLS`` (comma-separated), ``_ALLOWED_PATHS``
    (comma-separated), and ``_WALL_CLOCK_SECONDS``, plus an optional
    ``_MAX_BUDGET_MICROS``. All three per-role variables are required; no
    default tool access, path access, or vendor is assumed. A real
    environment variable always wins over one loaded from a ``.env`` file.
    Any keyword also accepted by :class:`AgentSessionDoor` may be passed to
    override what the environment supplies (for example ``launcher`` in
    tests).
    """

    load_dotenv(dotenv_path)
    command = os.environ.get(ENV_AGENT_DOOR_LAUNCH_COMMAND, "")
    if not command.strip():
        raise ContractError(
            "concept_agent_session_door_from_env requires %s to be set"
            % ENV_AGENT_DOOR_LAUNCH_COMMAND
        )
    role_configs: Dict[str, AgentRoleConfig] = {}
    for role, prefix in _ROLE_ENV_PREFIXES:
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
        role_configs[role] = AgentRoleConfig(**kwargs)
    return AgentSessionDoor(shlex.split(command), role_configs, **overrides)


__all__ = [
    "AgentConceptArtist",
    "AgentExplodeInspector",
    "AgentWishResearcher",
    "ENV_AGENT_DOOR_LAUNCH_COMMAND",
    "ROLE_CONCEPT_IMAGES",
    "ROLE_EXPLODED_VIEW_CHECK",
    "ROLE_WISH_RESEARCH",
    "concept_agent_session_door_from_env",
]
