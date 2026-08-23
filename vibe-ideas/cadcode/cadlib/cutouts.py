"""Press-fit pockets, magnet pockets, bearing seats, wall cutouts, cable channels.

All helpers cut FROM an existing ``part``. They do not produce solids on
their own — pass the body to be modified as the first arg.
"""

from __future__ import annotations

import math

import cadquery as cq

from cadlib.tables import BEARING_TABLE, MAGNET_TABLE


_SIDE_FRAME = {
    "+X": (0, 1, 1.0, "YZ", "|X"),
    "-X": (0, 1, -1.0, "YZ", "|X"),
    "+Y": (1, 0, 1.0, "XZ", "|Y"),
    "-Y": (1, 0, -1.0, "XZ", "|Y"),
}


def _number(name: str, value: float) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        result = math.nan
    if isinstance(value, bool) or not math.isfinite(result):
        raise ValueError(f"{name} must be a finite number, got {value!r}")
    return result


def _wall_frame(part, side, center, width, height, wall, margin, tolerance):
    """Return normalized values plus normal/cross axes after cheap checks."""
    if side not in _SIDE_FRAME:
        raise ValueError(f"side must be one of {sorted(_SIDE_FRAME)}, got {side!r}")
    if not isinstance(center, (tuple, list)) or len(center) != 3:
        raise ValueError("center must be an explicit world-space (x, y, z) triple")
    center = tuple(_number(f"center[{i}]", value) for i, value in enumerate(center))
    width, height, wall, margin, tolerance = (
        _number("width", width),
        _number("height", height),
        _number("wall_thickness", wall),
        _number("sample_margin", margin),
        _number("tolerance", tolerance),
    )
    if min(width, height, wall) <= 0:
        raise ValueError("width, height, and wall_thickness must be > 0")
    if tolerance <= 0 or margin <= tolerance or wall <= 10 * tolerance:
        raise ValueError("tolerance, sample_margin, and wall sampling depth are invalid")
    solids = part.solids().vals()
    if len(solids) != 1:
        raise ValueError(
            "part must contain exactly one solid for an unambiguous wall proof"
        )

    axis, cross, sign, _, _ = _SIDE_FRAME[side]
    bbox = solids[0].BoundingBox()
    lows = (bbox.xmin, bbox.ymin, bbox.zmin)
    highs = (bbox.xmax, bbox.ymax, bbox.zmax)
    outer = highs[axis] if sign > 0 else lows[axis]
    if abs(center[axis] - outer) > max(10 * tolerance, 1e-6):
        raise ValueError(
            f"center must lie on the selected {side} exterior face; expected {outer}"
        )
    if wall >= highs[axis] - lows[axis]:
        raise ValueError("wall_thickness must be smaller than the part normal extent")
    for value, size, index, label in (
        (center[cross], width, cross, "width"),
        (center[2], height, 2, "height"),
    ):
        if value - size / 2 - margin <= lows[index] + tolerance or (
            value + size / 2 + margin >= highs[index] - tolerance
        ):
            raise ValueError(
                f"opening {label} plus adjacent-wall probes must fit on the face"
            )
    return center, width, height, wall, margin, tolerance, axis, cross, sign


