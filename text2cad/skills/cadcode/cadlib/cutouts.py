"""Press-fit pockets, magnet pockets, bearing seats, cable channels.

All helpers cut FROM an existing ``part``. They do not produce solids on
their own — pass the body to be modified as the first arg.
"""

from __future__ import annotations

import cadquery as cq

from cadlib.tables import BEARING_TABLE, MAGNET_TABLE


def add_press_fit_pocket(
    part: cq.Workplane,
    *,
    positions: list[tuple[float, float]],
    insert_diameter: float,
    insert_depth: float,
    interference: float = 0.05,
    lead_in_chamfer: float = 0.4,
    bottom_clearance: float = 0.3,
    open_face: str = ">Z",
) -> cq.Workplane:
    """Cut press-fit pockets sized for an insert (shaft, dowel, etc.).

    ``interference`` is undersize per nominal — default 0.05 mm matches
    a stock i3-class printer with ~0.10 mm horizontal-expansion. Tighten
    only after you've measured the printer.

    The pocket is ``insert_depth + bottom_clearance`` deep so the insert
    can fully seat without bottoming on plastic dust.
    """
    pocket_d = insert_diameter - interference
    depth = insert_depth + bottom_clearance
    part = (
        part.faces(open_face).workplane()
        .pushPoints(positions)
        .hole(pocket_d, depth=depth)
    )
    if lead_in_chamfer > 0:
        # Chamfer the rim of the pocket on each pocket. Use a circle-edge
        # filter so we don't chamfer the rest of the top face.
        part = part.faces(open_face).edges("%CIRCLE").chamfer(lead_in_chamfer)
    return part


def add_magnet_pocket(
    part: cq.Workplane,
    *,
    positions: list[tuple[float, float]],
    magnet_size: str = "10x3",
    fit_type: str = "slip",
    top_wall: float = 0.4,
    open_face: str = ">Z",
) -> cq.Workplane:
    """Cut neodymium-disc-magnet pockets, recessed by ``top_wall`` from
    ``open_face`` so the magnet sits hidden beneath a thin plastic skin.

    ``fit_type``: "slip" (+0.2 mm dia, glue with CA) | "press" (-0.1 mm,
    friction-only). Print orientation must keep ``top_wall`` as a bridge
    that prints well — see references/patterns/magnet-pocket.md.
    """
    if magnet_size not in MAGNET_TABLE:
        raise ValueError(
            f"unknown magnet_size {magnet_size!r}; use one of {sorted(MAGNET_TABLE)}"
        )
    if fit_type not in ("slip", "press"):
        raise ValueError(f"fit_type must be 'slip' or 'press', got {fit_type!r}")
    m = MAGNET_TABLE[magnet_size]
    pocket_d = m["d"] + (0.2 if fit_type == "slip" else -0.1)
    # Workplane offset INTO the body by top_wall, then hole the magnet depth.
    part = (
        part.faces(open_face).workplane(offset=-top_wall)
        .pushPoints(positions)
        .hole(pocket_d, depth=m["h"] + 0.1)
    )
    return part


def add_bearing_seat(
    part: cq.Workplane,
    *,
    positions: list[tuple[float, float]],
    bearing: str = "608",
    lead_chamfer: float = 0.5,
    open_back: bool = False,
    open_face: str = ">Z",
) -> cq.Workplane:
    """Cut a bearing seat (outer race press-fit + inner race relief
    shoulder) at each (x, y).

    ``open_back=True`` cuts the shoulder all the way through (for a
    shaft passing entirely through the part). ``open_back=False`` keeps a
    closed back behind the bearing — useful for end caps.
    """
    if bearing not in BEARING_TABLE:
        raise ValueError(
            f"unknown bearing {bearing!r}; use one of {sorted(BEARING_TABLE)}"
        )
    b = BEARING_TABLE[bearing]
    # Outer pocket (press fit on outer race)
    part = (
        part.faces(open_face).workplane()
        .pushPoints(positions)
        .hole(b["pocket"], depth=b["h"] + 0.1)
    )
    # Inner relief — keeps inner race spinning free
    if open_back:
        part = (
            part.faces(open_face).workplane()
            .pushPoints(positions)
            .hole(b["shoulder_id"])  # through-hole
        )
    else:
        part = (
            part.faces(open_face).workplane(offset=-(b["h"] + 0.1))
            .pushPoints(positions)
            .hole(b["shoulder_id"], depth=b["shoulder_h"])
        )
    if lead_chamfer > 0:
        part = part.faces(open_face).edges("%CIRCLE").chamfer(lead_chamfer)
    return part


