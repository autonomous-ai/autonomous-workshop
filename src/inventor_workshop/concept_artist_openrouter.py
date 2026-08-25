"""A real ``ConceptArtist`` that draws through OpenRouter's image API.

``DefaultConcept`` (``concept.py``) already owns the prompts, the generation
order, and the sealing; this module supplies the one thing it was missing —
an injected ``concept_artist`` that actually draws pixels, by calling
OpenRouter's unified image API (``POST /api/v1/images``) with model
``openai/gpt-image-2``. Not wired into any inventor by this module; a
Workshop operator constructs and injects it explicitly, the same way
``ShopDoor`` is constructed and injected today.
"""

from __future__ import annotations

import base64
import json
import os
import time
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, Sequence

from ._http import HttpResponse, Transport, make_urllib_transport
from .concept import ConceptImageRequest
from .env import load_dotenv
from .errors import ConceptProviderError, ContractError

OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
OPENROUTER_IMAGE_MODEL = "openai/gpt-image-2"

# Environment variables read by OpenRouterConceptArtist.from_env().
ENV_OPENROUTER_API_KEY = "OPENROUTER_API_KEY"
ENV_OPENROUTER_IMAGE_MODEL = "OPENROUTER_IMAGE_MODEL"
ENV_OPENROUTER_API_BASE = "OPENROUTER_API_BASE"

# OpenRouter's image API accepts at most 16 reference images per call.
MAX_INPUT_REFERENCES = 16

# Image payloads (base64 PNG) routinely exceed Shop's 2 MiB JSON-sized cap.
DEFAULT_MAX_RESPONSE_BYTES = 20 * 1024 * 1024
DEFAULT_TIMEOUT_SECONDS = 180
DEFAULT_MAX_ATTEMPTS = 3

_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_JPEG_MAGIC = b"\xff\xd8\xff"
_GIF_MAGICS = (b"GIF87a", b"GIF89a")


def _sniff_image_media_type(data: bytes) -> Optional[str]:
    """Identify an image's real format from its bytes, not its filename."""

    if data.startswith(_PNG_MAGIC):
        return "image/png"
    if data.startswith(_JPEG_MAGIC):
        return "image/jpeg"
    if any(data.startswith(magic) for magic in _GIF_MAGICS):
        return "image/gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def _is_retryable_status(status: int) -> bool:
    return status == 429 or 500 <= status <= 599


def _error_excerpt(body: bytes) -> str:
    return body.decode("utf-8", errors="replace")[:500]


