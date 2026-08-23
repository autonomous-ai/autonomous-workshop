"""Hollow boxes, lid lips, and other enclosure shells."""

from __future__ import annotations

import cadquery as cq


def hollow_box(
    *,
    length: float,
    width: float,
    height: float,
    wall: float = 2.0,
    corner_radius: float = 0.0,
    open_face: str = ">Z",
) -> cq.Workplane:
    """Rectangular enclosure shell — solid box, shelled inward, optionally
    rounded vertical corners.

    All dimensions are EXTERNAL. ``wall`` is uniform. ``open_face`` is the
    face that gets shelled out (top by default, so the cavity opens upward).

    >>> body = hollow_box(length=80, width=60, height=30, wall=2.0, corner_radius=4)
    """
    if wall <= 0:
        raise ValueError(f"wall must be > 0, got {wall}")
    if wall * 2 >= min(length, width, height):
        raise ValueError(
            f"wall {wall} is too thick — leaves no cavity in {length}x{width}x{height}"
        )
    if corner_radius >= min(length, width) / 2:
        raise ValueError(
            f"corner_radius {corner_radius} exceeds half the smallest dimension"
        )

    body = cq.Workplane("XY").box(length, width, height)
    if corner_radius > 0:
        body = body.edges("|Z").fillet(corner_radius)
    return body.faces(open_face).shell(-wall)


def add_lid_lip(
    part: cq.Workplane,
    *,
    length: float,
    width: float,
    wall: float,
    lip_height: float = 3.0,
    lip_clearance: float = 0.3,
    open_face: str = ">Z",
) -> cq.Workplane:
    """Add a raised, base-owned rim on an enclosure's open face.

    This grows the selected side of ``part`` by ``lip_height``. Use it only
    when the design explicitly assigns a raised locating rim to the base. A
    plain :func:`hollow_box` cavity is already the female mate for a lid-owned
    skirt; use :func:`lid_with_skirt` for that common case instead. If the base
    has an exact final envelope, budget this external rim inside that envelope
    or omit it.

    ``lip_clearance`` is per-side; typical FDM value 0.25–0.4 mm.
    """
    if lip_height <= 0:
        raise ValueError(f"lip_height must be > 0, got {lip_height}")
    if lip_clearance < 0:
        raise ValueError(f"lip_clearance must be >= 0, got {lip_clearance}")

    inner_l = length - 2 * wall
    inner_w = width - 2 * wall
    lip_l = inner_l - 2 * lip_clearance
    lip_w = inner_w - 2 * lip_clearance
    if lip_l <= 0 or lip_w <= 0:
        raise ValueError(
            f"lip clearance {lip_clearance} too large for inner {inner_l}x{inner_w}"
        )

    lip = (
        part.faces(open_face).workplane()
        .rect(lip_l, lip_w)
        .extrude(lip_height)
    )
    # Hollow out the lip so it's just a rim, not a solid plug.
    lip_t = (inner_l - lip_l) / 2 + wall  # outer wall + inner shoulder
    hollow_l = lip_l - 2 * wall
    hollow_w = lip_w - 2 * wall
    if hollow_l > 0 and hollow_w > 0:
        lip = (
            lip.faces(open_face).workplane()
            .rect(hollow_l, hollow_w)
            .cutBlind(-lip_height)
        )
    return lip


