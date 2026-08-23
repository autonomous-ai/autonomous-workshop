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
    """Add an inward lip on the open face of an enclosure base. A matching
    lid (with the same XY outer + ``2*lip_clearance`` deducted from its
    inner) drops in and is held by friction.

    Pairs with ``lid_plate(...)`` for the matching lid.

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
) -> cq.Workplane:
    """Matching lid for an enclosure made with ``hollow_box`` + ``add_lid_lip``.

    Returns a lid with a downward-facing tongue that slips into the base's
    lip. Outer footprint matches the enclosure; tongue is undersized by
    ``2*lip_clearance``.
    """
    inner_l = length - 2 * wall - 2 * lip_clearance
    inner_w = width - 2 * wall - 2 * lip_clearance
    if inner_l <= 0 or inner_w <= 0:
        raise ValueError(f"lid_plate inner dim non-positive: {inner_l}x{inner_w}")

    lid = cq.Workplane("XY").box(length, width, thickness)
    if corner_radius > 0:
        lid = lid.edges("|Z").fillet(corner_radius)
    tongue = (
        cq.Workplane("XY")
        .box(inner_l, inner_w, lip_height)
        .translate((0, 0, -(thickness + lip_height) / 2))
    )
    return lid.union(tongue)
