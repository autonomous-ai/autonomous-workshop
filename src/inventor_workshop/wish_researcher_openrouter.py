"""A real ``WishResearcher`` backed by a caller-configured chat endpoint.

``DefaultConcept`` (``concept.py``) derives its brief from a researched
breakdown of the Wish, through an injected ``wish_researcher``. This module
supplies a real one — it does not assume any vendor. The base URL, API key, and
model are all supplied by the caller, exactly as they are for the concept artist
and the exploded-view inspector; it is a plain contract, not a hardcoded host.

The request enables the endpoint's web search facility and asks for every stated
fact to name the source it came from, or to say plainly that it had none. The
answer is parsed strictly: a missing fact raises rather than being filled in, an
unparseable answer raises rather than becoming an empty breakdown, and a fact
citing a source the endpoint returned no material for raises rather than being
recorded as a source that cannot be shown.

Nothing here is wired into any inventor. A Workshop that has not been given a
researcher keeps waiting truthfully for the wish-research capability.
"""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from ._http import HttpResponse, Transport, make_urllib_transport
from .concept import WishResearchRequest
from .env import load_dotenv
from .errors import ConceptProviderError, ContractError
from .jobs import (
    ConceptComponent,
    WishResearch,
    WishResearchFinding,
    WishResearchSource,
)
from .models import utc_now

DEFAULT_MAX_RESPONSE_BYTES = 2 * 1024 * 1024
DEFAULT_TIMEOUT_SECONDS = 120
DEFAULT_MAX_ATTEMPTS = 3
CHAT_COMPLETIONS_PATH = "/chat/completions"
WEB_SEARCH_PLUGIN_ID = "web"

# Environment variables read by OpenAICompatibleWishResearcher.from_env().
# No default host is assumed -- all three name the caller's own endpoint.
ENV_WISH_RESEARCHER_BASE_URL = "WISH_RESEARCHER_BASE_URL"
ENV_WISH_RESEARCHER_API_KEY = "WISH_RESEARCHER_API_KEY"
ENV_WISH_RESEARCHER_MODEL = "WISH_RESEARCHER_MODEL"

_JSON_OBJECT = re.compile(r"\{.*\}", re.DOTALL)
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

