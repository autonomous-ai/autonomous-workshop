"""Read reference images, local files or http(s) links, into Wish references.

Each reference ends as exact bytes plus a ``WishReference`` bound by size and
SHA-256, whatever its origin. A link is downloaded once here, at Wish time,
under a byte cap and a timeout, and then goes through the same checks as a
file; the run never sees the URL as an input, only the bytes. Pillow decodes
only the header (``Image.open`` + ``verify``), so a hostile file cannot
allocate a full-size bitmap here; the pixel and side limits are checked before
anyone decodes the image for real.
"""

from __future__ import annotations

import hashlib
import io
import re
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Callable, Dict, Sequence, Union

from workshop.errors import ContractError
from workshop.wish.contracts import (
    MAX_WISH_REFERENCE_BYTES,
    MAX_WISH_REFERENCE_PIXELS,
    MAX_WISH_REFERENCE_TOTAL_BYTES,
    MAX_WISH_REFERENCES,
    MAX_WISH_REFERENCE_SIDE_PX,
    MIN_WISH_REFERENCE_SIDE_PX,
    WISH_REFERENCE_MEDIA_TYPES,
    WishReference,
)

_PILLOW_FORMATS = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}
_MAX_SLUG_CHARS = 40
_URL_SCHEMES = ("http", "https")
WISH_REFERENCE_FETCH_TIMEOUT_SECONDS = 30
_USER_AGENT = "autonomous-workshop/wish-reference"


@dataclass(frozen=True)
class LoadedWishReference:
    reference: WishReference
    content: bytes
    source: str = ""
    """The path or URL the bytes came from, exactly as the person gave it."""

    @property
    def downloaded(self) -> bool:
        return is_reference_url(self.source)


def is_reference_url(value: object) -> bool:
    """True for an ``http://`` or ``https://`` link; a ``Path`` is never one."""

    if not isinstance(value, str):
        return False
    return urllib.parse.urlsplit(value).scheme.lower() in _URL_SCHEMES


