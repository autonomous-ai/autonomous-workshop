"""Screw bosses, heat-set insert pockets, nut traps."""

from __future__ import annotations

import cadquery as cq

from cadlib.tables import HEATSET_TABLE, NUT_TABLE, SCREW_TABLE


def add_screw_post(
    part: cq.Workplane,
    *,
    positions: list[tuple[float, float]],
    screw_size: str = "M3",
    boss_height: float,
    boss_od: float | None = None,
    hole_type: str = "self_tap",
    countersink: str | None = None,
    cbore_depth: float = 3.0,
    open_face: str = ">Z",
) -> cq.Workplane:
    """Add cylindrical screw bosses standing up from ``open_face``, with
    holes drilled coaxially.

    Parameters
    ----------
    positions : list of (x, y)
        Boss centres in the face's local frame.
    screw_size : "M2" | "M2.5" | "M3" | "M4" | "M5"
    boss_height : mm above ``open_face``
    boss_od : outer diameter; defaults to 2 * clearance + 4 mm
        (≥ 8 mm for M3 — the field-safe minimum, see screw-boss.md)
    hole_type : "clearance" (for through-bolts) | "self_tap" (taps into plastic)
    countersink : None | "cbore" | "csink"

    >>> body = cq.Workplane("XY").box(40, 40, 5)
    >>> body = add_screw_post(
    ...     body,
    ...     positions=[(-15, -15), (15, -15), (-15, 15), (15, 15)],
    ...     screw_size="M3",
    ...     boss_height=8,
    ... )
    """
    if screw_size not in SCREW_TABLE:
        raise ValueError(f"unknown screw_size {screw_size!r}; use one of {sorted(SCREW_TABLE)}")
    s = SCREW_TABLE[screw_size]
    hole_d = s["clearance"] if hole_type == "clearance" else s["self_tap"]
    od = boss_od if boss_od is not None else 2 * s["clearance"] + 4.0
    if od <= hole_d + 1.0:
        raise ValueError(
            f"boss_od {od} leaves wall <0.5mm around {hole_d}mm hole"
        )

    # Extrude posts.
    posts = (
        part.faces(open_face).workplane()
        .pushPoints(positions)
        .circle(od / 2)
        .extrude(boss_height)
    )
    # Cut holes from the boss tops. ">Z[-2]" picks the original parent face
    # plus boss tops — the cboreHole locates on each pushed point.
    sel = ">Z" if open_face == ">Z" else open_face
    posts = (
        posts.faces(sel).workplane()
        .pushPoints(positions)
    )
    if countersink == "cbore":
        cap_d = s["cap_head_dia"] + 0.5
        posts = posts.cboreHole(hole_d, cap_d, cbore_depth, depth=boss_height + 2)
    elif countersink == "csink":
        cap_d = s["cap_head_dia"] + 0.5
        posts = posts.cskHole(hole_d, cap_d, 90, depth=boss_height + 2)
    else:
        posts = posts.hole(hole_d, depth=boss_height + 2)
    return posts


def add_heat_set_pocket(
    part: cq.Workplane,
    *,
    positions: list[tuple[float, float]],
    insert_size: str = "M3",
    bottom_clearance: float = 1.5,
    open_face: str = ">Z",
) -> cq.Workplane:
    """Cut heat-set insert pockets into ``part`` at each (x, y) in
    ``positions``. The insert is pressed in from ``open_face``.

    ``pocket_d`` is the insert's BODY diameter (knurls bite into the
    plastic). Pocket depth = insert length + ``bottom_clearance``. A shallow
    rim relief (``relief_d`` × ``relief_h`` from ``HEATSET_TABLE``) is
    counterbored at the open face so the plastic the insert displaces as it
    reflows has somewhere to go instead of mounding proud of the surface.

    >>> body = cq.Workplane("XY").box(40, 40, 12)
    >>> body = add_heat_set_pocket(body, positions=[(0, 0)], insert_size="M3")
    """
    if insert_size not in HEATSET_TABLE:
        raise ValueError(
            f"unknown insert_size {insert_size!r}; use one of {sorted(HEATSET_TABLE)}"
        )
    h = HEATSET_TABLE[insert_size]
    depth = h["insert_len"] + bottom_clearance
    # cboreHole cuts the body pocket (diameter) plus the rim relief
    # (cboreDiameter × cboreDepth) in one pass, from the open face inward.
    part = (
        part.faces(open_face).workplane()
        .pushPoints(positions)
        .cboreHole(h["pocket_d"], h["relief_d"], h["relief_h"], depth=depth)
    )
    return part


def add_nut_trap(
    part: cq.Workplane,
    *,
    positions: list[tuple[float, float]],
    nut_size: str = "M3",
    pocket_face: str = ">Z",
    screw_face: str = "<Z",
) -> cq.Workplane:
    """Cut an ISO hex nut trap + coaxial screw clearance hole.

    The hex pocket opens at ``pocket_face`` (top-drop or below-bridge); the
    screw enters from ``screw_face`` (opposite side). Pocket flats are
    sized for a +0.2 mm FDM clearance over the nominal nut flat.

    >>> body = cq.Workplane("XY").box(30, 30, 10)
    >>> body = add_nut_trap(body, positions=[(0, 0)], nut_size="M3")
    """
    if nut_size not in NUT_TABLE:
        raise ValueError(
            f"unknown nut_size {nut_size!r}; use one of {sorted(NUT_TABLE)}"
        )
    n = NUT_TABLE[nut_size]
    # Hex pocket from pocket_face
    part = (
        part.faces(pocket_face).workplane()
        .pushPoints(positions)
        .polygon(6, n["pocket_flat"], circumscribed=False)
        .cutBlind(-n["pocket_h"])
    )
    # Screw clearance hole all the way through from the opposite face
    part = (
        part.faces(screw_face).workplane()
        .pushPoints(positions)
        .hole(n["screw_clear"])
    )
    return part