def lid_plate(
    *,
    length: float,
    width: float,
    thickness: float = 3.0,
    corner_radius: float = 0.0,
    lip_clearance: float = 0.3,
    wall: float = 2.0,
    lip_height: float = 2.5,
    lip_wall: float | None = None,
) -> cq.Workplane:
    """Build a lid plate with the legacy solid locating tongue.

    Existing projects rely on the solid-tongue geometry when ``lip_wall`` is
    omitted, so that behavior remains stable for EDIT/REMIX rebuilds. New
    enclosure designs should call :func:`lid_with_skirt`, or explicitly pass
    ``lip_wall``, to get a material-efficient annular locating skirt.
    """
    if length <= 0 or width <= 0 or thickness <= 0:
        raise ValueError("lid_plate length, width, and thickness must be > 0")
    if wall <= 0:
        raise ValueError(f"wall must be > 0, got {wall}")
    if lip_height <= 0:
        raise ValueError(f"lip_height must be > 0, got {lip_height}")
    if lip_clearance < 0:
        raise ValueError(f"lip_clearance must be >= 0, got {lip_clearance}")
    if corner_radius < 0 or corner_radius >= min(length, width) / 2:
        raise ValueError(
            f"corner_radius {corner_radius} must be >= 0 and below half "
            "the smallest footprint dimension"
        )

    inner_l = length - 2 * wall - 2 * lip_clearance
    inner_w = width - 2 * wall - 2 * lip_clearance
    if inner_l <= 0 or inner_w <= 0:
        raise ValueError(f"lid_plate inner dim non-positive: {inner_l}x{inner_w}")

    lid = cq.Workplane("XY").box(length, width, thickness)
    if corner_radius > 0:
        lid = lid.edges("|Z").fillet(corner_radius)
    if lip_wall is None:
        tongue = (
            cq.Workplane("XY")
            .box(inner_l, inner_w, lip_height)
            .translate((0, 0, -(thickness + lip_height) / 2))
        )
        return lid.union(tongue)

    if lip_wall <= 0:
        raise ValueError(f"lip_wall must be > 0, got {lip_wall}")
    void_l = inner_l - 2 * lip_wall
    void_w = inner_w - 2 * lip_wall
    if void_l <= 0 or void_w <= 0:
        raise ValueError(
            f"lip_wall {lip_wall} leaves no center void inside "
            f"{inner_l}x{inner_w} skirt"
        )

    # Overlap only inside the plate material. The exposed skirt depth below
    # the plate remains exactly ``lip_height`` after the robust fused union.
    join_overlap = min(0.2, thickness * 0.25, lip_wall * 0.25, lip_height * 0.25)
    skirt_total_height = lip_height + join_overlap
    plate_underside = -thickness / 2
    skirt_center_z = plate_underside - lip_height / 2 + join_overlap / 2

    skirt = cq.Workplane("XY").box(inner_l, inner_w, skirt_total_height)
    outer_radius = max(0.0, corner_radius - wall - lip_clearance)
    if outer_radius >= min(inner_l, inner_w) / 2:
        raise ValueError("lid skirt outer corner radius exceeds its footprint")
    if outer_radius > 0:
        skirt = skirt.edges("|Z").fillet(outer_radius)
    skirt = skirt.translate((0, 0, skirt_center_z))

    void = cq.Workplane("XY").box(void_l, void_w, skirt_total_height + 2.0)
    inner_radius = max(0.0, outer_radius - lip_wall)
    if inner_radius >= min(void_l, void_w) / 2:
        raise ValueError("lid skirt inner corner radius exceeds its center void")
    if inner_radius > 0:
        void = void.edges("|Z").fillet(inner_radius)
    void = void.translate((0, 0, skirt_center_z))

    result = lid.union(skirt.cut(void))
    if result.solids().size() != 1:
        raise ValueError("lid skirt did not fuse into one connected lid solid")
    return result


def lid_with_skirt(
    *,
    length: float,
    width: float,
    thickness: float = 3.0,
    corner_radius: float = 0.0,
    lip_clearance: float = 0.3,
    wall: float = 2.0,
    lip_height: float = 2.5,
    lip_wall: float | None = None,
) -> cq.Workplane:
    """Build a plate with a downward annular locating skirt.

    The skirt fits a plain :func:`hollow_box` cavity: its outer footprint is
    the cavity minus ``lip_clearance`` on each side, its center stays open, and
    ``lip_height`` is the exact exposed depth below the plate. ``lip_wall``
    defaults to the enclosure wall. This explicit helper is preferred for new
    designs; :func:`lid_plate` retains its old solid tongue by default so
    existing CREATE projects rebuild without silent geometry drift.
    """
    return lid_plate(
        length=length,
        width=width,
        thickness=thickness,
        corner_radius=corner_radius,
        lip_clearance=lip_clearance,
        wall=wall,
        lip_height=lip_height,
        lip_wall=wall if lip_wall is None else lip_wall,
    )