class OpenRouterConceptArtist:
    """Draw one image per :class:`ConceptImageRequest` through OpenRouter.

    Satisfies the ``ConceptArtist`` callable contract: writes the produced
    image into ``request.workspace / request.filename`` and returns that
    relative filename. No seed or temperature is ever sent, and every call
    asks for exactly one image, matching the rest of Concept's already
    nondeterministic pipeline.
    """

    def __init__(
        self,
        api_key: str,
        *,
        model: str = OPENROUTER_IMAGE_MODEL,
        api_base: str = OPENROUTER_API_BASE,
        max_response_bytes: int = DEFAULT_MAX_RESPONSE_BYTES,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        transport: Optional[Transport] = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if not isinstance(api_key, str) or not api_key.strip():
            raise ContractError("OpenRouterConceptArtist requires a non-empty api_key")
        if not isinstance(model, str) or not model.strip():
            raise ContractError("OpenRouterConceptArtist requires a non-empty model")
        if not isinstance(api_base, str) or not api_base.startswith("https://"):
            raise ContractError(
                "OpenRouterConceptArtist api_base must be an HTTPS URL"
            )
        if (
            not isinstance(timeout_seconds, int)
            or isinstance(timeout_seconds, bool)
            or timeout_seconds <= 0
        ):
            raise ContractError(
                "OpenRouterConceptArtist timeout_seconds must be a positive integer"
            )
        if (
            not isinstance(max_attempts, int)
            or isinstance(max_attempts, bool)
            or max_attempts < 1
        ):
            raise ContractError(
                "OpenRouterConceptArtist max_attempts must be a positive integer"
            )
        self._api_key = api_key
        self._model = model
        self._api_base = api_base.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._max_attempts = max_attempts
        self._sleep = sleep
        self._transport = transport or make_urllib_transport(
            max_response_bytes, oversize_error=ConceptProviderError
        )

    @classmethod
    def from_env(
        cls, *, dotenv_path: Optional[str] = None, **overrides: Any
    ) -> "OpenRouterConceptArtist":
        """Build from environment variables, loading a ``.env`` file first.

        Reads ``OPENROUTER_API_KEY`` (required), and optionally
        ``OPENROUTER_IMAGE_MODEL`` / ``OPENROUTER_API_BASE``. A real
        environment variable always wins over one loaded from the file.
        Any keyword also accepted by the constructor may be passed to
        override what the environment supplies.
        """

        load_dotenv(dotenv_path)
        api_key = os.environ.get(ENV_OPENROUTER_API_KEY, "")
        if not api_key.strip():
            raise ContractError(
                "OpenRouterConceptArtist.from_env requires %s to be set"
                % ENV_OPENROUTER_API_KEY
            )
        kwargs: Dict[str, Any] = dict(overrides)
        model = os.environ.get(ENV_OPENROUTER_IMAGE_MODEL)
        if model and "model" not in kwargs:
            kwargs["model"] = model
        api_base = os.environ.get(ENV_OPENROUTER_API_BASE)
        if api_base and "api_base" not in kwargs:
            kwargs["api_base"] = api_base
        return cls(api_key, **kwargs)

    def __call__(self, request: ConceptImageRequest) -> str:
        if not isinstance(request, ConceptImageRequest):
            raise ContractError(
                "OpenRouterConceptArtist requires a ConceptImageRequest"
            )
        if len(request.references) > MAX_INPUT_REFERENCES:
            raise ConceptProviderError(
                "concept image %r references %d images, more than OpenRouter's "
                "%d-image limit per call"
                % (request.role, len(request.references), MAX_INPUT_REFERENCES)
            )
        payload: Dict[str, Any] = {
            "model": self._model,
            "prompt": request.prompt,
            "n": 1,
            "output_format": "png",
            "stream": False,
        }
        if request.references:
            payload["input_references"] = [
                self._encode_reference(path) for path in request.references
            ]
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": "Bearer %s" % self._api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        response = self._send(
            "POST", self._api_base + "/images", headers, body, request.role
        )
        image_bytes = self._extract_image(response, request.role)
        target = request.workspace / request.filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(image_bytes)
        return request.filename

    def _encode_reference(self, path: Path) -> Mapping[str, Any]:
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
        encoded = base64.b64encode(data).decode("ascii")
        return {
            "type": "image_url",
            "image_url": {"url": "data:%s;base64,%s" % (media_type, encoded)},
        }

    def _send(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: bytes,
        role: str,
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
                    "OpenRouter image request for %r failed with HTTP %d: %s"
                    % (role, response.status, _error_excerpt(response.body))
                )
            self._sleep(2.0 ** (attempt - 1))

    @staticmethod
    def _extract_image(response: HttpResponse, role: str) -> bytes:
        try:
            payload = json.loads(response.body.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise ConceptProviderError(
                "OpenRouter returned a non-JSON response for %r: %s" % (role, exc)
            ) from exc
        if not isinstance(payload, Mapping):
            raise ConceptProviderError(
                "OpenRouter returned a non-object response for %r" % role
            )
        data = payload.get("data")
        if (
            not isinstance(data, Sequence)
            or isinstance(data, (str, bytes))
            or not data
        ):
            raise ConceptProviderError("OpenRouter returned no image data for %r" % role)
        first = data[0]
        if not isinstance(first, Mapping) or not isinstance(
            first.get("b64_json"), str
        ):
            raise ConceptProviderError(
                "OpenRouter response for %r did not include b64_json image data"
                % role
            )
        try:
            return base64.b64decode(first["b64_json"], validate=True)
        except (ValueError, TypeError) as exc:
            raise ConceptProviderError(
                "OpenRouter returned malformed base64 image data for %r: %s"
                % (role, exc)
            ) from exc


__all__ = [
    "DEFAULT_MAX_RESPONSE_BYTES",
    "DEFAULT_MAX_ATTEMPTS",
    "DEFAULT_TIMEOUT_SECONDS",
    "ENV_OPENROUTER_API_BASE",
    "ENV_OPENROUTER_API_KEY",
    "ENV_OPENROUTER_IMAGE_MODEL",
    "MAX_INPUT_REFERENCES",
    "OPENROUTER_API_BASE",
    "OPENROUTER_IMAGE_MODEL",
    "OpenRouterConceptArtist",
]