def verify_side_wall_through_cut(
    part: cq.Workplane,
    *,
    side: str,
    center: tuple[float, float, float],
    width: float,
    height: float,
    wall_thickness: float,
    sample_margin: float = 0.2,
    tolerance: float = 1e-6,
) -> dict[str, int | float | str]:
    """Prove an enclosed side-wall aperture on the final post-boolean solid.

    At three wall depths, five requested-aperture samples must be air and four
    samples immediately outside the requested straight-edge extents must remain
    material. These 27 final-solid probes catch a one-sided cutter, wrong size
    or center, an oversized opening, and a later union that refills the hole.
    """
    center, width, height, wall, margin, tolerance, axis, cross, sign = _wall_frame(
        part, side, center, width, height, wall_thickness, sample_margin, tolerance
    )
    normal_inset = min(wall * 0.1, margin)
    edge_inset = min(
        margin,
        max(10 * tolerance, min(width, height, wall) * 1e-3),
        width / 4,
        height / 4,
    )

    def point(normal_depth, cross_offset=0.0, z_offset=0.0):
        result = list(center)
        result[axis] -= sign * normal_depth
        result[cross] += cross_offset
        result[2] += z_offset
        return tuple(result)

    solid = part.solids().val()

    def contains(probe):
        return solid.isInside(cq.Vector(*probe), tolerance)

    depths = (normal_inset, wall / 2, wall - normal_inset)
    aperture_offsets = [
        (0.0, 0.0),
        (-(width / 2 - edge_inset), 0.0),
        (width / 2 - edge_inset, 0.0),
        (0.0, -(height / 2 - edge_inset)),
        (0.0, height / 2 - edge_inset),
    ]
    aperture_points = [
        point(depth, cross_offset=cross_offset, z_offset=z_offset)
        for depth in depths
        for cross_offset, z_offset in aperture_offsets
    ]
    blocked = [probe for probe in aperture_points if contains(probe)]
    if blocked:
        raise ValueError(
            "side-wall aperture is not through or does not cover the requested "
            f"width/height: material remains at {blocked}"
        )

    adjacent_offsets = [
        (-(width / 2 + edge_inset), 0.0),
        (width / 2 + edge_inset, 0.0),
        (0.0, -(height / 2 + edge_inset)),
        (0.0, height / 2 + edge_inset),
    ]
    adjacent_points = [
        point(depth, cross_offset=cross_offset, z_offset=z_offset)
        for depth in depths
        for cross_offset, z_offset in adjacent_offsets
    ]
    missing = [probe for probe in adjacent_points if not contains(probe)]
    if missing:
        raise ValueError(
            "side-wall aperture lacks surrounding wall material at "
            f"{missing}"
        )
    return {
        "side": side,
        "aperture_air_samples": len(aperture_points),
        "adjacent_wall_samples": len(adjacent_points),
        "wall_thickness": wall,
    }


def add_rounded_side_wall_cutout(
    part: cq.Workplane,
    *,
    side: str,
    center: tuple[float, float, float],
    width: float,
    height: float,
    wall_thickness: float,
    corner_radius: float = 1.0,
    overshoot: float = 0.5,
    sample_margin: float = 0.2,
    tolerance: float = 1e-6,
) -> cq.Workplane:
    """Cut and prove a rounded aperture through an enclosed +/-X or +/-Y wall.

    ``center`` is the world-space point on the selected exterior face; ``width``
    runs horizontally along that face and ``height`` runs along Z. The cutter
    starts in interior air and ends in exterior air. Call
    :func:`verify_side_wall_through_cut` again after any later boolean.
    """
    center, width, height, wall, margin, tolerance, axis, _, _ = _wall_frame(
        part, side, center, width, height, wall_thickness, sample_margin, tolerance
    )
    radius = _number("corner_radius", corner_radius)
    overcut = _number("overshoot", overshoot)
    if radius < 0 or radius >= min(width, height) / 2:
        raise ValueError("corner_radius must be >= 0 and smaller than half the short side")
    if overcut <= tolerance:
        raise ValueError("overshoot must exceed tolerance on both wall faces")

    _, _, _, plane, normal_edges = _SIDE_FRAME[side]
    start = {
        "+X": center[0] - wall - overcut,
        "-X": center[0] - overcut,
        "+Y": center[1] + overcut,  # XZ positive normal points toward -Y
        "-Y": center[1] + wall + overcut,
    }[side]
    origin = list(center)
    origin[axis] = start
    cutter = (
        cq.Workplane(plane, origin=tuple(origin))
        .rect(width, height)
        .extrude(wall + 2 * overcut)
    )
    if radius:
        cutter = cutter.edges(normal_edges).fillet(radius)
    result = part.cut(cutter)
    verify_side_wall_through_cut(
        result,
        side=side,
        center=center,
        width=width,
        height=height,
        wall_thickness=wall,
        sample_margin=margin,
        tolerance=tolerance,
    )
    return result


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
