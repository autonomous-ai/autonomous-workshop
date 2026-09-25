"""Generate one concept-art image via OpenRouter for brainstorm-reskin.

Each of the five personality subagents in the brainstorm-reskin skill calls
this once, blind to the others, to render its Design Contract's ``signature``
component. The call is deterministic tooling, not a model judgement: it
builds one image-generation request, decodes and bounds the one image the
response carries, and writes it to disk. Everything about *whether* the image
is any good — subject, composition, theme — is the personality's prompt, not
this script's job to judge; this script only enforces what
``design-a-toy`` Stage 3 requires of any reference image: 800x800 or
smaller, PNG/JPEG/WebP, a single readable frame.

Credentials come from a ``.env`` file (``OPENROUTER_API_KEY`` and
``OPENROUTER_IMAGE_MODEL``, one ``NAME=value`` line each) or the process
environment, which wins when set. The key is never written to a log, an
exception message, or a ``repr()`` — only :class:`OpenRouterConfig` ever
holds it, and printing that value is redacted.
"""

from __future__ import annotations

import base64
import binascii
import io
import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Mapping, Optional

MAX_IMAGE_SIDE_PX = 800
MAX_IMAGE_BYTES = 12 * 1024 * 1024
MAX_RESPONSE_BYTES = 16 * 1024 * 1024
MAX_PROMPT_CHARS = 8_000
HTTP_TIMEOUT_SECONDS = 180
OPENROUTER_CHAT_COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"
USER_AGENT = "brainstorm-reskin/openrouter-image"

OPENROUTER_API_KEY_NAME = "OPENROUTER_API_KEY"
OPENROUTER_IMAGE_MODEL_NAME = "OPENROUTER_IMAGE_MODEL"
MAX_API_KEY_CHARS = 512
MAX_MODEL_NAME_CHARS = 256

_PILLOW_FORMATS: Dict[str, str] = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}
_MEDIA_EXTENSIONS: Dict[str, str] = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}
_DATA_URL = re.compile(r"^data:(?P<media_type>image/(?:png|jpeg|webp));base64,(?P<data>.+)$", re.DOTALL)
_ENV_LINE = re.compile(r"^(?P<name>[A-Za-z_][A-Za-z0-9_]*)=(?P<value>.*)$")


class OpenRouterError(RuntimeError):
    """A ``.env``/environment value was unusable, or OpenRouter's answer was."""


@dataclass(frozen=True)
class OpenRouterConfig:
    """The two values this script needs; nothing here should ever be logged."""

    api_key: str
    model: str

    def __repr__(self) -> str:
        return "OpenRouterConfig(api_key=<redacted>, model=%r)" % self.model

    def __str__(self) -> str:
        return repr(self)


@dataclass(frozen=True)
class GeneratedImage:
    path: Path
    model: str
    media_type: str
    size: int
    width: int
    height: int


@dataclass(frozen=True)
class HttpResponse:
    status: int
    content: bytes


# (url, headers, body) -> response. The only test seam: replace outbound HTTP.
Transport = Callable[[str, Mapping[str, str], bytes], HttpResponse]


def _urllib_transport(url: str, headers: Mapping[str, str], body: bytes) -> HttpResponse:
    request = urllib.request.Request(url, method="POST", data=body)
    for name, value in headers.items():
        request.add_header(name, value)
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            content = response.read(MAX_RESPONSE_BYTES + 1)
            if len(content) > MAX_RESPONSE_BYTES:
                raise OpenRouterError("OpenRouter response exceeds the size limit")
            return HttpResponse(response.status, content)
    except urllib.error.HTTPError as exc:
        content = exc.read(MAX_RESPONSE_BYTES + 1)
        return HttpResponse(exc.code, content[:MAX_RESPONSE_BYTES])
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        # str(exc) here is a socket/DNS reason, never anything we sent.
        raise OpenRouterError("OpenRouter is unreachable: %s" % exc) from exc


def parse_env_file(path: Path) -> Dict[str, str]:
    """Parse bounded ``NAME=value`` lines; blank lines and ``#`` comments skip."""

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise OpenRouterError("could not read env file: %s" % path) from exc
    values: Dict[str, str] = {}
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = _ENV_LINE.match(line)
        if match is None:
            raise OpenRouterError("%s line %d is malformed" % (path, line_number))
        values[match.group("name")] = match.group("value")
    return values


def load_openrouter_config(
    env_path: Path,
    environment: Optional[Mapping[str, str]] = None,
) -> OpenRouterConfig:
    """Resolve the API key and image model; a process value wins over the file.

    Neither value is echoed into the raised message: a missing key names only
    the variable, never a partial value.
    """

    file_values = parse_env_file(env_path) if env_path.is_file() else {}
    process_values = environment or {}

    def resolve(name: str, max_chars: int) -> str:
        value = process_values.get(name) or file_values.get(name)
        if not value or not isinstance(value, str) or not value.strip():
            raise OpenRouterError("%s is not set" % name)
        if len(value) > max_chars:
            raise OpenRouterError("%s is too long" % name)
        return value

    api_key = resolve(OPENROUTER_API_KEY_NAME, MAX_API_KEY_CHARS)
    model = resolve(OPENROUTER_IMAGE_MODEL_NAME, MAX_MODEL_NAME_CHARS)
    return OpenRouterConfig(api_key=api_key, model=model)


