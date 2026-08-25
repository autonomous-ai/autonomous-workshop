"""A real ``ExplodeInspector`` backed by a caller-configured vision endpoint.

``DefaultConcept`` (``concept.py``) checks the exploded view for component
completeness before drawing any component image, through an injected
``explode_inspector``. This module supplies a real one — it does not assume
any vendor. The base URL, API key, and model are all supplied by the caller,
because the exact "OpenAI-compatible" endpoint to use was not yet decided
when this module was written; it is a plain contract, not a hardcoded host.
"""

from __future__ import annotations

import base64
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from ._http import HttpResponse, Transport, make_urllib_transport
from .concept_artist_openrouter import _sniff_image_media_type
from .env import load_dotenv
from .errors import ConceptProviderError, ContractError
from .jobs import ConceptBrief

DEFAULT_MAX_RESPONSE_BYTES = 4 * 1024 * 1024
DEFAULT_TIMEOUT_SECONDS = 60
DEFAULT_MAX_ATTEMPTS = 3
CHAT_COMPLETIONS_PATH = "/chat/completions"

# Environment variables read by OpenAICompatibleExplodeInspector.from_env().
# No default host is assumed -- all three name the caller's own endpoint.
ENV_EXPLODE_INSPECTOR_BASE_URL = "CONCEPT_EXPLODE_INSPECTOR_BASE_URL"
ENV_EXPLODE_INSPECTOR_API_KEY = "CONCEPT_EXPLODE_INSPECTOR_API_KEY"
ENV_EXPLODE_INSPECTOR_MODEL = "CONCEPT_EXPLODE_INSPECTOR_MODEL"

_JSON_ARRAY_OR_OBJECT = re.compile(r"[\[{].*[\]}]", re.DOTALL)


def _is_retryable_status(status: int) -> bool:
    return status == 429 or 500 <= status <= 599


def _error_excerpt(body: bytes) -> str:
    return body.decode("utf-8", errors="replace")[:500]


def _inspection_prompt(brief: ConceptBrief) -> str:
    offered = "\n".join(
        "- %s: %s" % (component.key, component.name) for component in brief.components
    )
    return (
        "This image is an exploded view of %s. It should separate every "
        "component below along the assembly axes, each one wholly visible.\n\n"
        "Components offered (answer using ONLY these keys):\n%s\n\n"
        "Reply with ONLY a JSON array of the component keys you can see as "
        "distinct, separated parts in the image. Use exactly the keys listed "
        "above, spelled exactly as given. Omit a key if that component is not "
        "visible as its own separated part. If no components are visible, "
        "reply with an empty JSON array []. Do not include any other text."
        % (brief.object, offered)
    )


def _extract_json_answer(text: str) -> Any:
    stripped = text.strip()
    try:
        return json.loads(stripped)
    except ValueError:
        pass
    match = _JSON_ARRAY_OR_OBJECT.search(stripped)
    if match is None:
        raise ValueError("no JSON array or object found in answer")
    return json.loads(match.group(0))


