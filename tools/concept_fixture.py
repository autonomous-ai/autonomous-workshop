"""A deterministic fixture concept artist. NOT a concept image provider.

This repo has no image model, and an STL does not exist at Concept time, so the
shipped Concept job waits truthfully for a real provider. Tests and the showcase
builder still need the pipeline to run end to end, so this module draws tiny
synthetic PNGs from the brief instead.

What it produces is a swatch, not a picture of anything. It is deliberately kept
out of ``src/`` so it can never be installed or wired into a real Workshop, and
nothing here should be read as evidence that a design was visualized.

The one thing it does honestly: the exploded swatch carries one colour band per
component, and :func:`fixture_explode_inspector` reads those bands back out of
the file. That makes the exploded-view completeness check a real check over real
bytes in tests, rather than a stub that always agrees.
"""

from __future__ import annotations

import hashlib
import struct
import zlib
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from inventor_workshop.concept import ConceptImageRequest
from inventor_workshop.jobs import ConceptBrief


FIXTURE_MARK = "workshop-concept-fixture"
_SWATCH_WIDTH = 8


def _colour(seed: str) -> Tuple[int, int, int]:
    digest = hashlib.sha256((FIXTURE_MARK + "/" + seed).encode("utf-8")).digest()
    # Keep every channel clear of black and white so bands stay distinguishable.
    return tuple(24 + (value % 200) for value in digest[:3])  # type: ignore[return-value]


def component_colour(key: str) -> Tuple[int, int, int]:
    """The band colour that identifies one component in an exploded swatch."""

    return _colour("component/" + key)


def _write_png(path: Path, rows: Sequence[Tuple[int, int, int]]) -> None:
    raw = b"".join(
        b"\x00" + bytes(channel for _ in range(_SWATCH_WIDTH) for channel in row)
        for row in rows
    )

    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        )

    header = struct.pack(">IIBBBBB", _SWATCH_WIDTH, len(rows), 8, 2, 0, 0, 0)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


def _read_png_rows(path: Path) -> List[Tuple[int, int, int]]:
    data = Path(path).read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("fixture inspector received a file that is not a PNG")
    offset = 8
    width = height = 0
    compressed = b""
    while offset < len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        payload = data[offset + 8 : offset + 8 + length]
        if kind == b"IHDR":
            width, height, depth, colour_type = struct.unpack(
                ">IIBB", payload[:10]
            )
            if depth != 8 or colour_type != 2:
                raise ValueError("fixture inspector expects 8-bit RGB swatches")
        elif kind == b"IDAT":
            compressed += payload
        offset += 12 + length
    raw = zlib.decompress(compressed)
    stride = width * 3
    rows = []
    for index in range(height):
        start = index * (stride + 1) + 1
        pixel = raw[start : start + 3]
        rows.append((pixel[0], pixel[1], pixel[2]))
    return rows


class FixtureConceptArtist:
    """Draw one swatch per request. A fixture, never a real provider.

    ``omit`` names components the exploded swatch should leave out, which is how
    a test produces an incomplete explode without hand-crafting PNG bytes.
    """

    def __init__(self, omit: Sequence[str] = ()) -> None:
        self.omit = tuple(omit)
        self.requests: List[ConceptImageRequest] = []

    def __call__(self, request: ConceptImageRequest) -> str:
        if not isinstance(request, ConceptImageRequest):
            raise TypeError("fixture concept artist requires a ConceptImageRequest")
        self.requests.append(request)
        rows: List[Tuple[int, int, int]]
        if request.role == "exploded":
            rows = [
                component_colour(component.key)
                for component in request.brief.components
                if component.key not in self.omit
            ] or [_colour("empty-explode")]
        elif request.kind == "component":
            rows = [component_colour(request.role)]
        else:
            rows = [
                _colour(
                    "%s/%d/%s"
                    % (
                        request.role,
                        request.round,
                        hashlib.sha256(
                            request.prompt.encode("utf-8")
                        ).hexdigest(),
                    )
                )
            ]
        _write_png(request.workspace / request.filename, rows)
        return request.filename

    def prompts(self) -> Dict[str, str]:
        return {request.role: request.prompt for request in self.requests}


def fixture_explode_inspector(
    image: Path, brief: ConceptBrief
) -> Tuple[str, ...]:
    """Report which components the exploded swatch actually separates."""

    observed = set(_read_png_rows(image))
    return tuple(
        component.key
        for component in brief.components
        if component_colour(component.key) in observed
    )


__all__ = [
    "FIXTURE_MARK",
    "FixtureConceptArtist",
    "component_colour",
    "fixture_explode_inspector",
]
