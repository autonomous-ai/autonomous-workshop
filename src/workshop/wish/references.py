"""Read reference image files into Wish references plus their exact bytes.

Pillow decodes only the header (``Image.open`` + ``verify``), so a hostile file
cannot allocate a full-size bitmap here; the pixel and side limits are checked
before anyone decodes the image for real.
"""

from __future__ import annotations

import hashlib
import io
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Sequence, Union

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


@dataclass(frozen=True)
class LoadedWishReference:
    reference: WishReference
    content: bytes


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
        path = Path(raw)
        display = path.name or str(path)
        if not path.is_file():
            raise ContractError("reference image is not a readable file: %s" % display)
        size = path.stat().st_size
        if size == 0:
            raise ContractError("reference image is empty: %s" % display)
        if size > MAX_WISH_REFERENCE_BYTES:
            raise ContractError(
                "reference image %s exceeds %d bytes" % (display, MAX_WISH_REFERENCE_BYTES)
            )
        content = path.read_bytes()
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
            _slug(path.stem),
            WISH_REFERENCE_MEDIA_TYPES[media_type],
        )
        reference = WishReference(name, digest, media_type, size, width, height)
        seen[digest] = display
        loaded.append(LoadedWishReference(reference, content))
    return tuple(loaded)


def wish_reference_files(loaded: Sequence[LoadedWishReference]) -> Dict[str, bytes]:
    """Map each reference name to its exact bytes for the run host."""

    files: Dict[str, bytes] = {}
    for item in loaded:
        if not isinstance(item, LoadedWishReference):
            raise ContractError("wish reference files require loaded references")
        files[item.reference.name] = item.content
    return files


__all__ = ["LoadedWishReference", "load_wish_references", "wish_reference_files"]
