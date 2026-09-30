"""den_plug -- the star, and the one component allowed to break the floor.

A 36.00 mm flange standing 1.00 mm proud of the field on a spigot buried in the
den pocket, with two tall prominences bursting from the corners that face the
board border.  The top face is flat: a winning piece seats on the star exactly
as it seats on any land cell, one step higher.

Print stance: spigot on the bed, flange and flames upward.  The flange's
underside is drafted off the spigot at 48 degrees from horizontal so the step
needs no support, and each flame's base stands wholly on the flange, so none of
it has to be cut back or propped up.
"""

from __future__ import annotations

import math

from build123d import Plane, Pos, Rectangle, extrude, loft

import params as P
from features import hex_grain_tool, tapered_flame


def _flange_body():
    """Spigot, drafted skirt, flange: one revolved-free prismatic stack."""
    spigot = extrude(Rectangle(P.DEN_SPIGOT, P.DEN_SPIGOT), P.DEN_SPIGOT_DEPTH)
    skirt = loft(
        [
            Plane(origin=(0, 0, P.DEN_SPIGOT_DEPTH))
            * Rectangle(P.DEN_SPIGOT, P.DEN_SPIGOT),
            Plane(origin=(0, 0, P.DEN_SPIGOT_DEPTH + P.DEN_CHAMFER_RISE))
            * Rectangle(P.DEN_FLANGE, P.DEN_FLANGE),
        ],
        ruled=True,
    )
    body = spigot + skirt
    lip = P.DEN_PROUD - P.DEN_CHAMFER_RISE
    if lip > 0.01:
        body = body + Pos(0, 0, P.DEN_SPIGOT_DEPTH + P.DEN_CHAMFER_RISE) * extrude(
            Rectangle(P.DEN_FLANGE, P.DEN_FLANGE), lip
        )
    return body


def den_bodies():
    """role -> solid for one star, in print orientation.

    Local frame: the cell centre is the origin, -Y points at the board border,
    so both flames stand at the two border-facing corners; the field datum is
    Z = DEN_SPIGOT_DEPTH and the flange's flat top is one millimetre above it.
    """
    body = _flange_body()
    field_z = P.DEN_SPIGOT_DEPTH
    top_z = field_z + P.DEN_PROUD

    grains = hex_grain_tool(
        frame=P.DEN_FLANGE,
        clear=P.DISC_NOMINAL_D + 0.8,
        pitch=P.DEN_GRAIN_PITCH,
        depth=P.DEN_GRAIN_DEPTH,
        z0=top_z,
    )
    if grains is not None:
        body = body - grains

    reach = P.FLARE_DIAGONAL / math.sqrt(2.0)
    flames = []
    for sign in (-1.0, 1.0):
        flame = tapered_flame(
            base_radius=P.FLARE_BASE_D / 2.0,
            tip_radius=P.FLARE_TIP_R,
            height=field_z + P.FLARE_HEIGHT - top_z,
            lean_deg=P.FLARE_LEAN_DEG,
            heading_deg=math.degrees(math.atan2(-1.0, sign)),
        )
        flames.append(Pos(sign * reach, -reach, top_z) * flame)
    kept = flames[0] + flames[1:]
    kept.label = "den_prominence"
    body.label = "den_plug"
    return {"star": body, "flare": kept}


def build_den_plug():
    """The whole printed part, fused: what the print gates measure."""
    bodies = den_bodies()
    body = bodies["star"] + bodies["flare"]
    body.label = "den_plug"
    return body
