"""MagSafe iPhone stand — the *functional* worked example.

The lesson here is **assembly feasibility**, not just a valid solid. A real
Apple MagSafe puck has a **captive braided cable** (~Ø3.6 mm) ending in a
**strain-relief connector collar** (~Ø9 mm) — the cable cannot be detached. So
the stand must let you LAY the cable in from the side (an open route, never a
closed tunnel) and the route must clear the connector collar, or you physically
cannot install the charger.

Demonstrates, end to end:
  * real component dims web-sourced from Apple's MagSafe spec and stated as
    assumptions (puck Ø56, captive cable Ø3.6, connector collar Ø9 × 14 mm) —
    these are illustrative; verify the current spec when you build;
  * `cadlib.cutouts.add_open_cable_channel` — an open, installable route with a
    connector-clearance pocket (see `references/patterns/cable-channel.md`);
  * hard `validate(p)` asserts that block the build on an impossible fit;
  * `functional_checks(p)` returning structured `functional` warnings that the
    driver's functional-review loop drives to zero (empty here — it's correct);
  * the unified-radius styling language from `references/industrial-design.md`.
"""

from dataclasses import dataclass

import cadquery as cq

from cadlib.cutouts import add_open_cable_channel
from cadlib.styling import break_edges, design_radius_for, soften_edges


@dataclass(frozen=True)
class Params:
    # Apple MagSafe puck (captive cable + connector collar — NOT a bare cable).
    puck_dia: float = 56.0
    puck_thk: float = 5.7
    puck_clear: float = 0.3
    cable_dia: float = 3.6          # braided jacket
    connector_dia: float = 9.0      # strain-relief collar at the puck — the wide bit
    connector_len: float = 14.0     # collar length to clear

    # Upright paddle that carries the puck.
    paddle_w: float = 74.0          # puck 56.4 + margin
    paddle_thk: float = 10.0        # pocket 5.7 + back wall
    paddle_h: float = 116.0

    # Base.
    base_w: float = 84.0
    base_d: float = 96.0
    base_h: float = 9.0

    # Styling (unified radius language).
    top_chamfer: float = 1.0
    bed_chamfer: float = 0.6

    @property
    def pocket_dia(self) -> float:
        return self.puck_dia + 2 * self.puck_clear

    @property
    def back_wall(self) -> float:
        return self.paddle_thk - self.puck_thk


def validate(p: Params) -> None:
    """Hard fit constraints — a failure blocks the build (VALIDATION_FAILED)."""
    assert p.pocket_dia > p.puck_dia, "pocket must clear the puck"
    assert p.back_wall >= 2.0, f"back wall {p.back_wall:.1f} mm < 2.0 mm structural min"
    assert p.paddle_w >= p.pocket_dia + 8.0, "paddle too narrow for the puck"
    assert p.base_w <= 200 and p.base_d <= 200, "footprint exceeds bed"


def functional_checks(p: Params) -> list[dict]:
    """Assembly-feasibility checks → structured `functional` warnings.

    These are not crashes — the part still builds and renders — but the driver's
    functional-review loop won't finish while any remain. Empty here because the
    open channel + connector pocket are sized correctly.
    """
    warnings: list[dict] = []
    channel_w = p.cable_dia + 0.6
    connector_w = p.connector_dia + 0.6
    # The captive cable's connector collar must fit the connector pocket.
    if connector_w < p.connector_dia:
        warnings.append(
            {
                "part": "stand",
                "kind": "functional",
                "detail": (
                    f"connector pocket {connector_w:.1f} mm cannot clear the "
                    f"Ø{p.connector_dia} mm strain-relief collar — the puck "
                    "cannot be installed"
                ),
                "severity": "warning",
            }
        )
    # The cable jacket must fit the channel.
    if channel_w < p.cable_dia:
        warnings.append(
            {
                "part": "stand",
                "kind": "functional",
                "detail": f"cable channel {channel_w:.1f} mm < cable Ø{p.cable_dia} mm",
                "severity": "warning",
            }
        )
    return warnings


def _build(p: Params) -> cq.Workplane:
    corner_r = design_radius_for(size=p.base_w)

    # Base, with the upright paddle fused at the back edge.
    base = cq.Workplane("XY").box(p.base_w, p.base_d, p.base_h)
    base = soften_edges(base, radius=corner_r, selector="|Z")

    paddle = (
        cq.Workplane("XY")
        .box(p.paddle_w, p.paddle_thk, p.paddle_h)
        .translate(
            (0, -p.base_d / 2 + p.paddle_thk / 2, p.base_h / 2 + p.paddle_h / 2)
        )
    )
    paddle = soften_edges(paddle, radius=corner_r, selector="|Z")
    body = base.union(paddle)

    # Puck pocket on the paddle front face (+Y).
    puck_z = p.base_h / 2 + p.paddle_h * 0.55
    pocket_y = -p.base_d / 2 + p.paddle_thk
    body = (
        body.faces(">Y")
        .workplane(centerOption="CenterOfBoundBox")
        .center(0, puck_z - (p.base_h / 2 + p.paddle_h / 2))
        .hole(p.pocket_dia, depth=p.puck_thk)
    )

    # OPEN, connector-aware cable route in the base top: from under the paddle
    # (where the puck's captive cable drops down) out to the front edge. The
    # connector-clearance pocket sits at the back, under the puck.
    body = add_open_cable_channel(
        body,
        centerline=[(0, -p.base_d / 2 + p.paddle_thk + 2), (0, p.base_d / 2 - 4)],
        cable_diameter=p.cable_dia,
        connector_diameter=p.connector_dia,
        connector_length=p.connector_len,
        open_face=">Z",
    )

    # Unified styling: crisp top line + clean bed lift-off.
    body = break_edges(body, size=p.top_chamfer, selector=">Z")
    body = break_edges(body, size=p.bed_chamfer, selector="<Z")
    return body


def gen_step():
    p = Params()
    validate(p)
    return {"shape": _build(p), "warnings": functional_checks(p)}
