"""Narrow host-only production adapter for Concept image roles."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import stat
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Mapping, Optional, Sequence

from workshop._validation import require_sha256
from workshop.errors import ContractError, EffectError


PROFILE_KIND = "autonomous-workshop.concept-image-profile"
DEFAULT_PROFILE_ID = "openrouter-images-v1"
DEFAULT_ORIGIN = "https://openrouter.ai"
DEFAULT_MODEL = "openai/gpt-image-2"
DEFAULT_IMAGE_TIMEOUT_SECONDS = 180.0
MAX_IMAGE_BYTES = 24 * 1024 * 1024
MAX_REFERENCES = 8
MAX_REQUEST_BYTES = 64 * 1024 * 1024


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def _text(value: Any, label: str, maximum: int = 8_000) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or any(ord(c) < 32 and c not in "\n\t" for c in value):
        raise ContractError("%s must be bounded text" % label)
    return value


def sniff_image(content: bytes) -> str:
    if not isinstance(content, bytes) or not 1 <= len(content) <= MAX_IMAGE_BYTES:
        raise ContractError("Concept image bytes are empty or oversized")
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if content.startswith(b"RIFF") and len(content) >= 12 and content[8:12] == b"WEBP":
        return "image/webp"
    raise ContractError("Concept image content type is not permitted")


@dataclass(frozen=True)
class ConceptImageProfile:
    profile_id: str = DEFAULT_PROFILE_ID
    origin: str = DEFAULT_ORIGIN
    model: str = DEFAULT_MODEL
    request_schema_version: str = "openrouter-images-v1"
    supports_idempotency: bool = False
    supports_operation_readback: bool = False
    supports_absence_proof: bool = False
    kind: str = PROFILE_KIND
    profile_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if self.kind != PROFILE_KIND:
            raise ContractError("Concept image profile kind is invalid")
        _text(self.profile_id, "Concept image profile id", 128)
        parsed = urllib.parse.urlsplit(self.origin)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in ("", "/")
            or parsed.query
            or parsed.fragment
        ):
            raise ContractError("Concept image profile origin must be a pinned HTTPS origin")
        _text(self.model, "Concept image model", 256)
        _text(self.request_schema_version, "Concept image request schema", 128)
        for name in ("supports_idempotency", "supports_operation_readback", "supports_absence_proof"):
            if type(getattr(self, name)) is not bool:
                raise ContractError("Concept image provider capabilities must be boolean")
        object.__setattr__(self, "profile_sha256", hashlib.sha256(_canonical(self.identity())).hexdigest())

    def identity(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "profile_id": self.profile_id,
            "origin": self.origin,
            "model": self.model,
            "request_schema_version": self.request_schema_version,
            "supports_idempotency": self.supports_idempotency,
            "supports_operation_readback": self.supports_operation_readback,
            "supports_absence_proof": self.supports_absence_proof,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.identity(), "profile_sha256": self.profile_sha256}


@dataclass(frozen=True)
class ConceptImageReference:
    role: str
    sha256: str
    media_type: str
    content: bytes

    def __post_init__(self) -> None:
        _text(self.role, "Concept image reference role", 128)
        require_sha256(self.sha256, "Concept image reference sha256")
        if hashlib.sha256(self.content).hexdigest() != self.sha256 or sniff_image(self.content) != self.media_type:
            raise ContractError("Concept image reference differs from its exact bytes")


@dataclass(frozen=True)
class ConceptImageRequest:
    role: str
    instruction: str
    output_path: str
    idempotency_key: str
    references: tuple[ConceptImageReference, ...] = ()
    context: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "references", tuple(self.references))
        _text(self.role, "Concept image role", 128)
        _text(self.instruction, "Concept image instruction")
        _text(self.output_path, "Concept image output path", 512)
        _text(self.idempotency_key, "Concept image idempotency key", 128)
        output = PurePosixPath(self.output_path)
        if (
            output.is_absolute()
            or ".." in output.parts
            or not output.parts
            or output.parts[0] != "images"
            or output.as_posix() != self.output_path
        ):
            raise ContractError("Concept image output path is unsafe")
        if (
            len(self.references) > MAX_REFERENCES
            or any(not isinstance(item, ConceptImageReference) for item in self.references)
            or len({item.role for item in self.references}) != len(self.references)
        ):
            raise ContractError("Concept image references are excessive or duplicated")
        context = dict(self.context)
        try:
            encoded_context = _canonical(context)
        except (TypeError, ValueError, UnicodeError) as exc:
            raise ContractError("Concept image request context is invalid") from exc
        if len(encoded_context) > 32_000:
            raise ContractError("Concept image request context is oversized")
        object.__setattr__(self, "context", context)

    @property
    def provider_prompt(self) -> str:
        if not self.context:
            return self.instruction
        return _canonical(
            {"instruction": self.instruction, "context": self.context}
        ).decode("utf-8")


@dataclass(frozen=True)
class ConceptImageResponse:
    content: bytes
    media_type: str
    provider_operation_id: Optional[str] = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if sniff_image(self.content) != self.media_type:
            raise ContractError("Concept image response media type differs from its bytes")
        if self.provider_operation_id is not None:
            _text(self.provider_operation_id, "provider operation id", 512)
        try:
            encoded = _canonical(dict(self.metadata))
        except (TypeError, ValueError, UnicodeError) as exc:
            raise ContractError("Concept image provider metadata is invalid") from exc
        if len(encoded) > 4_096:
            raise ContractError("Concept image provider metadata is oversized")


@dataclass(frozen=True)
class ConceptImageReconciliation:
    status: str
    response: Optional[ConceptImageResponse] = None

    def __post_init__(self) -> None:
        if self.status not in ("succeeded", "absent", "unknown"):
            raise ContractError("Concept image reconciliation status is invalid")
        if (self.status == "succeeded") != isinstance(
            self.response, ConceptImageResponse
        ):
            raise ContractError("Concept image reconciliation response is invalid")


class ConceptImagePreTransmissionError(EffectError):
    pass


class ConceptImageRejected(EffectError):
    pass


class ConceptImageAmbiguous(EffectError):
    def __init__(self, message: str, *, provider_operation_id: Optional[str] = None) -> None:
        super().__init__(message)
        self.provider_operation_id = provider_operation_id


Transport = Callable[[str, Mapping[str, str], bytes, float], tuple[int, Mapping[str, str], bytes]]
Reconciler = Callable[
    [str, Mapping[str, str], float], ConceptImageReconciliation
]


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


def urllib_image_transport(url: str, headers: Mapping[str, str], body: bytes, timeout: float) -> tuple[int, Mapping[str, str], bytes]:
    request = urllib.request.Request(url, data=body, headers=dict(headers), method="POST")
    opener = urllib.request.build_opener(_NoRedirect())
    try:
        with opener.open(request, timeout=timeout) as response:
            content = response.read(4 * MAX_IMAGE_BYTES + 1)
            return int(response.status), dict(response.headers.items()), content
    except urllib.error.HTTPError as exc:
        return int(exc.code), dict(exc.headers.items()), exc.read(64 * 1024)
    except (TimeoutError, urllib.error.URLError, OSError) as exc:
        raise ConceptImageAmbiguous("Concept image transmission outcome is unknown") from exc


class OpenRouterConceptImageClient:
    def __init__(self, profile: ConceptImageProfile, api_key: str, *, transport: Transport = urllib_image_transport, reconciler: Optional[Reconciler] = None, timeout: float = DEFAULT_IMAGE_TIMEOUT_SECONDS) -> None:
        if not isinstance(profile, ConceptImageProfile):
            raise ContractError("Concept image client requires a profile")
        self.profile = profile
        self.api_key = _text(api_key, "Concept image API key", 8_192)
        self.transport = transport
        self.reconciler = reconciler
        if not isinstance(timeout, (int, float)) or not 1 <= timeout <= 300:
            raise ContractError("Concept image timeout is invalid")
        self.timeout = float(timeout)

    def render(self, request: ConceptImageRequest) -> ConceptImageResponse:
        if not isinstance(request, ConceptImageRequest):
            raise ContractError("Concept image client requires a bounded request")
        references = [
            {
                "type": "image_url",
                "image_url": {
                    "url": "data:%s;base64,%s" % (
                        item.media_type,
                        base64.b64encode(item.content).decode("ascii"),
                    ),
                },
            }
            for item in request.references
        ]
        payload = {
            "model": self.profile.model,
            "prompt": request.provider_prompt,
            "n": 1,
            "input_references": references,
        }
        encoded_payload = _canonical(payload)
        if len(encoded_payload) > MAX_REQUEST_BYTES:
            raise ConceptImageRejected("Concept image request is oversized")
        headers = {"Authorization": "Bearer %s" % self.api_key, "Content-Type": "application/json"}
        if self.profile.supports_idempotency:
            headers["Idempotency-Key"] = request.idempotency_key
        url = self.profile.origin.rstrip("/") + "/api/v1/images"
        try:
            status, response_headers, body = self.transport(url, headers, encoded_payload, self.timeout)
        except ConceptImageAmbiguous:
            raise
        except Exception as exc:
            raise ConceptImagePreTransmissionError("Concept image request failed before transmission") from exc
        if (
            type(status) is not int
            or not isinstance(response_headers, Mapping)
            or not isinstance(body, bytes)
        ):
            raise ConceptImageRejected("Concept image transport response is malformed")
        if 300 <= status < 400:
            raise ConceptImageRejected("Concept image provider redirect was refused")
        if status < 200 or status >= 300:
            raise ConceptImageRejected("Concept image provider rejected role %s" % request.role)
        if len(body) > 4 * MAX_IMAGE_BYTES:
            raise ConceptImageRejected("Concept image provider response is oversized")
        try:
            value = json.loads(body.decode("utf-8"))
            data = value["data"]
            if (
                not isinstance(data, list)
                or len(data) != 1
                or not isinstance(data[0], Mapping)
                or set(data[0])
                - {"b64_json", "id", "media_type", "revised_prompt"}
                or not isinstance(data[0].get("b64_json"), str)
            ):
                raise ValueError("invalid image count")
            content = base64.b64decode(data[0]["b64_json"], validate=True)
        except (KeyError, TypeError, ValueError, UnicodeError, json.JSONDecodeError) as exc:
            raise ConceptImageRejected("Concept image provider returned malformed output") from exc
        media_type = sniff_image(content)
        declared_media_type = data[0].get("media_type")
        if declared_media_type is not None and declared_media_type != media_type:
            raise ConceptImageRejected(
                "Concept image provider media type differs from its bytes"
            )
        operation_id = data[0].get("id") or response_headers.get("x-request-id")
        return ConceptImageResponse(
            content=content,
            media_type=media_type,
            provider_operation_id=operation_id,
            metadata={"status": status},
        )

    def reconcile(
        self, provider_operation_id: str
    ) -> ConceptImageReconciliation:
        _text(provider_operation_id, "provider operation id", 512)
        if not self.profile.supports_operation_readback or self.reconciler is None:
            return ConceptImageReconciliation("unknown")
        result = self.reconciler(
            provider_operation_id,
            {"Authorization": "Bearer %s" % self.api_key},
            self.timeout,
        )
        if not isinstance(result, ConceptImageReconciliation):
            raise ConceptImageRejected("Concept image reconciliation is malformed")
        if result.status == "absent" and not self.profile.supports_absence_proof:
            raise ConceptImageRejected(
                "Concept image provider cannot authenticate absence"
            )
        return result


def load_concept_image_credentials(path_value: Optional[str] = None, *, transport: Transport = urllib_image_transport) -> OpenRouterConceptImageClient:
    raw = path_value if path_value is not None else os.environ.get("WORKSHOP_CONCEPT_IMAGE_CREDENTIALS_FILE")
    if not isinstance(raw, str) or not raw or not Path(raw).is_absolute():
        raise ContractError("Concept image credentials file is not configured")
    path = Path(raw)
    identity = path.lstat()
    if path.is_symlink() or not stat.S_ISREG(identity.st_mode) or stat.S_IMODE(identity.st_mode) != 0o600:
        raise ContractError("Concept image credentials must be a private regular file")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or set(value) != {"schema_version", "profile", "api_key"} or value["schema_version"] != 1:
        raise ContractError("Concept image credentials fields are invalid")
    profile_value = value["profile"]
    if not isinstance(profile_value, dict):
        raise ContractError("Concept image profile is invalid")
    profile = ConceptImageProfile(**profile_value)
    return OpenRouterConceptImageClient(profile, value["api_key"], transport=transport)


__all__ = [
    "ConceptImageAmbiguous", "ConceptImagePreTransmissionError", "ConceptImageProfile",
    "ConceptImageReconciliation",
    "ConceptImageReference", "ConceptImageRejected", "ConceptImageRequest",
    "ConceptImageResponse", "DEFAULT_IMAGE_TIMEOUT_SECONDS",
    "OpenRouterConceptImageClient", "load_concept_image_credentials",
    "sniff_image", "urllib_image_transport",
]
