"""Host-side transport for a concept's agent-authored drawing instructions.

Concept Codex sessions run with the sandbox network disabled, so drawing an
image happens on the host, between turns.  This adapter composes nothing: it
sends each authored drawing instruction verbatim, attaches the references the
concept named in order as inline bytes, and writes back exactly the bytes the
provider returned.  It assumes no vendor, model, or endpoint — configuration
is supplied explicitly by the caller.
"""

from __future__ import annotations

import base64
import hashlib
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Optional, Sequence

from workshop.concept.native import ConceptTree, NativeConcept, OVERALL_IMAGE_ROLES
from workshop.errors import ContractError, EffectError


MAX_RESPONSE_BYTES = 16 * 1024 * 1024
MAX_REFERENCES = 8
DEFAULT_TIMEOUT_SECONDS = 60.0
DEFAULT_MAX_RETRY_ATTEMPTS = 3
_RETRY_BACKOFF_SECONDS = 2.0
_RETRYABLE_STATUS_CODES = frozenset((408, 429, 500, 502, 503, 504))
_COMPONENT_REFERENCES = ("front",)
_OVERALL_REFERENCES = {
    "front": (),
    "top": ("front",),
    "bottom": ("front",),
    "exploded": ("front", "top", "bottom"),
}


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


@dataclass(frozen=True)
class ConceptImagesConfig:
    """Explicit provider configuration. Construction fails without one."""

    endpoint: str
    api_key: str
    model: str
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    max_retry_attempts: int = DEFAULT_MAX_RETRY_ATTEMPTS

    def __post_init__(self) -> None:
        if not isinstance(self.endpoint, str) or not self.endpoint.startswith("https://"):
            raise ContractError(
                "concept image provider endpoint must be an explicit https URL"
            )
        if not isinstance(self.api_key, str) or not self.api_key:
            raise ContractError("concept image provider api_key is required")
        if not isinstance(self.model, str) or not self.model:
            raise ContractError("concept image provider model is required")
        if not isinstance(self.timeout_seconds, (int, float)) or self.timeout_seconds <= 0:
            raise ContractError("concept image provider timeout_seconds must be positive")
        if (
            not isinstance(self.max_retry_attempts, int)
            or isinstance(self.max_retry_attempts, bool)
            or self.max_retry_attempts < 1
        ):
            raise ContractError(
                "concept image provider max_retry_attempts must be a positive integer"
            )


class ConceptImageDrawError(EffectError):
    """A required role's image could not be drawn."""

    def __init__(self, role: str, reason: str) -> None:
        super().__init__("concept image role %s failed: %s" % (role, reason))
        self.role = role


def _draw_order(tree: ConceptTree) -> list[tuple[str, str, tuple[str, ...], str]]:
    """Return (role, instruction, reference_roles, image_path) in draw order."""

    order: list[tuple[str, str, tuple[str, ...], str]] = []
    descriptor = tree.descriptor
    instructions = tree.drawing_instructions
    for role in OVERALL_IMAGE_ROLES:
        order.append(
            (
                role,
                instructions[role]["instruction"],
                _OVERALL_REFERENCES[role],
                descriptor[role]["path"],
            )
        )
    component_keys = sorted(item["key"] for item in tree.brief["components"])
    for key in component_keys:
        order.append(
            (
                "components.%s" % key,
                instructions["components"][key]["instruction"],
                _COMPONENT_REFERENCES,
                descriptor["components"][key]["path"],
            )
        )
    return order