def _decode_image(content: bytes) -> tuple[str, bytes]:
    try:
        payload = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OpenRouterError("OpenRouter response was not valid JSON") from exc
    try:
        url = payload["choices"][0]["message"]["images"][0]["image_url"]["url"]
    except (KeyError, IndexError, TypeError) as exc:
        raise OpenRouterError("OpenRouter response carried no image") from exc
    match = _DATA_URL.match(url) if isinstance(url, str) else None
    if match is None:
        raise OpenRouterError("OpenRouter image was not an inline data URL")
    try:
        data = base64.b64decode(match.group("data"), validate=True)
    except (ValueError, binascii.Error) as exc:
        raise OpenRouterError("OpenRouter image was not valid base64") from exc
    return match.group("media_type"), data


def generate_image(
    prompt: str,
    output_path: Path,
    *,
    config: OpenRouterConfig,
    transport: Optional[Transport] = None,
) -> GeneratedImage:
    """Request one image from OpenRouter and write it to ``output_path``.

    The prompt is the caller's whole job: it is what tells the model to draw
    exactly one subject fully inside the frame, per design-a-toy Stage 3.
    This function only bounds what comes back — 800x800 or smaller, a
    readable PNG/JPEG/WebP, one still frame — the same shape
    ``load_wish_references`` requires of any reference image.
    """

    if not isinstance(prompt, str) or not prompt.strip():
        raise OpenRouterError("prompt must be non-empty text")
    if len(prompt) > MAX_PROMPT_CHARS:
        raise OpenRouterError("prompt exceeds %d characters" % MAX_PROMPT_CHARS)
    if not isinstance(config, OpenRouterConfig):
        raise OpenRouterError("generate_image requires an OpenRouterConfig")

    send = transport or _urllib_transport
    body = json.dumps(
        {
            "model": config.model,
            "messages": [{"role": "user", "content": prompt}],
            "modalities": ["image", "text"],
        }
    ).encode("utf-8")
    headers = {
        "Authorization": "Bearer %s" % config.api_key,
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }
    response = send(OPENROUTER_CHAT_COMPLETIONS_URL, headers, body)
    if response.status != 200:
        # The body may echo the request but never the Authorization header,
        # so this is safe to surface; still cap it well under the API's own
        # error-body size.
        detail = response.content[:2000].decode("utf-8", errors="replace")
        raise OpenRouterError("OpenRouter returned HTTP %d: %s" % (response.status, detail))

    media_type, image_bytes = _decode_image(response.content)
    if not image_bytes:
        raise OpenRouterError("OpenRouter image was empty")
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise OpenRouterError("OpenRouter image exceeds %d bytes" % MAX_IMAGE_BYTES)

    from PIL import Image, UnidentifiedImageError

    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            image_format = image.format
            width, height = image.size
            frames = getattr(image, "n_frames", 1)
            image.verify()
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError) as exc:
        raise OpenRouterError("OpenRouter image is not a readable PNG, JPEG, or WebP") from exc

    resolved_media_type = _PILLOW_FORMATS.get(image_format or "")
    if resolved_media_type != media_type:
        raise OpenRouterError(
            "OpenRouter image format mismatch (declared %s, decoded %s)"
            % (media_type, image_format or "unknown")
        )
    if frames != 1:
        raise OpenRouterError("OpenRouter image must not be animated")
    if width > MAX_IMAGE_SIDE_PX or height > MAX_IMAGE_SIDE_PX:
        raise OpenRouterError(
            "OpenRouter image is %dx%d, over the %dx%d limit"
            % (width, height, MAX_IMAGE_SIDE_PX, MAX_IMAGE_SIDE_PX)
        )
    if width < 1 or height < 1:
        raise OpenRouterError("OpenRouter image has no pixels")

    extension = _MEDIA_EXTENSIONS[resolved_media_type]
    if output_path.suffix.lstrip(".").lower() != extension:
        output_path = output_path.with_suffix("." + extension)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(image_bytes)

    return GeneratedImage(
        path=output_path,
        model=config.model,
        media_type=resolved_media_type,
        size=len(image_bytes),
        width=width,
        height=height,
    )


__all__ = [
    "GeneratedImage",
    "HttpResponse",
    "MAX_IMAGE_SIDE_PX",
    "OPENROUTER_API_KEY_NAME",
    "OPENROUTER_IMAGE_MODEL_NAME",
    "OpenRouterConfig",
    "OpenRouterError",
    "Transport",
    "generate_image",
    "load_openrouter_config",
    "parse_env_file",
]
