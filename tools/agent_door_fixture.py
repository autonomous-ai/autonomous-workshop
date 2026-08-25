"""A deterministic, in-process launcher fixture. NOT a real agent process.

This repo starts no real coding-agent process and reaches no network, so the
shipped agent door waits for a real launcher to be configured. Tests and
``tools/build_showcase_products.py`` still need the door's three Concept
roles satisfied end to end, so this module supplies a
:data:`agent_session.ProcessLauncher` that never spawns a subprocess and
never touches the network: it writes a canned, deterministic structured
result straight to the result file the door names, exactly as a well-behaved
real process would, and returns a clean exit.

It is deliberately kept out of ``src/`` so it can never be installed or wired
into a real Workshop, following the same convention as
``tools/concept_fixture.py`` and ``tools/wish_research_fixture.py``. Nothing
produced here is evidence that a Wish was researched, a design was drawn, or
an exploded view was actually inspected.
"""

from __future__ import annotations

import base64
import hashlib
import json
import struct
import zlib
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from inventor_workshop.agent_session import (
    LaunchResult,
    LauncherOverBudget,
    LauncherTimedOut,
    ResolvedRoleAccess,
)

FIXTURE_MARK = "workshop-agent-door-fixture"
ROLE_WISH_RESEARCH = "wish-research"
ROLE_CONCEPT_IMAGES = "concept-images"
ROLE_EXPLODED_VIEW_CHECK = "exploded-view-check"
_FIXTURE_REASON = (
    "the fixture agent read no source and decided this from the request it "
    "was given"
)
_SWATCH_WIDTH = 8


def _colour(seed: str) -> Tuple[int, int, int]:
    digest = hashlib.sha256((FIXTURE_MARK + "/" + seed).encode("utf-8")).digest()
    return tuple(24 + (value % 200) for value in digest[:3])  # type: ignore[return-value]


def component_colour(key: str) -> Tuple[int, int, int]:
    """The band colour identifying one component key in an exploded swatch."""

    return _colour("component/" + key)


def _encode_png(rows: Sequence[Tuple[int, int, int]]) -> bytes:
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
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


def _decode_png(data: bytes) -> List[Tuple[int, int, int]]:
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("fixture agent door received a file that is not a PNG")
    offset = 8
    width = height = 0
    compressed = b""
    while offset < len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        payload = data[offset + 8 : offset + 8 + length]
        if kind == b"IHDR":
            width, height, depth, colour_type = struct.unpack(">IIBB", payload[:10])
            if depth != 8 or colour_type != 2:
                raise ValueError("fixture agent door expects 8-bit RGB swatches")
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


def _sequence(value: Any) -> Tuple[Any, ...]:
    if isinstance(value, (str, bytes, Mapping)) or not isinstance(value, Sequence):
        return ()
    return tuple(value)


def _spread(seed: str, low: float, high: float) -> float:
    digest = hashlib.sha256((FIXTURE_MARK + "/" + seed).encode("utf-8"))
    span = int.from_bytes(digest.digest()[:4], "big") % 1000
    return round(low + (high - low) * span / 999.0, 1)


def _dimensions(value: Any) -> Optional[Tuple[float, float, float]]:
    numbers = _sequence(value)
    if len(numbers) == 3:
        try:
            return tuple(float(item) for item in numbers)  # type: ignore[return-value]
        except (TypeError, ValueError):
            pass
    return None


