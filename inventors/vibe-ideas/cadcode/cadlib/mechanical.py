"""Snap fits, dovetails, ribs."""

from __future__ import annotations

import cadquery as cq


def add_snap_fit_cantilever(
    part: cq.Workplane,
    *,
    position: tuple[float, float, float],
    length: float = 10.0,
    thickness: float = 2.0,
    width: float = 6.0,
    catch_height: float = 0.8,
    relief_width: float = 1.2,
    lead_angle_deg: float = 30.0,
    axis: str = "+Y",
) -> cq.Workplane:
    """Add a cantilever snap arm at ``position`` (local coords in the
    parent part's frame).

    The arm extends along ``axis`` (one of "+X", "-X", "+Y", "-Y"). A catch
    nub protrudes ``catch_height`` mm at the tip, with ``lead_angle_deg``
    of lead-in chamfer on the insertion side.

    See references/patterns/snap-fit-cantilever.md for the mechanics
    (deflection y = F·L³/(3·E·I), stress σ = 3·E·h·y/(2·L²)).
    """
    if catch_height >= 0.1 * length:
        raise ValueError(
            f"catch_height {catch_height} exceeds beam's max safe deflection "
            f"(~0.1 * length = {0.1 * length:.2f}); insertion will overstress the arm"
        )
    if axis not in ("+X", "-X", "+Y", "-Y"):
        raise ValueError(f"axis must be one of +X/-X/+Y/-Y, got {axis!r}")

    sign = 1 if axis[0] == "+" else -1
    along_y = axis[1] == "Y"

    # Two relief slots on either side of the arm. We cut them through the part
    # depth of the arm so the arm is a true cantilever.
    px, py, pz = position
    arm_l = length
    arm_w = width
    arm_t = thickness
    rw = relief_width

    # Build slot cutters parallel to the axis direction
    def slot_box(offset):
        if along_y:
            box_l, box_w = arm_l, rw
            cx, cy = px, py + sign * arm_l / 2
            cx += offset
        else:
            box_l, box_w = rw, arm_l
            cx, cy = px + sign * arm_l / 2, py
            cy += offset
        return (
            cq.Workplane("XY")
            .box(box_l, box_w, arm_t * 2)
            .translate((cx, cy, pz))
        )

    side_offset = (arm_w + rw) / 2
    if along_y:
        slot_a = slot_box(side_offset)
        slot_b = slot_box(-side_offset)
    else:
        slot_a = slot_box(side_offset)
        slot_b = slot_box(-side_offset)
    part = part.cut(slot_a).cut(slot_b)

    # Catch nub at the arm tip
    if along_y:
        nub_cx, nub_cy = px, py + sign * (arm_l - 0.5)
    else:
        nub_cx, nub_cy = px + sign * (arm_l - 0.5), py
    nub = (
        cq.Workplane("XY")
        .box(arm_w * 0.8, arm_w * 0.8, catch_height)
        .translate((nub_cx, nub_cy, pz + arm_t / 2 + catch_height / 2))
    )
    # Lead-in chamfer on insertion side
    try:
        nub = nub.faces(">Z").edges().chamfer(catch_height * 0.4)
    except Exception:  # noqa: BLE001 — chamfer is best-effort on small features
        pass
    return part.union(nub)


def add_dovetail_slot(
    part: cq.Workplane,
    *,
    position: tuple[float, float, float],
    length: float,
    base_width: float = 10.0,
    angle_deg: float = 10.0,
    depth: float = 4.0,
    clearance: float = 0.4,
    axis: str = "+X",
) -> cq.Workplane:
    """Cut a female trapezoidal dovetail slot along ``axis``. A male
    dovetail of the same nominal base + height + angle, built separately,
    slides into it. ``clearance`` is added to the slot on each face.

    See references/patterns/dovetail-slide.md for matching male geometry.
    """
    import math
    if axis not in ("+X", "-X", "+Y", "-Y"):
        raise ValueError(f"axis must be one of +X/-X/+Y/-Y, got {axis!r}")
    if angle_deg <= 0 or angle_deg >= 30:
        raise ValueError(f"angle_deg must be in (0, 30), got {angle_deg}")

    base = base_width + 2 * clearance
    top = base + 2 * depth * math.tan(math.radians(angle_deg))
    # Trapezoidal profile in the cross-section plane (Z+ is wider, Z- is base).
    pts = [
        (-base / 2, 0),
        (base / 2, 0),
        (top / 2, depth),
        (-top / 2, depth),
    ]
    profile_plane = "YZ" if axis[1] == "X" else "XZ"
    cutter = (
        cq.Workplane(profile_plane)
        .polyline(pts)
        .close()
        .extrude(length)
    )
    # Place + orient
    cutter = cutter.translate(position)
    return part.cut(cutter)


def add_rib_stiffener(
    part: cq.Workplane,
    *,
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    height: float,
    thickness: float = 1.2,
    root_fillet: float = 0.5,
) -> cq.Workplane:
    """Add a vertical rib of ``thickness`` × ``height`` running from
    ``start`` to ``end`` (both XY+Z anchor points at the rib base).

    The rib stands UP from its base line by ``height``. Apply
    ``root_fillet`` mm fillet at the rib-to-parent junction to prevent
    crack initiation under cyclic load.
    """
    import math
    sx, sy, sz = start
    ex, ey, ez = end
    if (sx, sy) == (ex, ey):
        raise ValueError("rib start and end coincide in XY")
    if abs(sz - ez) > 1e-6:
        raise ValueError("rib base must lie on a single Z plane")
    length = math.hypot(ex - sx, ey - sy)
    angle = math.degrees(math.atan2(ey - sy, ex - sx))
    rib = (
        cq.Workplane("XY")
        .box(length, thickness, height, centered=(True, True, False))
        .translate(((sx + ex) / 2, (sy + ey) / 2, sz))
        .rotate(((sx + ex) / 2, (sy + ey) / 2, sz),
                ((sx + ex) / 2, (sy + ey) / 2, sz + 1), angle)
    )
    part = part.union(rib)
    if root_fillet > 0:
        try:
            part = part.faces("<Z").edges().fillet(root_fillet)
        except Exception:  # noqa: BLE001
            pass
    return part