_INSTRUCTIONS = (
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


def _is_retryable_status(status: int) -> bool:
    return status == 429 or 500 <= status <= 599


def _error_excerpt(body: bytes) -> str:
    return body.decode("utf-8", errors="replace")[:500]


def _research_prompt(request: WishResearchRequest) -> str:
    constraints = json.dumps(
        dict(request.wish.constraints), sort_keys=True, ensure_ascii=False
    )
    return "\n\n".join(
        (
            "WISH OBJECTIVE (the person's own words): %s" % request.wish.objective,
            "WISH CONSTRAINTS (already decided; honour them): %s" % constraints,
            "INVENTOR TASTE: %s — %s"
            % (request.taste.name, request.taste.description),
            "LANE: %s" % request.blueprint.lane,
            _INSTRUCTIONS,
        )
    )


def _extract_json_object(text: str) -> Any:
    stripped = text.strip()
    try:
        return json.loads(stripped)
    except ValueError:
        pass
    match = _JSON_OBJECT.search(stripped)
    if match is None:
        raise ValueError("no JSON object found in answer")
    return json.loads(match.group(0))


class OpenAICompatibleWishResearcher:
    """Ask a caller-configured chat endpoint, with web search, what to build.

    Satisfies the ``WishResearcher`` callable contract: given one
    :class:`WishResearchRequest`, returns the :class:`WishResearch` the endpoint
    actually stated, with the sources it actually returned. It decides nothing
    on the endpoint's behalf.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        *,
        max_response_bytes: int = DEFAULT_MAX_RESPONSE_BYTES,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        transport: Optional[Transport] = None,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], str] = utc_now,
    ) -> None:
        if not isinstance(base_url, str) or not base_url.strip():
            raise ContractError(
                "OpenAICompatibleWishResearcher requires a non-empty base_url"
            )
        if not base_url.startswith("https://") and not base_url.startswith(
            "http://"
        ):
            raise ContractError(
                "OpenAICompatibleWishResearcher base_url must be an HTTP(S) URL"
            )
        if not isinstance(api_key, str) or not api_key.strip():
            raise ContractError(
                "OpenAICompatibleWishResearcher requires a non-empty api_key"
            )
        if not isinstance(model, str) or not model.strip():
            raise ContractError(
                "OpenAICompatibleWishResearcher requires a non-empty model"
            )
        if (
            not isinstance(timeout_seconds, int)
            or isinstance(timeout_seconds, bool)
            or timeout_seconds <= 0
        ):
            raise ContractError(
                "OpenAICompatibleWishResearcher timeout_seconds must be a "
                "positive integer"
            )
        if (
            not isinstance(max_attempts, int)
            or isinstance(max_attempts, bool)
            or max_attempts < 1
        ):
            raise ContractError(
                "OpenAICompatibleWishResearcher max_attempts must be a "
                "positive integer"
            )
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._max_attempts = max_attempts
        self._sleep = sleep
        self._clock = clock
        self._transport = transport or make_urllib_transport(
            max_response_bytes, oversize_error=ConceptProviderError
        )

    @classmethod
    def from_env(
        cls, *, dotenv_path: Optional[str] = None, **overrides: Any
    ) -> "OpenAICompatibleWishResearcher":
        """Build from environment variables, loading a ``.env`` file first.

        Reads ``WISH_RESEARCHER_BASE_URL``, ``WISH_RESEARCHER_API_KEY``, and
        ``WISH_RESEARCHER_MODEL`` -- all required, since this adapter assumes no
        vendor. A real environment variable always wins over one loaded from the
        file.
        """

        load_dotenv(dotenv_path)
        values = {
            ENV_WISH_RESEARCHER_BASE_URL: os.environ.get(
                ENV_WISH_RESEARCHER_BASE_URL, ""
            ),
            ENV_WISH_RESEARCHER_API_KEY: os.environ.get(
                ENV_WISH_RESEARCHER_API_KEY, ""
            ),
            ENV_WISH_RESEARCHER_MODEL: os.environ.get(
                ENV_WISH_RESEARCHER_MODEL, ""
            ),
        }
        missing = [name for name, value in values.items() if not value.strip()]
        if missing:
            raise ContractError(
                "OpenAICompatibleWishResearcher.from_env requires %s to be set"
                % ", ".join(missing)
            )
        return cls(
            values[ENV_WISH_RESEARCHER_BASE_URL],
            values[ENV_WISH_RESEARCHER_API_KEY],
            values[ENV_WISH_RESEARCHER_MODEL],
            **overrides
        )

    def __call__(self, request: WishResearchRequest) -> WishResearch:
        if not isinstance(request, WishResearchRequest):
            raise ContractError(
                "OpenAICompatibleWishResearcher requires a WishResearchRequest"
            )
        payload: Dict[str, Any] = {
            "model": self._model,
            "stream": False,
            # Web search, so the answer can rest on retrieved material rather
            # than recall alone. The endpoint's returned citations become the
            # source records behind the findings.
            "plugins": [{"id": WEB_SEARCH_PLUGIN_ID}],
            "messages": [
                {"role": "user", "content": _research_prompt(request)}
            ],
        }
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": "Bearer %s" % self._api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        response = self._send(
            "POST", self._base_url + CHAT_COMPLETIONS_PATH, headers, body
        )
        answer, annotations = self._message(response)
        return self._parse(answer, annotations)

    def _send(
        self, method: str, url: str, headers: Mapping[str, str], body: bytes
    ) -> HttpResponse:
        attempt = 0
        while True:
            attempt += 1
            response = self._transport(
                method, url, headers, body, self._timeout_seconds
            )
            if response.status < 400:
                return response
            if (
                not _is_retryable_status(response.status)
                or attempt >= self._max_attempts
            ):
                raise ConceptProviderError(
                    "wish research request failed with HTTP %d: %s"
                    % (response.status, _error_excerpt(response.body))
                )
            self._sleep(2.0 ** (attempt - 1))

    @staticmethod
    def _message(response: HttpResponse) -> Tuple[str, Sequence[Any]]:
        """The answer text and the endpoint's own returned source citations."""

        try:
            payload = json.loads(response.body.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise ConceptProviderError(
                "wish researcher returned a response that is not JSON: %s" % exc
            ) from exc
        if not isinstance(payload, Mapping):
            raise ConceptProviderError(
                "wish researcher response is not a JSON object"
            )
        choices = payload.get("choices")
        if (
            isinstance(choices, (str, bytes))
            or not isinstance(choices, Sequence)
            or not choices
            or not isinstance(choices[0], Mapping)
        ):
            raise ConceptProviderError(
                "wish researcher response carries no answer"
            )
        message = choices[0].get("message")
        if not isinstance(message, Mapping):
            raise ConceptProviderError(
                "wish researcher response carries no answer message"
            )
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ConceptProviderError(
                "wish researcher answer carries no text"
            )
        annotations = message.get("annotations")
        if isinstance(annotations, (str, bytes)) or not isinstance(
            annotations, Sequence
        ):
            annotations = ()
        return content, tuple(annotations)

    def _sources(
        self, annotations: Sequence[Any]
    ) -> Tuple[Tuple[WishResearchSource, ...], Dict[str, str]]:
        """Turn the endpoint's citations into records, keyed by their origin."""

        retrieved_at = self._clock()
        records: List[WishResearchSource] = []
        by_origin: Dict[str, str] = {}
        for index, annotation in enumerate(annotations, start=1):
            if not isinstance(annotation, Mapping):
                continue
            citation = annotation.get("url_citation")
            if not isinstance(citation, Mapping):
                citation = annotation
            origin = citation.get("url")
            excerpt = citation.get("content")
            if not isinstance(origin, str) or not origin.strip():
                continue
            if not isinstance(excerpt, str) or not excerpt.strip():
                # A citation with no material is not a source that can be
                # shown, so it is not recorded as one. A finding that cites it
                # fails below rather than resting on an empty record.
                continue
            title = citation.get("title")
            if not isinstance(title, str) or not title.strip():
                title = origin
            identifier = "s%03d" % index
            records.append(
                WishResearchSource.create(
                    identifier,
                    origin,
                    title[:500],
                    excerpt[:20_000],
                    retrieved_at,
                )
            )
            by_origin.setdefault(origin, identifier)
        return tuple(records), by_origin

    def _parse(self, answer: str, annotations: Sequence[Any]) -> WishResearch:
        try:
            parsed = _extract_json_object(answer)
        except ValueError as exc:
            raise ConceptProviderError(
                "wish researcher answer could not be parsed into a breakdown: %s"
                % exc
            ) from exc
        if not isinstance(parsed, Mapping):
            raise ConceptProviderError(
                "wish researcher answer is not a JSON object"
            )
        for name in _REQUIRED_ANSWER_FIELDS:
            if parsed.get(name) in (None, "", [], {}):
                raise ConceptProviderError(
                    "wish researcher answer states no %s; the breakdown must "
                    "decide it and this adapter will not fill it in" % name
                )
        sources, by_origin = self._sources(annotations)
        components = self._components(parsed["components"])
        findings = self._findings(parsed["findings"], by_origin)
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
                "wish researcher answer is not a usable breakdown: %s" % exc
            ) from exc

    @staticmethod
    def _components(value: Any) -> Tuple[ConceptComponent, ...]:
        if isinstance(value, (str, bytes, Mapping)) or not isinstance(
            value, Sequence
        ):
            raise ConceptProviderError(
                "wish researcher answer components must be a list of parts"
            )
        parts: List[ConceptComponent] = []
        for position, item in enumerate(value, start=1):
            if not isinstance(item, Mapping):
                raise ConceptProviderError(
                    "wish researcher answer component %d is not an object"
                    % position
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

    @staticmethod
    def _findings(
        value: Any, by_origin: Mapping[str, str]
    ) -> Tuple[WishResearchFinding, ...]:
        if isinstance(value, (str, bytes, Mapping)) or not isinstance(
            value, Sequence
        ):
            raise ConceptProviderError(
                "wish researcher answer findings must be a list"
            )
        findings: List[WishResearchFinding] = []
        for position, item in enumerate(value, start=1):
            if not isinstance(item, Mapping):
                raise ConceptProviderError(
                    "wish researcher answer finding %d is not an object" % position
                )
            cited = item.get("sources") or item.get("source_urls") or ()
            if isinstance(cited, (str, bytes)) or not isinstance(cited, Sequence):
                raise ConceptProviderError(
                    "wish researcher answer finding %d cites sources that are "
                    "not a list" % position
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


__all__ = [
    "CHAT_COMPLETIONS_PATH",
    "DEFAULT_MAX_ATTEMPTS",
    "DEFAULT_MAX_RESPONSE_BYTES",
    "DEFAULT_TIMEOUT_SECONDS",
    "ENV_WISH_RESEARCHER_API_KEY",
    "ENV_WISH_RESEARCHER_BASE_URL",
    "ENV_WISH_RESEARCHER_MODEL",
    "OpenAICompatibleWishResearcher",
    "WEB_SEARCH_PLUGIN_ID",
]