class FixtureAgentLauncher:
    """A deterministic launcher serving the three Concept roles offline.

    ``omit`` names exploded-view component keys the ``concept-images`` role
    should leave out of its exploded swatch, mirroring
    ``tools/concept_fixture.py``'s ``FixtureConceptArtist`` — how a test
    produces an incomplete explode without hand-crafting PNG bytes.
    """

    def __init__(self, omit: Sequence[str] = ()) -> None:
        self.omit = tuple(omit)
        self.calls: List[Tuple[str, Dict[str, Any]]] = []

    def __call__(
        self,
        role: str,
        request: Mapping[str, Any],
        access: ResolvedRoleAccess,
        workspace: Path,
        result_file: Path,
    ) -> LaunchResult:
        self.calls.append((role, dict(request)))
        if role == ROLE_WISH_RESEARCH:
            payload = self._wish_research(request)
        elif role == ROLE_CONCEPT_IMAGES:
            payload = self._concept_image(request)
        elif role == ROLE_EXPLODED_VIEW_CHECK:
            payload = self._exploded_view_check(request)
        else:
            raise ValueError("fixture agent door has no canned result for role %r" % role)
        result_file.write_text(
            json.dumps(payload, sort_keys=True, ensure_ascii=False), encoding="utf-8"
        )
        return LaunchResult(exit_status=0, stdout="", stderr="", spent_micros=1)

    # -- wish-research ------------------------------------------------------

    def _wish_research(self, request: Mapping[str, Any]) -> Dict[str, Any]:
        wish = request.get("wish") or {}
        constraints = dict(wish.get("constraints") or {})
        objective = " ".join(str(wish.get("objective", "")).split())
        described = objective.split(".")[0].strip() or objective
        lane = request.get("lane", "")

        envelope = _dimensions(constraints.get("envelope_mm")) or (
            _spread(objective, 45.0, 180.0),
            _spread(objective + "/width", 45.0, 180.0),
            _spread(objective + "/height", 20.0, 90.0),
        )
        wall = constraints.get("wall_mm")
        if type(wall) not in (int, float):
            wall = _spread(objective + "/wall", 1.6, 3.2)
        features = tuple(
            str(item) for item in _sequence(constraints.get("features")) if str(item).strip()
        ) or ("a fixture-derived reading of the wished-for object",)
        orientation = constraints.get("print_orientation")
        if not isinstance(orientation, str) or not orientation.strip():
            orientation = "flat on its largest face"
        supports = constraints.get("print_supports")
        if supports is not True and supports is not False:
            supports = False
        fits = constraints.get("fits")
        fits = dict(fits) if isinstance(fits, Mapping) else None

        components = [
            dict(item) for item in _sequence(constraints.get("components")) if isinstance(item, Mapping)
        ]
        if not components:
            components = self._parts(described, envelope)

        findings = [
            {"claim": "The wished-for object is %s." % described[:400], "field": "object", "decided_because": _FIXTURE_REASON},
            {"claim": "It belongs to the %s lane." % lane, "field": "category", "decided_because": _FIXTURE_REASON},
            {
                "claim": "Its envelope is %s mm." % " x ".join("%.1f" % value for value in envelope),
                "field": "envelope_mm",
                "decided_because": _FIXTURE_REASON,
            },
            {"claim": "Its wall thickness is %.1f mm." % float(wall), "field": "wall_mm", "decided_because": _FIXTURE_REASON},
            {"claim": "Its distinctive features are: %s." % "; ".join(features), "field": "features", "decided_because": _FIXTURE_REASON},
            {
                "claim": "It prints %s%s." % (orientation, "" if supports else ", without supports"),
                "field": "print",
                "decided_because": _FIXTURE_REASON,
            },
            {
                "claim": self._components_claim(components),
                "field": "components",
                "decided_because": _FIXTURE_REASON,
            },
        ]
        if fits is not None:
            findings.append(
                {
                    "claim": "It must hold %s." % fits.get("target", "the stated target"),
                    "field": "fits",
                    "decided_because": _FIXTURE_REASON,
                }
            )
        return {
            "object": described[:500],
            "category": lane,
            "envelope_mm": list(envelope),
            "wall_mm": float(wall),
            "features": list(features),
            "print": {"orientation": orientation, "supports": bool(supports)},
            "fits": fits,
            "components": components,
            "findings": findings,
            "sources": [],
        }

    @staticmethod
    def _components_claim(components: Sequence[Mapping[str, Any]]) -> str:
        if len(components) == 1:
            return "The design is one printed part: %s." % components[0]["name"]
        return "The design is made of %d printed parts: %s." % (
            len(components),
            ", ".join(item["name"] for item in components),
        )

    @staticmethod
    def _parts(described: str, envelope: Sequence[float]) -> List[Dict[str, Any]]:
        length, width, height = (float(value) for value in envelope)
        return [
            {
                "key": "base",
                "name": "Base",
                "purpose": "Seats the design on a surface and carries the upper part.",
                "form": "a squared plinth with a recessed underside and a rim that receives the upper part",
                "dimensions_mm": [length, width, round(height * 0.4, 1)],
                "placement": "the lowest part of the assembly, resting on the surface",
                "interfaces": "its rim receives the crown; nothing sits below it",
            },
            {
                "key": "crown",
                "name": "Crown",
                "purpose": "Carries the reading of %s that the Wish asked for." % described[:200],
                "form": "a tapering upper volume rising from the base rim, its faces stepped so the silhouette reads from every side",
                "dimensions_mm": [round(length * 0.9, 1), round(width * 0.9, 1), round(height * 0.6, 1)],
                "placement": "seated on the base rim, forming the visible top of the design",
                "interfaces": "its lower rim drops into the base rim; nothing sits above it",
            },
        ]

    # -- concept-images -------------------------------------------------------

    def _concept_image(self, request: Mapping[str, Any]) -> Dict[str, Any]:
        role = request.get("role", "")
        kind = request.get("kind", "")
        brief = request.get("brief") or {}
        components = _sequence(brief.get("components"))
        if role == "exploded":
            rows = [
                component_colour(item["key"])
                for item in components
                if isinstance(item, Mapping) and item.get("key") not in self.omit
            ] or [_colour("empty-explode")]
        elif kind == "component":
            rows = [component_colour(role)]
        else:
            rows = [
                _colour(
                    "%s/%s/%s"
                    % (
                        role,
                        request.get("round", 0),
                        hashlib.sha256(str(request.get("prompt", "")).encode("utf-8")).hexdigest(),
                    )
                )
            ]
        return {
            "image_base64": base64.b64encode(_encode_png(rows)).decode("ascii"),
            "media_type": "image/png",
        }

    # -- exploded-view-check --------------------------------------------------

    def _exploded_view_check(self, request: Mapping[str, Any]) -> Dict[str, Any]:
        image = request.get("image") or {}
        data = base64.b64decode(image.get("data_base64", ""))
        observed = set(_decode_png(data))
        offered = _sequence(request.get("components"))
        visible = [
            item["key"]
            for item in offered
            if isinstance(item, Mapping) and component_colour(item["key"]) in observed
        ]
        return {"components": visible}


class FixtureLauncherTimeout(FixtureAgentLauncher):
    """A launcher stub that always reports a wall-clock overrun."""

    def __call__(self, role, request, access, workspace, result_file):  # type: ignore[override]
        raise LauncherTimedOut()


class FixtureLauncherOverBudget(FixtureAgentLauncher):
    """A launcher stub that always reports a budget overrun."""

    def __init__(self, spent_micros: int, omit: Sequence[str] = ()) -> None:
        super().__init__(omit)
        self._spent_micros = spent_micros

    def __call__(self, role, request, access, workspace, result_file):  # type: ignore[override]
        raise LauncherOverBudget(self._spent_micros)


__all__ = [
    "FIXTURE_MARK",
    "FixtureAgentLauncher",
    "FixtureLauncherOverBudget",
    "FixtureLauncherTimeout",
    "ROLE_CONCEPT_IMAGES",
    "ROLE_EXPLODED_VIEW_CHECK",
    "ROLE_WISH_RESEARCH",
    "component_colour",
]