def _parse_component_keys(value: Any) -> Tuple[str, ...]:
    """Accept a bare array of keys, or an object carrying one under a
    plausible field name — both are common shapes a small prompt like ours
    can come back as."""

    if isinstance(value, Mapping):
        for name in ("visible", "components", "keys", "visible_components"):
            if name in value:
                value = value[name]
                break
        else:
            raise ValueError("answer object does not name a components field")
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("answer is not a list of component keys")
    keys: List[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError("answer contains a non-string component key")
        keys.append(item)
    return tuple(keys)


class OpenAICompatibleExplodeInspector:
    """Ask a caller-configured vision endpoint which components are visible.

    Satisfies the ``ExplodeInspector`` callable contract: given the exploded
    image path and the brief, returns the component keys the endpoint
    reports as visible, offered-keys-only and strictly parsed.
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
    ) -> None:
        if not isinstance(base_url, str) or not base_url.strip():
            raise ContractError(
                "OpenAICompatibleExplodeInspector requires a non-empty base_url"
            )
        if not base_url.startswith("https://") and not base_url.startswith(
            "http://"
        ):
            raise ContractError(
                "OpenAICompatibleExplodeInspector base_url must be an HTTP(S) URL"
            )
        if not isinstance(api_key, str) or not api_key.strip():
            raise ContractError(
                "OpenAICompatibleExplodeInspector requires a non-empty api_key"
            )
        if not isinstance(model, str) or not model.strip():
            raise ContractError(
                "OpenAICompatibleExplodeInspector requires a non-empty model"
            )
        if (
            not isinstance(timeout_seconds, int)
            or isinstance(timeout_seconds, bool)
            or timeout_seconds <= 0
        ):
            raise ContractError(
                "OpenAICompatibleExplodeInspector timeout_seconds must be a "
                "positive integer"
            )
        if (
            not isinstance(max_attempts, int)
            or isinstance(max_attempts, bool)
            or max_attempts < 1
        ):
            raise ContractError(
                "OpenAICompatibleExplodeInspector max_attempts must be a "
                "positive integer"
            )
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._max_attempts = max_attempts
        self._sleep = sleep
        self._transport = transport or make_urllib_transport(
            max_response_bytes, oversize_error=ConceptProviderError
        )

    @classmethod
    def from_env(
        cls, *, dotenv_path: Optional[str] = None, **overrides: Any
    ) -> "OpenAICompatibleExplodeInspector":
        """Build from environment variables, loading a ``.env`` file first.

        Reads ``CONCEPT_EXPLODE_INSPECTOR_BASE_URL``,
        ``CONCEPT_EXPLODE_INSPECTOR_API_KEY``, and
        ``CONCEPT_EXPLODE_INSPECTOR_MODEL`` -- all required, since this
        adapter assumes no vendor. A real environment variable always wins
        over one loaded from the file.
        """

        load_dotenv(dotenv_path)
        values = {
            ENV_EXPLODE_INSPECTOR_BASE_URL: os.environ.get(
                ENV_EXPLODE_INSPECTOR_BASE_URL, ""
            ),
            ENV_EXPLODE_INSPECTOR_API_KEY: os.environ.get(
                ENV_EXPLODE_INSPECTOR_API_KEY, ""
            ),
            ENV_EXPLODE_INSPECTOR_MODEL: os.environ.get(
                ENV_EXPLODE_INSPECTOR_MODEL, ""
            ),
        }
        missing = [name for name, value in values.items() if not value.strip()]
        if missing:
            raise ContractError(
                "OpenAICompatibleExplodeInspector.from_env requires %s to be set"
                % ", ".join(missing)
            )
        return cls(
            values[ENV_EXPLODE_INSPECTOR_BASE_URL],
            values[ENV_EXPLODE_INSPECTOR_API_KEY],
            values[ENV_EXPLODE_INSPECTOR_MODEL],
            **overrides
        )

    def __call__(self, image: Path, brief: ConceptBrief) -> Sequence[str]:
        if not isinstance(brief, ConceptBrief):
            raise ContractError(
                "OpenAICompatibleExplodeInspector requires a ConceptBrief"
            )
        image_content = self._encode_image(Path(image))
        payload: Dict[str, Any] = {
            "model": self._model,
            "stream": True,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": _inspection_prompt(brief)},
                        image_content,
                    ],
                }
            ],
        }
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": "Bearer %s" % self._api_key,
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }
        response = self._send(
            "POST", self._base_url + CHAT_COMPLETIONS_PATH, headers, body
        )
        answer = self._extract_streamed_answer_text(response)
        return self._parse_offered_keys(answer, brief)

    @staticmethod
    def _encode_image(path: Path) -> Mapping[str, Any]:
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise ConceptProviderError(
                "could not read exploded-view image %s: %s" % (path, exc)
            ) from exc
        media_type = _sniff_image_media_type(data)
        if media_type is None:
            raise ConceptProviderError(
                "exploded-view image %s is not a recognized image format" % path
            )
        encoded = base64.b64encode(data).decode("ascii")
        return {
            "type": "image_url",
            "image_url": {"url": "data:%s;base64,%s" % (media_type, encoded)},
        }

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
                    "exploded-view inspection request failed with HTTP %d: %s"
                    % (response.status, _error_excerpt(response.body))
                )
            self._sleep(2.0 ** (attempt - 1))

    @staticmethod
    def _extract_streamed_answer_text(response: HttpResponse) -> str:
        """Accumulate an SSE chat-completions stream into its answer text.

        Every request sets ``stream: true``, so the response is a sequence of
        ``data: <chunk>`` lines ending in ``data: [DONE]`` rather than one JSON
        object. Each chunk's ``choices[0].delta.content`` is appended in
        order; a chunk that carries no content (the opening role-only chunk,
        the closing finish-reason chunk) is simply skipped.
        """

        try:
            text = response.body.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ConceptProviderError(
                "exploded-view inspector returned a non-UTF-8 streamed response: %s"
                % exc
            ) from exc
        pieces: List[str] = []
        for line in text.splitlines():
            line = line.strip()
            if not line.startswith("data:"):
                continue
            data = line[len("data:") :].strip()
            if not data or data == "[DONE]":
                continue
            try:
                chunk = json.loads(data)
            except ValueError as exc:
                raise ConceptProviderError(
                    "exploded-view inspector returned a malformed streamed "
                    "chunk: %s" % exc
                ) from exc
            if not isinstance(chunk, Mapping):
                raise ConceptProviderError(
                    "exploded-view inspector streamed chunk is not an object"
                )
            choices = chunk.get("choices")
            if (
                not isinstance(choices, Sequence)
                or isinstance(choices, (str, bytes))
                or not choices
            ):
                continue
            first = choices[0]
            if not isinstance(first, Mapping):
                continue
            delta = first.get("delta")
            content = delta.get("content") if isinstance(delta, Mapping) else None
            if isinstance(content, str) and content:
                pieces.append(content)
        answer = "".join(pieces)
        if not answer.strip():
            raise ConceptProviderError(
                "exploded-view inspector streamed response carries no answer text"
            )
        return answer

    @staticmethod
    def _parse_offered_keys(answer: str, brief: ConceptBrief) -> Tuple[str, ...]:
        try:
            parsed = _extract_json_answer(answer)
            keys = _parse_component_keys(parsed)
        except ValueError as exc:
            raise ConceptProviderError(
                "exploded-view inspector answer could not be parsed into "
                "component keys: %s" % exc
            ) from exc
        offered = set(brief.component_keys)
        unknown = [key for key in keys if key not in offered]
        if unknown:
            raise ConceptProviderError(
                "exploded-view inspector named components that were never "
                "offered: %s" % ", ".join(sorted(set(unknown)))
            )
        seen = set()
        ordered = []
        for key in keys:
            if key not in seen:
                seen.add(key)
                ordered.append(key)
        return tuple(ordered)


__all__ = [
    "CHAT_COMPLETIONS_PATH",
    "DEFAULT_MAX_ATTEMPTS",
    "DEFAULT_MAX_RESPONSE_BYTES",
    "DEFAULT_TIMEOUT_SECONDS",
    "ENV_EXPLODE_INSPECTOR_API_KEY",
    "ENV_EXPLODE_INSPECTOR_BASE_URL",
    "ENV_EXPLODE_INSPECTOR_MODEL",
    "OpenAICompatibleExplodeInspector",
]