class ConceptImagesAdapter:
    """Draws one concept's complete image set, never composing a request."""

    def __init__(
        self,
        config: ConceptImagesConfig,
        *,
        opener: Optional[Callable[[urllib.request.Request, float], object]] = None,
    ) -> None:
        if not isinstance(config, ConceptImagesConfig):
            raise ContractError(
                "concept image adapter requires an explicit ConceptImagesConfig"
            )
        self._config = config
        self._opener = opener or urllib.request.urlopen

    def draw_concept(self, tree: ConceptTree, concept: NativeConcept) -> dict[str, str]:
        """Draw every required role in order, skipping roles already written.

        Returns a mapping of role -> sha256 for images this call newly wrote,
        so a resumed draw after a credential wait never redraws or pays for a
        role whose file the descriptor already binds correctly.
        """

        order = _draw_order(tree)
        drawn: dict[str, str] = {}
        images: dict[str, bytes] = {}
        for role, instruction, references, relative_path in order:
            destination = tree.root / relative_path
            existing = self._existing_bytes(destination, role)
            if existing is not None:
                images[role] = existing
                continue
            missing = [reference for reference in references if reference not in images]
            if missing:
                raise ConceptImageDrawError(
                    role, "a required reference role was never drawn: %s" % missing
                )
            reference_bytes = [images[reference] for reference in references]
            if len(reference_bytes) > MAX_REFERENCES:
                raise ConceptImageDrawError(
                    role,
                    "reference count %d exceeds the provider's limit of %d"
                    % (len(reference_bytes), MAX_REFERENCES),
                )
            image_bytes = self._draw_one(role, instruction, reference_bytes)
            self._write_role(destination, role, image_bytes)
            images[role] = image_bytes
            drawn[role] = _sha256(image_bytes)
        return drawn

    def _existing_bytes(self, destination: Path, role: str) -> Optional[bytes]:
        if destination.is_symlink() or not destination.is_file():
            return None
        try:
            return destination.read_bytes()
        except OSError as exc:
            raise ConceptImageDrawError(
                role, "an already-written image could not be read"
            ) from exc

    def _write_role(self, destination: Path, role: str, content: bytes) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(destination, "xb") as stream:
                stream.write(content)
        except FileExistsError:
            existing = destination.read_bytes()
            if existing != content:
                raise ConceptImageDrawError(
                    role, "the image path was written with different bytes"
                ) from None
        except OSError as exc:
            raise ConceptImageDrawError(role, "the drawn image could not be written") from exc

    def _draw_one(
        self, role: str, instruction: str, references: Sequence[bytes]
    ) -> bytes:
        payload_document: dict[str, object] = {
            "model": self._config.model,
            "prompt": instruction,
        }
        if references:
            payload_document["input_references"] = [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/png;base64,%s"
                        % base64.b64encode(reference).decode("ascii")
                    },
                }
                for reference in references
            ]
        payload = json.dumps(payload_document).encode("utf-8")
        request = urllib.request.Request(
            self._config.endpoint,
            data=payload,
            method="POST",
            headers={
                "Authorization": "Bearer %s" % self._config.api_key,
                "Content-Type": "application/json",
            },
        )
        last_reason = "no attempt was made"
        for attempt in range(1, self._config.max_retry_attempts + 1):
            try:
                with self._opener(
                    request, timeout=self._config.timeout_seconds
                ) as response:
                    status = getattr(response, "status", 200)
                    body = response.read(MAX_RESPONSE_BYTES + 1)
            except urllib.error.HTTPError as exc:
                status = exc.code
                body = exc.read(MAX_RESPONSE_BYTES + 1) if hasattr(exc, "read") else b""
                if status not in _RETRYABLE_STATUS_CODES:
                    raise ConceptImageDrawError(
                        role, "provider returned non-retryable status %d" % status
                    ) from exc
                last_reason = "provider returned retryable status %d" % status
                if attempt < self._config.max_retry_attempts:
                    time.sleep(_RETRY_BACKOFF_SECONDS * attempt)
                    continue
                raise ConceptImageDrawError(role, last_reason) from exc
            except urllib.error.URLError as exc:
                last_reason = "transport error: %s" % exc.reason
                if attempt < self._config.max_retry_attempts:
                    time.sleep(_RETRY_BACKOFF_SECONDS * attempt)
                    continue
                raise ConceptImageDrawError(role, last_reason) from exc
            if len(body) > MAX_RESPONSE_BYTES:
                raise ConceptImageDrawError(
                    role, "response exceeds the configured maximum size"
                )
            if status in _RETRYABLE_STATUS_CODES:
                last_reason = "provider returned retryable status %d" % status
                if attempt < self._config.max_retry_attempts:
                    time.sleep(_RETRY_BACKOFF_SECONDS * attempt)
                    continue
                raise ConceptImageDrawError(role, last_reason)
            return self._extract_image(role, status, body)
        raise ConceptImageDrawError(role, last_reason)

    def _extract_image(self, role: str, status: int, body: bytes) -> bytes:
        if status != 200:
            raise ConceptImageDrawError(role, "provider returned status %d" % status)
        try:
            document = json.loads(body.decode("utf-8"))
        except (UnicodeError, ValueError) as exc:
            raise ConceptImageDrawError(
                role, "response is not valid JSON"
            ) from exc
        if not isinstance(document, dict):
            raise ConceptImageDrawError(role, "response is not a JSON object")
        encoded = document.get("image_base64")
        if encoded is None:
            images = document.get("data")
            if isinstance(images, list) and len(images) == 1:
                image = images[0]
                if isinstance(image, dict):
                    encoded = image.get("b64_json")
        if not isinstance(encoded, str) or not encoded:
            raise ConceptImageDrawError(role, "response contains no image data")
        try:
            image_bytes = base64.b64decode(encoded, validate=True)
        except (ValueError, TypeError) as exc:
            raise ConceptImageDrawError(
                role, "response image data is not valid base64"
            ) from exc
        if not image_bytes:
            raise ConceptImageDrawError(role, "response contains no image data")
        return image_bytes


__all__ = [
    "ConceptImageDrawError",
    "ConceptImagesAdapter",
    "ConceptImagesConfig",
    "DEFAULT_MAX_RETRY_ATTEMPTS",
    "DEFAULT_TIMEOUT_SECONDS",
    "MAX_REFERENCES",
    "MAX_RESPONSE_BYTES",
]
