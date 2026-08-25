"""A deterministic fixture wish researcher. NOT a real researcher.

This repo talks to no model and reads no web page, so the shipped Concept job
waits truthfully for a real wish-research capability. Tests and the showcase
builder still need the pipeline to run end to end, so this module derives a
breakdown from the Wish's own words and constraints instead.

Every finding it returns is marked as a fixture decision, and it records no
sources at all, because it read nothing. It is deliberately kept out of ``src/``
so it can never be installed or wired into a real Workshop, and nothing here
should be read as evidence that a Wish was actually researched.
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from inventor_workshop.concept import WishResearchRequest
from inventor_workshop.jobs import (
    ConceptComponent,
    WishResearch,
    WishResearchFinding,
)


FIXTURE_MARK = "workshop-wish-research-fixture"
_FIXTURE_REASON = (
    "the fixture researcher read no source and decided this from the Wish's "
    "own words"
)
_LANE_CATEGORIES = {
    "classics-made-yours": "a printed edition of a known game",
    "invented-games": "a printed edition of a new game",
    "moving-machines": "a hand-operated mechanism",
    "holdable-science": "a hands-on demonstration object",
    "little-worlds": "a small scene object",
}


def _sequence(value: Any) -> Tuple[Any, ...]:
    if isinstance(value, (str, bytes, Mapping)) or not isinstance(value, Sequence):
        return ()
    return tuple(value)


def _spread(objective: str, low: float, high: float) -> float:
    """One stable number per Wish, so two Wishes do not share an envelope."""

    digest = hashlib.sha256((FIXTURE_MARK + "/" + objective).encode("utf-8"))
    span = int.from_bytes(digest.digest()[:4], "big") % 1000
    return round(low + (high - low) * span / 999.0, 1)


def _dimensions(value: Any) -> Optional[Tuple[float, float, float]]:
    numbers = _sequence(value)
    if len(numbers) != 3:
        return None
    try:
        return tuple(float(item) for item in numbers)  # type: ignore[return-value]
    except (TypeError, ValueError):
        return None


def _components(value: Any) -> Tuple[ConceptComponent, ...]:
    declared = _sequence(value)
    parts: List[ConceptComponent] = []
    for item in declared:
        if not isinstance(item, Mapping):
            continue
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
    return tuple(parts)


class FixtureWishResearcher:
    """Break a Wish down deterministically, with nothing sourced.

    Where the Wish already states a physical fact, it is carried through; where
    it does not, a stable value is derived from the objective text so two
    different Wishes never share an envelope. Every fact is recorded as a
    fixture decision, never as a citation.
    """

    def __init__(self) -> None:
        self.requests: List[WishResearchRequest] = []

    def __call__(self, request: WishResearchRequest) -> WishResearch:
        if not isinstance(request, WishResearchRequest):
            raise TypeError("fixture wish researcher requires a WishResearchRequest")
        self.requests.append(request)
        wish = request.wish
        constraints: Dict[str, Any] = dict(wish.constraints)
        objective = " ".join(wish.objective.split())
        described = objective.split(".")[0].strip() or objective

        envelope = _dimensions(constraints.get("envelope_mm")) or (
            _spread(objective, 45.0, 180.0),
            _spread(objective + "/width", 45.0, 180.0),
            _spread(objective + "/height", 20.0, 90.0),
        )
        wall = constraints.get("wall_mm")
        if type(wall) not in (int, float):
            wall = _spread(objective + "/wall", 1.6, 3.2)
        features = tuple(
            str(item)
            for item in _sequence(constraints.get("features"))
            if str(item).strip()
        ) or (
            "a %s reading of the wished-for object, worked into its %s mm "
            "silhouette rather than applied to it"
            % (request.taste.name, ("%.1f" % envelope[2]).rstrip("0").rstrip(".")),
        )
        orientation = constraints.get("print_orientation")
        if not isinstance(orientation, str) or not orientation.strip():
            orientation = "flat on its largest face"
        supports = constraints.get("print_supports")
        if supports is not True and supports is not False:
            supports = False
        fits = constraints.get("fits")
        fits = dict(fits) if isinstance(fits, Mapping) else None

        components = _components(constraints.get("components"))
        if not components:
            components = self._parts(described, envelope)

        findings = [
            WishResearchFinding(
                "The wished-for object is %s." % described[:400],
                "object",
                decided_because=_FIXTURE_REASON,
            ),
            WishResearchFinding(
                "It belongs to the %s lane." % request.blueprint.lane,
                "category",
                decided_because=_FIXTURE_REASON,
            ),
            WishResearchFinding(
                "Its envelope is %s mm."
                % " x ".join(("%.1f" % value) for value in envelope),
                "envelope_mm",
                decided_because=_FIXTURE_REASON,
            ),
            WishResearchFinding(
                "Its wall thickness is %.1f mm." % float(wall),
                "wall_mm",
                decided_because=_FIXTURE_REASON,
            ),
            WishResearchFinding(
                "Its distinctive features are: %s." % "; ".join(features),
                "features",
                decided_because=_FIXTURE_REASON,
            ),
            WishResearchFinding(
                "It prints %s%s."
                % (orientation, "" if supports else ", without supports"),
                "print",
                decided_because=_FIXTURE_REASON,
            ),
            WishResearchFinding(
                self._components_claim(components),
                "components",
                decided_because=_FIXTURE_REASON,
            ),
        ]
        if fits is not None:
            findings.append(
                WishResearchFinding(
                    "It must hold %s." % fits.get("target", "the stated target"),
                    "fits",
                    decided_because=_FIXTURE_REASON,
                )
            )
        return WishResearch(
            described[:500],
            _LANE_CATEGORIES.get(request.blueprint.lane, request.blueprint.lane),
            envelope,
            float(wall),
            features,
            {"orientation": orientation, "supports": bool(supports)},
            components,
            fits,
            tuple(findings),
            (),
        )

    @staticmethod
    def _components_claim(components: Sequence[ConceptComponent]) -> str:
        if len(components) == 1:
            return (
                "The design is one printed part: %s." % components[0].name
            )
        return "The design is made of %d printed parts: %s." % (
            len(components),
            ", ".join(item.name for item in components),
        )

    @staticmethod
    def _parts(
        described: str, envelope: Sequence[float]
    ) -> Tuple[ConceptComponent, ...]:
        """A two-part breakdown, so nothing here restates the envelope."""

        length, width, height = (float(value) for value in envelope)
        return (
            ConceptComponent(
                "base",
                "Base",
                "Seats the design on a surface and carries the upper part.",
                "a squared plinth with a recessed underside and a rim that "
                "receives the upper part",
                (length, width, round(height * 0.4, 1)),
                "the lowest part of the assembly, resting on the surface",
                "its rim receives the crown; nothing sits below it",
            ),
            ConceptComponent(
                "crown",
                "Crown",
                "Carries the reading of %s that the Wish asked for."
                % described[:200],
                "a tapering upper volume rising from the base rim, its faces "
                "stepped so the silhouette reads from every side",
                (
                    round(length * 0.9, 1),
                    round(width * 0.9, 1),
                    round(height * 0.6, 1),
                ),
                "seated on the base rim, forming the visible top of the design",
                "its lower rim drops into the base rim; nothing sits above it",
            ),
        )


__all__ = [
    "FIXTURE_MARK",
    "FixtureWishResearcher",
]