class _HttpOnlyRedirects(urllib.request.HTTPRedirectHandler):
    """Follow redirects only to http(s); a hop to file:, ftp:, or data: fails."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        target = urllib.parse.urljoin(req.full_url, newurl)
        if urllib.parse.urlsplit(target).scheme.lower() not in _URL_SCHEMES:
            raise urllib.error.URLError("redirect to a non-http location refused")
        return super().redirect_request(req, fp, code, msg, headers, target)


def _urllib_fetch(url: str) -> bytes:
    """Download at most one byte over the cap so the size rule can reject it."""

    limit = MAX_WISH_REFERENCE_BYTES + 1
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        opener = urllib.request.build_opener(_HttpOnlyRedirects())
        with opener.open(request, timeout=WISH_REFERENCE_FETCH_TIMEOUT_SECONDS) as response:
            declared = response.headers.get("Content-Length")
            if declared is not None and declared.isdigit() and int(declared) > MAX_WISH_REFERENCE_BYTES:
                raise ContractError(
                    "reference image %s exceeds %d bytes" % (url, MAX_WISH_REFERENCE_BYTES)
                )
            return response.read(limit)
    except urllib.error.HTTPError as exc:
        if 300 <= exc.code < 400:
            # urllib refuses a redirect off http(s) before our handler sees it.
            raise ContractError(
                "reference image link redirected to a location the Workshop will not "
                "follow: %s" % url
            ) from exc
        raise ContractError(
            "reference image link returned HTTP %d: %s" % (exc.code, url)
        ) from exc
    except (urllib.error.URLError, OSError, TimeoutError, ValueError) as exc:
        reason = getattr(exc, "reason", None) or exc
        raise ContractError(
            "reference image could not be downloaded: %s (%s)" % (url, reason)
        ) from exc


# The only test seam: replace the download, keep every validation rule.
_FETCH: Callable[[str], bytes] = _urllib_fetch


def _url_stem(url: str) -> str:
    """The last path segment of a link, without its extension or query."""

    path = urllib.parse.unquote(urllib.parse.urlsplit(url).path)
    return PurePosixPath(path).stem


def _slug(stem: str) -> str:
    ascii_stem = (
        unicodedata.normalize("NFKD", stem).encode("ascii", "ignore").decode("ascii")
    )
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_stem.lower()).strip("-")
    slug = slug[:_MAX_SLUG_CHARS].strip("-")
    return slug or "image"


def load_wish_references(
    paths: Sequence[Union[str, Path]],
) -> tuple[LoadedWishReference, ...]:
    """Validate reference image files in the order given and name them ref-NN."""

    if isinstance(paths, (str, bytes, Path)):
        raise ContractError("reference image paths must be a list")
    if len(paths) > MAX_WISH_REFERENCES:
        raise ContractError("a Wish may attach at most %d reference images" % MAX_WISH_REFERENCES)
    if not paths:
        return ()
    from PIL import Image, UnidentifiedImageError

    loaded: list[LoadedWishReference] = []
    seen: Dict[str, str] = {}
    total = 0
    for position, raw in enumerate(paths, start=1):
        if is_reference_url(raw):
            source = str(raw)
            display = source
            stem = _url_stem(source)
            content = _FETCH(source)
        else:
            path = Path(raw)
            source = str(raw)
            display = path.name or str(path)
            stem = path.stem
            if not path.is_file():
                raise ContractError("reference image is not a readable file: %s" % display)
            content = path.read_bytes()
        size = len(content)
        if size == 0:
            raise ContractError("reference image is empty: %s" % display)
        if size > MAX_WISH_REFERENCE_BYTES:
            raise ContractError(
                "reference image %s exceeds %d bytes" % (display, MAX_WISH_REFERENCE_BYTES)
            )
        digest = hashlib.sha256(content).hexdigest()
        if digest in seen:
            raise ContractError(
                "reference image %s repeats the bytes of %s" % (display, seen[digest])
            )
        try:
            with Image.open(io.BytesIO(content)) as image:
                image_format = image.format
                width, height = image.size
                frames = getattr(image, "n_frames", 1)
                image.verify()
        except (UnidentifiedImageError, OSError, ValueError, SyntaxError) as exc:
            raise ContractError(
                "reference image %s is not a readable PNG, JPEG, or WebP" % display
            ) from exc
        media_type = _PILLOW_FORMATS.get(image_format or "")
        if media_type is None:
            raise ContractError(
                "reference image %s must be PNG, JPEG, or WebP (got %s)"
                % (display, image_format or "unknown")
            )
        if frames != 1:
            raise ContractError("reference image %s must not be animated" % display)
        if (
            not MIN_WISH_REFERENCE_SIDE_PX <= width <= MAX_WISH_REFERENCE_SIDE_PX
            or not MIN_WISH_REFERENCE_SIDE_PX <= height <= MAX_WISH_REFERENCE_SIDE_PX
            or width * height > MAX_WISH_REFERENCE_PIXELS
        ):
            raise ContractError(
                "reference image %s must be %d-%d px per side and at most %d pixels"
                % (
                    display,
                    MIN_WISH_REFERENCE_SIDE_PX,
                    MAX_WISH_REFERENCE_SIDE_PX,
                    MAX_WISH_REFERENCE_PIXELS,
                )
            )
        total += size
        if total > MAX_WISH_REFERENCE_TOTAL_BYTES:
            raise ContractError(
                "reference images together exceed %d bytes" % MAX_WISH_REFERENCE_TOTAL_BYTES
            )
        name = "ref-%02d-%s.%s" % (
            position,
            _slug(stem),
            WISH_REFERENCE_MEDIA_TYPES[media_type],
        )
        reference = WishReference(name, digest, media_type, size, width, height)
        seen[digest] = display
        loaded.append(LoadedWishReference(reference, content, source))
    return tuple(loaded)


def wish_reference_files(loaded: Sequence[LoadedWishReference]) -> Dict[str, bytes]:
    """Map each reference name to its exact bytes for the run host."""

    files: Dict[str, bytes] = {}
    for item in loaded:
        if not isinstance(item, LoadedWishReference):
            raise ContractError("wish reference files require loaded references")
        files[item.reference.name] = item.content
    return files


def wish_reference_sources(loaded: Sequence[LoadedWishReference]) -> Dict[str, str]:
    """Map each downloaded reference name to the link it came from.

    Local files are left out: their paths are the person's machine layout,
    not provenance worth sealing. The map goes into the Wish context so a
    reader of ``WISH.json`` knows where a reference's bytes were fetched; the
    bytes stay bound by SHA-256 regardless of what the link serves later.
    """

    sources: Dict[str, str] = {}
    for item in loaded:
        if not isinstance(item, LoadedWishReference):
            raise ContractError("wish reference sources require loaded references")
        if item.downloaded:
            sources[item.reference.name] = item.source
    return sources


__all__ = [
    "LoadedWishReference",
    "WISH_REFERENCE_FETCH_TIMEOUT_SECONDS",
    "is_reference_url",
    "load_wish_references",
    "wish_reference_files",
    "wish_reference_sources",
]