def add_cable_channel(
    part: cq.Workplane,
    *,
    centerline: list[tuple[float, float]],
    cable_diameter: float = 4.5,
    channel_depth: float | None = None,
    channel_clearance: float = 0.4,
    open_face: str = ">Z",
) -> cq.Workplane:
    """Cut a U-shaped cable channel along ``centerline`` on ``open_face``.

    Channel is open-top (no lid). Phase-1 only supports STRAIGHT
    (two-point) centerlines; multi-segment polyline + sweep is phase 2.

    For a press-retained cable, use ``channel_clearance`` near 0. For a
    slip-fit, use 0.4 mm clearance and plan a lid separately.
    """
    import math
    if len(centerline) != 2:
        raise NotImplementedError(
            "add_cable_channel currently only supports a straight 2-point "
            f"centerline, got {len(centerline)} points"
        )
    depth = channel_depth if channel_depth is not None else cable_diameter * 0.9
    width = cable_diameter + channel_clearance
    (x1, y1), (x2, y2) = centerline
    length = math.hypot(x2 - x1, y2 - y1)
    if length <= 0:
        raise ValueError("centerline endpoints coincide")
    angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    cutter = (
        cq.Workplane("XY")
        .rect(length, width)
        .extrude(depth + 1)              # +1 overcut to pierce cleanly
        .translate((cx, cy, 0))
        .rotate((cx, cy, 0), (cx, cy, 1), angle)
    )
    # Lift cutter to sit at the open_face top so it cuts downward from
    # the surface. For the default ">Z" we cut from the part's max Z.
    if open_face == ">Z":
        z_top = part.val().BoundingBox().zmax
        cutter = cutter.translate((0, 0, z_top - depth))
    elif open_face == "<Z":
        z_bot = part.val().BoundingBox().zmin
        cutter = cutter.translate((0, 0, z_bot - 1))
    return part.cut(cutter)


def _straight_slot_cutter(
    *,
    centerline: list[tuple[float, float]],
    width: float,
    depth: float,
    part: cq.Workplane,
    open_face: str,
    length_override: float | None = None,
    anchor_at_start: bool = False,
) -> cq.Workplane:
    """An open-top rectangular slot cutter along a straight 2-point centerline.

    Shared by the cable channel and the connector-clearance pocket. When
    ``anchor_at_start`` the slot of length ``length_override`` starts at the
    first centerline point and runs toward the second (used for the connector
    pocket at the cable's exit); otherwise it spans the full centerline.
    """
    import math

    if len(centerline) != 2:
        raise NotImplementedError(
            "open cable channel supports a straight 2-point centerline only, "
            f"got {len(centerline)} points"
        )
    (x1, y1), (x2, y2) = centerline
    span = math.hypot(x2 - x1, y2 - y1)
    if span <= 0:
        raise ValueError("centerline endpoints coincide")
    angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
    length = span if length_override is None else min(length_override, span)
    if anchor_at_start:
        ux, uy = (x2 - x1) / span, (y2 - y1) / span
        cx, cy = x1 + ux * length / 2, y1 + uy * length / 2
    else:
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    cutter = (
        cq.Workplane("XY")
        .rect(length, width)
        .extrude(depth + 1)  # +1 overcut to pierce cleanly
        .translate((cx, cy, 0))
        .rotate((cx, cy, 0), (cx, cy, 1), angle)
    )
    if open_face == ">Z":
        z_top = part.val().BoundingBox().zmax
        return cutter.translate((0, 0, z_top - depth))
    if open_face == "<Z":
        z_bot = part.val().BoundingBox().zmin
        return cutter.translate((0, 0, z_bot - 1))
    raise ValueError(f"open_face must be '>Z' or '<Z', got {open_face!r}")


def add_open_cable_channel(
    part: cq.Workplane,
    *,
    centerline: list[tuple[float, float]],
    cable_diameter: float = 3.6,
    connector_diameter: float = 9.0,
    connector_length: float = 14.0,
    channel_clearance: float = 0.6,
    channel_depth: float | None = None,
    open_face: str = ">Z",
) -> cq.Workplane:
    """Cut an OPEN, installable route for a CAPTIVE cable whose device end has a
    strain-relief **connector collar** wider than the jacket (e.g. an Apple
    MagSafe puck's permanently-attached cable).

    Two open-top cuts along a STRAIGHT ``centerline`` on ``open_face``:

      * a **connector-clearance pocket** — width ``connector_diameter +
        clearance``, length ``connector_length`` — starting at ``centerline[0]``
        (the device/cable-exit end), so the collar drops in; and
      * a **cable channel** — width ``cable_diameter + clearance`` — for the
        whole run.

    Open-top by design: a captive cable can only be **laid in from the side**,
    never threaded through a closed tunnel. Use this (not ``add_cable_channel``)
    whenever the cable cannot be detached from its connector.

    >>> body = add_open_cable_channel(
    ...     body, centerline=[(0, 20), (0, -20)],
    ...     cable_diameter=3.6, connector_diameter=9.0, connector_length=14.0)
    """
    if cable_diameter <= 0 or connector_diameter <= 0:
        raise ValueError("cable_diameter and connector_diameter must be > 0")
    if connector_diameter < cable_diameter:
        raise ValueError(
            f"connector_diameter {connector_diameter} < cable_diameter "
            f"{cable_diameter} — a connector collar is wider than its jacket"
        )
    if connector_length <= 0:
        raise ValueError("connector_length must be > 0")

    cable_w = cable_diameter + channel_clearance
    cable_depth = channel_depth if channel_depth is not None else cable_diameter * 0.9
    connector_w = connector_diameter + channel_clearance
    connector_depth = max(cable_depth, connector_diameter * 0.6)

    part = part.cut(
        _straight_slot_cutter(
            centerline=centerline,
            width=cable_w,
            depth=cable_depth,
            part=part,
            open_face=open_face,
        )
    )
    part = part.cut(
        _straight_slot_cutter(
            centerline=centerline,
            width=connector_w,
            depth=connector_depth,
            part=part,
            open_face=open_face,
            length_override=connector_length,
            anchor_at_start=True,
        )
    )
    return part
